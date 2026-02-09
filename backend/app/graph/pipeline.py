from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import AnalysisState
from app.graph.nodes import (
    market_node,
    historical_node,
    sentiment_node,
    analytics_node,
    strategy_node,
    report_node,
)


def build_graph(checkpointer=None):
    """Build and compile the 6-node analysis pipeline."""
    graph = StateGraph(AnalysisState)

    # Add nodes
    graph.add_node("market", market_node)
    graph.add_node("historical", historical_node)
    graph.add_node("sentiment", sentiment_node)
    graph.add_node("analytics", analytics_node)
    graph.add_node("strategy", strategy_node)
    graph.add_node("report", report_node)

    # Sequential edges
    graph.add_edge(START, "market")
    graph.add_edge("market", "historical")
    graph.add_edge("historical", "sentiment")
    graph.add_edge("sentiment", "analytics")
    graph.add_edge("analytics", "strategy")
    graph.add_edge("strategy", "report")
    graph.add_edge("report", END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)


# Shared graph instance
memory = MemorySaver()
compiled_graph = build_graph(checkpointer=memory)
