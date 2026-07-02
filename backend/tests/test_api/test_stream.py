import asyncio
import json
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.routers import analysis as analysis_module


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _chain_start(name):
    return {"event": "on_chain_start", "name": name, "data": {}}


def _chain_end(name, output):
    return {"event": "on_chain_end", "name": name, "data": {"output": output}}


def make_fake_graph(events, delay=0.0):
    """A stand-in for compiled_graph whose astream_events yields a script."""

    class FakeGraph:
        def astream_events(self, *args, **kwargs):
            async def gen():
                for event in events:
                    if delay:
                        await asyncio.sleep(delay)
                    yield event

            return gen()

    return FakeGraph()


async def collect_sse(resp):
    """Parse an SSE response body into (event, data) tuples and comments."""
    events, comments = [], []
    event_name, data_lines = None, []
    async for line in resp.aiter_lines():
        if line.startswith(":"):
            comments.append(line)
        elif line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].strip())
        elif line == "" and event_name:
            events.append((event_name, json.loads("\n".join(data_lines))))
            event_name, data_lines = None, []
    return events, comments


HAPPY_EVENTS = [
    _chain_start("market"),
    _chain_start("historical"),
    _chain_start("sentiment"),
    _chain_end("market", {"market_data": {"latest_price": 100}}),
    _chain_end(
        "historical",
        {
            "historical_data": {
                "pct_change": 5.0,
                "price_history": [{"date": "2024-01-01", "price": 1.0}],
            }
        },
    ),
    _chain_end("sentiment", {"sentiment_data": {"sentiment": "bullish"}}),
    _chain_start("analytics"),
    _chain_end("analytics", {"analytics_data": {"composite_score": 0.5}}),
    _chain_start("strategy"),
    _chain_end("strategy", {"strategy_data": {"action": "HOLD"}}),
    _chain_start("report"),
    _chain_end("report", {"report": "## Report"}),
]


class TestStreamEndpoint:
    @pytest.mark.anyio
    async def test_happy_path_streams_all_nodes(self, client):
        start = await client.post("/api/analysis", json={"days": 30})
        thread_id = start.json()["thread_id"]

        with patch.object(
            analysis_module, "compiled_graph", make_fake_graph(HAPPY_EVENTS)
        ):
            async with client.stream(
                "GET", f"/api/analysis/{thread_id}/stream"
            ) as resp:
                assert resp.status_code == 200
                assert "text/event-stream" in resp.headers["content-type"]
                events, _ = await collect_sse(resp)

        starts = [d["node"] for n, d in events if n == "node_start"]
        completes = [d["node"] for n, d in events if n == "node_complete"]
        assert set(starts) == {
            "market", "historical", "sentiment", "analytics", "strategy", "report"
        }
        assert set(completes) == set(starts)

        # node_complete carries a running completed-count, not a position
        counts = [d["completed"] for n, d in events if n == "node_complete"]
        assert counts == [1, 2, 3, 4, 5, 6]

        # historical node_complete must NOT include price_history...
        hist = next(
            d for n, d in events
            if n == "node_complete" and d["node"] == "historical"
        )
        assert "price_history" not in hist["result"]

        # ...but the final complete event must
        complete = next(d for n, d in events if n == "complete")
        assert complete["all_data"]["historical_data"]["price_history"]
        assert complete["report"] == "## Report"
        assert complete["errors"] == []

        # job reflects completion for the polling fallback
        status = await client.get(f"/api/analysis/{thread_id}")
        assert status.json()["status"] == "completed"

    @pytest.mark.anyio
    async def test_fatal_error_emits_error_event(self, client):
        start = await client.post("/api/analysis", json={"days": 30})
        thread_id = start.json()["thread_id"]

        fatal_events = [
            _chain_start("market"),
            _chain_end(
                "market",
                {
                    "market_data": {"error": "coin not found"},
                    "errors": ["market: coin not found"],
                },
            ),
            _chain_start("historical"),
            _chain_end(
                "historical",
                {"historical_data": {"pct_change": 1.0, "price_history": []}},
            ),
            _chain_start("sentiment"),
            _chain_end("sentiment", {"sentiment_data": {"sentiment": "neutral"}}),
            _chain_start("analytics"),
            _chain_end(
                "analytics",
                {
                    "analytics_data": {"error": "missing fields"},
                    "errors": ["analytics: missing fields"],
                },
            ),
        ]

        with patch.object(
            analysis_module, "compiled_graph", make_fake_graph(fatal_events)
        ):
            async with client.stream(
                "GET", f"/api/analysis/{thread_id}/stream"
            ) as resp:
                events, _ = await collect_sse(resp)

        names = [n for n, _ in events]
        assert "complete" not in names
        assert names[-1] == "error"
        error = events[-1][1]
        assert "market: coin not found" in error["error"]

        # strategy/report never streamed
        assert not any(
            d.get("node") in {"strategy", "report"} for _, d in events
        )

        status = await client.get(f"/api/analysis/{thread_id}")
        assert status.json()["status"] == "error"

    @pytest.mark.anyio
    async def test_unknown_thread_returns_404(self, client):
        resp = await client.get("/api/analysis/unknown/stream")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_generator_exception_emits_error_event(self, client):
        start = await client.post("/api/analysis", json={"days": 30})
        thread_id = start.json()["thread_id"]

        class ExplodingGraph:
            def astream_events(self, *args, **kwargs):
                async def gen():
                    yield _chain_start("market")
                    raise RuntimeError("boom")

                return gen()

        with patch.object(
            analysis_module, "compiled_graph", ExplodingGraph()
        ):
            async with client.stream(
                "GET", f"/api/analysis/{thread_id}/stream"
            ) as resp:
                events, _ = await collect_sse(resp)

        assert events[-1][0] == "error"
        assert "boom" in events[-1][1]["error"]

        status = await client.get(f"/api/analysis/{thread_id}")
        assert status.json()["status"] == "error"

    @pytest.mark.anyio
    async def test_heartbeat_emitted_while_graph_is_busy(
        self, client, monkeypatch
    ):
        monkeypatch.setattr(
            analysis_module, "HEARTBEAT_INTERVAL_SECONDS", 0.05
        )
        start = await client.post("/api/analysis", json={"days": 30})
        thread_id = start.json()["thread_id"]

        # Each event takes 3 heartbeat intervals to arrive
        with patch.object(
            analysis_module,
            "compiled_graph",
            make_fake_graph(HAPPY_EVENTS[:4], delay=0.15),
        ):
            async with client.stream(
                "GET", f"/api/analysis/{thread_id}/stream"
            ) as resp:
                _, comments = await collect_sse(resp)

        assert any("heartbeat" in c for c in comments)
