from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    analytics_node,
    has_fatal_error,
    historical_node,
    market_node,
    report_node,
    sentiment_node,
    strategy_node,
)
from app.graph.state import AnalysisState


def build_graph(checkpointer=None):
    """Build and compile the 6-node analysis pipeline.

    market/historical/sentiment fan out in parallel and join at analytics.
    If a required fetch failed, the graph ends before the paid LLM stages.
    """
    graph = StateGraph(AnalysisState)

    graph.add_node("market", market_node)
    graph.add_node("historical", historical_node)
    graph.add_node("sentiment", sentiment_node)
    graph.add_node("analytics", analytics_node)
    graph.add_node("strategy", strategy_node)
    graph.add_node("report", report_node)

    graph.add_edge(START, "market")
    graph.add_edge(START, "historical")
    graph.add_edge(START, "sentiment")
    # Join: analytics waits for all three fetch branches
    graph.add_edge(["market", "historical", "sentiment"], "analytics")
    graph.add_conditional_edges(
        "analytics",
        lambda state: END if has_fatal_error(state) else "strategy",
        [END, "strategy"],
    )
    graph.add_edge("strategy", "report")
    graph.add_edge("report", END)

    return graph.compile(checkpointer=checkpointer)


# Shared graph instance — no checkpointer: runs are one-shot and the router
# accumulates node outputs itself, so persisted state would only leak memory
compiled_graph = build_graph()
