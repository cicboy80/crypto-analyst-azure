import json
import uuid
import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models import AnalysisRequest, AnalysisStatus
from app.graph.pipeline import compiled_graph
from app.graph.nodes import NODE_NAMES
from app.services.job_manager import job_manager

router = APIRouter()


@router.post("/api/analysis", status_code=202)
async def start_analysis(request: AnalysisRequest):
    """Start a new analysis run. Returns a thread_id for streaming."""
    thread_id = str(uuid.uuid4())
    job_manager.create(thread_id)
    return {"thread_id": thread_id, "status": "pending"}


@router.get("/api/analysis/{thread_id}/stream")
async def stream_analysis(thread_id: str, crypto_name: str = "bitcoin", currency: str = "usd", days: int = 365):
    """SSE endpoint that runs the LangGraph pipeline and streams node results."""

    async def event_generator() -> AsyncGenerator[str, None]:
        job_manager.update(thread_id, status="running")

        initial_state = {
            "crypto_name": crypto_name.lower(),
            "currency": currency.lower(),
            "days": days,
        }

        config = {"configurable": {"thread_id": thread_id}}

        completed_nodes: set[str] = set()
        step_counter = 0

        try:
            async for event in compiled_graph.astream_events(
                initial_state, config=config, version="v2"
            ):
                kind = event.get("event")
                name = event.get("name")

                # Detect node starts
                if kind == "on_chain_start" and name in NODE_NAMES:
                    step_counter = NODE_NAMES.index(name) + 1
                    job_manager.update(
                        thread_id,
                        current_step=name,
                        steps_completed=step_counter - 1,
                    )
                    sse_data = json.dumps({
                        "node": name,
                        "step": step_counter,
                        "total_steps": len(NODE_NAMES),
                    })
                    yield f"event: node_start\ndata: {sse_data}\n\n"

                # Detect node completions
                if kind == "on_chain_end" and name in NODE_NAMES and name not in completed_nodes:
                    completed_nodes.add(name)
                    output = event.get("data", {}).get("output", {})

                    # Extract the relevant data from the node output
                    node_result = _extract_node_result(name, output)

                    step_num = NODE_NAMES.index(name) + 1
                    job_manager.update(
                        thread_id,
                        steps_completed=step_num,
                    )

                    sse_data = json.dumps({
                        "node": name,
                        "step": step_num,
                        "total_steps": len(NODE_NAMES),
                        "result": node_result,
                    }, default=str)
                    yield f"event: node_complete\ndata: {sse_data}\n\n"

            # Get final state from checkpointer
            final_state = compiled_graph.get_state(config)
            state_values = final_state.values if final_state else {}

            final_result = {
                "market_data": state_values.get("market_data"),
                "historical_data": state_values.get("historical_data"),
                "sentiment_data": state_values.get("sentiment_data"),
                "analytics_data": state_values.get("analytics_data"),
                "strategy_data": state_values.get("strategy_data"),
                "report": state_values.get("report"),
            }

            job_manager.update(
                thread_id,
                status="completed",
                steps_completed=len(NODE_NAMES),
                result=final_result,
            )

            sse_data = json.dumps({
                "report": state_values.get("report", ""),
                "all_data": final_result,
            }, default=str)
            yield f"event: complete\ndata: {sse_data}\n\n"

        except Exception as e:
            job_manager.update(
                thread_id, status="error", error=str(e)
            )
            sse_data = json.dumps({"error": str(e)})
            yield f"event: error\ndata: {sse_data}\n\n"

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
