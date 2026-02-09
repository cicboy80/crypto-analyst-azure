import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestHealthEndpoint:
    @pytest.mark.anyio
    async def test_health_returns_200(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestAnalysisEndpoints:
    @pytest.mark.anyio
    async def test_start_analysis_returns_202(self, client):
        resp = await client.post(
            "/api/analysis",
            json={"crypto_name": "bitcoin", "currency": "usd", "days": 365},
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "thread_id" in data
        assert data["status"] == "pending"

    @pytest.mark.anyio
    async def test_start_analysis_default_values(self, client):
        resp = await client.post("/api/analysis", json={})
        assert resp.status_code == 202

    @pytest.mark.anyio
    async def test_start_analysis_invalid_days(self, client):
        resp = await client.post(
            "/api/analysis",
            json={"crypto_name": "bitcoin", "currency": "usd", "days": 5},
        )
        assert resp.status_code == 422  # Validation error

    @pytest.mark.anyio
    async def test_start_analysis_days_too_high(self, client):
        resp = await client.post(
            "/api/analysis",
            json={"crypto_name": "bitcoin", "currency": "usd", "days": 1000},
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_get_analysis_not_found(self, client):
        resp = await client.get("/api/analysis/nonexistent-id")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_get_analysis_after_start(self, client):
        # Start an analysis
        start_resp = await client.post(
            "/api/analysis",
            json={"crypto_name": "bitcoin", "currency": "usd", "days": 365},
        )
        thread_id = start_resp.json()["thread_id"]

        # Poll for status
        status_resp = await client.get(f"/api/analysis/{thread_id}")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["thread_id"] == thread_id
        assert data["status"] == "pending"

    @pytest.mark.anyio
    async def test_stream_endpoint_returns_sse(self, client):
        # Start analysis to create a job
        start_resp = await client.post(
            "/api/analysis",
            json={"crypto_name": "bitcoin", "currency": "usd", "days": 30},
        )
        thread_id = start_resp.json()["thread_id"]

        # The stream endpoint should return text/event-stream content type
        # We just verify the endpoint is reachable (full SSE testing needs mock pipeline)
        with patch("app.routers.analysis.compiled_graph") as mock_graph:
            # Mock astream_events to return empty async iterator
            async def empty_stream(*args, **kwargs):
                return
                yield  # make it an async generator

            mock_graph.astream_events = empty_stream
            mock_graph.get_state.return_value = MagicMock(
                values={
                    "market_data": None,
                    "historical_data": None,
                    "sentiment_data": None,
                    "analytics_data": None,
                    "strategy_data": None,
                    "report": None,
                }
            )

            resp = await client.get(
                f"/api/analysis/{thread_id}/stream",
                params={"crypto_name": "bitcoin", "currency": "usd", "days": "30"},
            )
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers["content-type"]
