from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import SupportState

from app.graph.nodes import (
    triage_node,
    investigation_node,
    resolution_node,
    approval_node,
    handle_rejection_node,
    response_node,
    route_after_triage,
    qa_node,
    rework_node,
    qa_failure_node,
)


MAX_RETRIES = 2


def route_after_resolution(state: SupportState) -> str:
    resolution_proposal = state["resolution_proposal"]

    if resolution_proposal is None:
        raise ValueError("Resolution proposal is missing.")

    return "approval"


def route_after_approval(state: SupportState) -> str:
    approval_status = state["approval_status"]

    if approval_status == "approve":
        return "qa"

    if approval_status == "reject":
        return "rejection"

    if approval_status == "not_required":
        return "qa"

    raise ValueError(
        f"Invalid approval status: {approval_status}"
    )


def route_after_qa(state: SupportState) -> str:
    qa_result = state["qa_result"]

    if qa_result is None:
        raise ValueError(
            "QA result is missing."
        )

    if qa_result.get("passed") is True:
        return "response"

    # A human rejection is a deliberate workflow decision,
    # not a QA defect to be automatically reworked.
    if state["approval_status"] == "rejected":
        return "qa_failure"

    # retry_count represents completed rework attempts.
    # When it reaches MAX_RETRIES, terminate safely.
    if state["retry_count"] >= MAX_RETRIES:
        return "qa_failure"

    return "rework"


def build_graph():
    graph = StateGraph(SupportState)

    graph.add_node("triage", triage_node)
    graph.add_node("investigation", investigation_node)
    graph.add_node("resolution", resolution_node)
    graph.add_node("approval", approval_node)
    graph.add_node("rejection", handle_rejection_node)
    graph.add_node("qa", qa_node)
    graph.add_node("rework", rework_node)
    graph.add_node("qa_failure", qa_failure_node)
    graph.add_node("response", response_node)

    graph.add_edge(START, "triage")

    graph.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "investigation": "investigation",
        },
    )

    graph.add_edge(
        "investigation",
        "resolution",
    )

    graph.add_conditional_edges(
        "resolution",
        route_after_resolution,
        {
            "approval": "approval",
        },
    )

    graph.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "qa": "qa",
            "rejection": "rejection",
        },
    )

    graph.add_edge(
        "rejection",
        "qa",
    )

    graph.add_conditional_edges(
        "qa",
        route_after_qa,
        {
            "response": "response",
            "rework": "rework",
            "qa_failure": "qa_failure",
        },
    )

    graph.add_edge(
        "rework",
        "resolution",
    )

    graph.add_edge(
        "qa_failure",
        END,
    )

    graph.add_edge(
        "response",
        END,
    )

    checkpointer = MemorySaver()

    return graph.compile(
        checkpointer=checkpointer,
    )