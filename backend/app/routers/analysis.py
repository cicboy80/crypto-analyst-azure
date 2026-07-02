import asyncio
import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.graph.nodes import NODE_NAMES, has_fatal_error
from app.graph.pipeline import compiled_graph
from app.models import AnalysisRequest, AnalysisStatus
from app.services.job_manager import job_manager

router = APIRouter()

# SSE comment emitted while the graph is busy so proxies don't drop the
# idle connection; module-level so tests can shrink it
HEARTBEAT_INTERVAL_SECONDS = 15.0


@router.post("/api/analysis", status_code=202)
async def start_analysis(request: AnalysisRequest):
    """Start a new analysis run. Returns a thread_id for streaming."""
    thread_id = str(uuid.uuid4())
    job_manager.create(thread_id, params=request)
    return {"thread_id": thread_id, "status": "pending"}


@router.get("/api/analysis/{thread_id}/stream")
async def stream_analysis(thread_id: str, request: Request):
    """SSE endpoint that runs the LangGraph pipeline and streams node results."""
    job = job_manager.get(thread_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if job.status == "running":
        raise HTTPException(status_code=409, detail="Analysis already streaming")

    params = job.params or AnalysisRequest()

    async def event_generator() -> AsyncGenerator[str, None]:
        job_manager.update(thread_id, status="running")

        initial_state = {
            "crypto_name": params.crypto_name.lower(),
            "currency": params.currency.lower(),
            "days": params.days,
        }

        completed_nodes: set[str] = set()
        # Node outputs accumulated here (unstripped, so price_history is
        # available for the final complete event); replaces the checkpointer
        accumulated: dict = {"errors": []}
        pending: asyncio.Task | None = None

        try:
            events = aiter(
                compiled_graph.astream_events(initial_state, version="v2")
            )

            while True:
                if await request.is_disconnected():
                    # Client is gone; abandon the run and drop the job
                    job_manager.delete(thread_id)
                    return

                if pending is None:
                    pending = asyncio.ensure_future(anext(events))

                done, _ = await asyncio.wait(
                    {pending}, timeout=HEARTBEAT_INTERVAL_SECONDS
                )
                if not done:
                    yield ": heartbeat\n\n"
                    continue

                task, pending = pending, None
                try:
                    event = task.result()
                except StopAsyncIteration:
                    break

                kind = event.get("event")
                name = event.get("name")

                if kind == "on_chain_start" and name in NODE_NAMES:
                    job_manager.update(thread_id, current_step=name)
                    sse_data = json.dumps({
                        "node": name,
                        "total_steps": len(NODE_NAMES),
                    })
                    yield f"event: node_start\ndata: {sse_data}\n\n"

                if kind == "on_chain_end" and name in NODE_NAMES and name not in completed_nodes:
                    completed_nodes.add(name)
                    output = event.get("data", {}).get("output", {}) or {}
                    for key, value in output.items():
                        if key == "errors":
                            accumulated["errors"].extend(value)
                        else:
                            accumulated[key] = value

                    node_result = _extract_node_result(name, output)

                    job_manager.update(
                        thread_id,
                        steps_completed=len(completed_nodes),
                    )

                    sse_data = json.dumps({
                        "node": name,
                        "completed": len(completed_nodes),
                        "total_steps": len(NODE_NAMES),
                        "result": node_result,
                    }, default=str)
                    yield f"event: node_complete\ndata: {sse_data}\n\n"

            if has_fatal_error(accumulated):
                error_msg = "; ".join(accumulated["errors"]) or "Analysis failed"
                job_manager.update(thread_id, status="error", error=error_msg)
                sse_data = json.dumps({"error": error_msg})
                yield f"event: error\ndata: {sse_data}\n\n"
                return

            final_result = {
                "market_data": accumulated.get("market_data"),
                "historical_data": accumulated.get("historical_data"),
                "sentiment_data": accumulated.get("sentiment_data"),
                "analytics_data": accumulated.get("analytics_data"),
                "strategy_data": accumulated.get("strategy_data"),
                "report": accumulated.get("report"),
            }

            job_manager.update(
                thread_id,
                status="completed",
                steps_completed=len(completed_nodes),
                result=final_result,
            )

            sse_data = json.dumps({
                "report": accumulated.get("report", ""),
                "all_data": final_result,
                "errors": accumulated["errors"],
            }, default=str)
            yield f"event: complete\ndata: {sse_data}\n\n"

        except Exception as e:
            job_manager.update(
                thread_id, status="error", error=str(e)
            )
            sse_data = json.dumps({"error": str(e)})
            yield f"event: error\ndata: {sse_data}\n\n"

        finally:
            if pending is not None:
                pending.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/api/analysis/{thread_id}")
async def get_analysis_status(thread_id: str):
    """Polling fallback — returns current job state."""
    job = job_manager.get(thread_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return AnalysisStatus(
        thread_id=job.thread_id,
        status=job.status,
        current_step=job.current_step,
        steps_completed=job.steps_completed,
        result=job.result,
        error=job.error,
    )


def _extract_node_result(node_name: str, output: dict) -> dict:
    """Extract the relevant data payload from a node's output dict."""
    key_map = {
        "market": "market_data",
        "historical": "historical_data",
        "sentiment": "sentiment_data",
        "analytics": "analytics_data",
        "strategy": "strategy_data",
        "report": "report",
    }

    key = key_map.get(node_name)
    if key and key in output:
        result = output[key]
        # For historical data, exclude price_history from SSE to reduce payload
        # (frontend gets it from the complete event)
        if node_name == "historical" and isinstance(result, dict):
            return {
                k: v for k, v in result.items() if k != "price_history"
            }
        return result

    return output
