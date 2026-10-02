from langgraph.graph import StateGraph, START, END

from app.graph.state import SupportState
from app.graph.nodes import (
    triage_node,
    investigation_node,
    response_node,
    route_after_triage,
)


def build_graph():
    graph = StateGraph(SupportState)

    graph.add_node("triage", triage_node)
    graph.add_node("investigation", investigation_node)
    graph.add_node("response", response_node)

    graph.add_edge(START, "triage")

    graph.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "investigation": "investigation",
            "response": "response",
        },
    )

    graph.add_edge("investigation", END)
    graph.add_edge("response", END)

    return graph.compile()