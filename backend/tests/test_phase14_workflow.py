import pytest

from app.graph.nodes import (
    approval_node,
    handle_rejection_node,
    qa_failure_node,
    rework_node,
    response_node,
    route_after_triage,
)
from app.graph.workflow import (
    route_after_approval,
    route_after_qa,
    route_after_resolution,
)


def make_base_state():
    return {
        "user_request": "I want a refund for my order 1001",
        "customer_id": 1,
        "ticket_id": None,
        "issue_type": "refund",
        "investigation_results": {
            "summary": "Verified order 1001.",
            "customer_found": True,
            "orders_found": 1,
            "relevant_order_id": 1001,
            "payment_status": "completed",
            "facts": [
                "Order 1001 exists.",
                "Payment is completed.",
            ],
        },
        "resolution_proposal": {
            "action": "refund",
            "amount": 2499.0,
            "reason": "Eligible refund.",
            "requires_approval": True,
            "next_step": "Process the approved refund.",
        },
        "approval_status": None,
        "qa_result": None,
        "retry_count": 0,
        "final_response": None,
    }


def test_refund_triage_enters_investigation():
    state = make_base_state()

    state["issue_type"] = "refund"

    assert route_after_triage(state) == "investigation"


def test_delivery_triage_enters_investigation():
    state = make_base_state()

    state["issue_type"] = "delivery"

    assert route_after_triage(state) == "investigation"


def test_general_request_enters_investigation():
    state = make_base_state()

    state["issue_type"] = "general"

    assert route_after_triage(state) == "investigation"


def test_invalid_triage_value_raises_error():
    state = make_base_state()

    state["issue_type"] = "unknown"

    with pytest.raises(
        ValueError,
        match="Invalid issue type",
    ):
        route_after_triage(state)


def test_resolution_always_routes_to_approval():
    state = make_base_state()

    assert route_after_resolution(state) == "approval"


def test_missing_resolution_cannot_route():
    state = make_base_state()

    state["resolution_proposal"] = None

    with pytest.raises(
        ValueError,
        match="Resolution proposal is missing",
    ):
        route_after_resolution(state)


def test_approved_resolution_routes_to_qa():
    state = make_base_state()

    state["approval_status"] = "approve"

    assert route_after_approval(state) == "qa"


def test_rejected_resolution_routes_to_rejection():
    state = make_base_state()

    state["approval_status"] = "reject"

    assert route_after_approval(state) == "rejection"


def test_non_sensitive_resolution_routes_to_qa():
    state = make_base_state()

    state["approval_status"] = "not_required"

    assert route_after_approval(state) == "qa"


def test_invalid_approval_status_raises_error():
    state = make_base_state()

    state["approval_status"] = "invalid"

    with pytest.raises(
        ValueError,
        match="Invalid approval status",
    ):
        route_after_approval(state)


def test_rejection_node_marks_request_rejected():
    state = make_base_state()

    state["approval_status"] = "reject"

    result = handle_rejection_node(state)

    assert result["approval_status"] == "rejected"


def test_qa_pass_routes_to_response():
    state = make_base_state()

    state["approval_status"] = "approve"
    state["qa_result"] = {
        "passed": True,
        "reason": "Valid resolution.",
        "issues": [],
    }

    assert route_after_qa(state) == "response"


def test_qa_failure_routes_to_rework():
    state = make_base_state()

    state["approval_status"] = "approve"
    state["qa_result"] = {
        "passed": False,
        "reason": "Invalid resolution.",
        "issues": [
            "Resolution requires correction."
        ],
    }
    state["retry_count"] = 0

    assert route_after_qa(state) == "rework"


def test_qa_failure_at_retry_limit_routes_to_failure():
    state = make_base_state()

    state["approval_status"] = "approve"
    state["qa_result"] = {
        "passed": False,
        "reason": "Invalid resolution.",
        "issues": [
            "Resolution requires correction."
        ],
    }
    state["retry_count"] = 2

    assert route_after_qa(state) == "qa_failure"


def test_rejected_request_does_not_enter_rework():
    state = make_base_state()

    state["approval_status"] = "rejected"
    state["qa_result"] = {
        "passed": False,
        "reason": "Customer rejected the proposed action.",
        "issues": [],
    }

    state["retry_count"] = 0

    assert route_after_qa(state) == "qa_failure"


def test_rework_increments_retry_count():
    state = make_base_state()

    state["qa_result"] = {
        "passed": False,
        "reason": "QA failed.",
        "issues": [
            "Resolution requires correction."
        ],
    }

    state["retry_count"] = 0

    result = rework_node(state)

    assert result["retry_count"] == 1
    assert result["approval_status"] is None


def test_second_rework_increments_retry_count():
    state = make_base_state()

    state["qa_result"] = {
        "passed": False,
        "reason": "QA failed.",
        "issues": [
            "Resolution requires correction."
        ],
    }

    state["retry_count"] = 1

    result = rework_node(state)

    assert result["retry_count"] == 2
    assert result["approval_status"] is None


def test_rework_requires_qa_failure():
    state = make_base_state()

    state["qa_result"] = {
        "passed": True,
        "reason": "QA passed.",
        "issues": [],
    }

    with pytest.raises(
        ValueError,
        match="Rework can only start",
    ):
        rework_node(state)


def test_qa_failure_generates_safe_final_response():
    state = make_base_state()

    state["qa_result"] = {
        "passed": False,
        "reason": "QA failed.",
        "issues": [
            "Invalid resolution."
        ],
    }

    result = qa_failure_node(state)

    assert result["final_response"] is not None
    assert (
        "could not be completed"
        in result["final_response"]
    )


def test_response_node_requires_passed_qa():
    state = make_base_state()

    state["approval_status"] = "approve"
    state["qa_result"] = {
        "passed": False,
        "reason": "QA failed.",
        "issues": [
            "Invalid resolution."
        ],
    }

    with pytest.raises(
        ValueError,
        match="QA did not pass",
    ):
        response_node(state)