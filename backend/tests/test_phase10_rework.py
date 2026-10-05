from app.graph.nodes import (
    qa_node,
    rework_node,
)
from app.graph.workflow import route_after_qa


def test_phase10_qa_failure_enters_rework():
    """
    Verify that a QA failure is routed to the rework path
    when the retry limit has not been reached.
    """

    state = {
        "user_request": "I want a refund for my order 1001",
        "customer_id": 1,
        "ticket_id": None,
        "issue_type": "refund",

        "investigation_results": {
            "summary": "Verified order 1001.",
            "customer_found": True,
            "orders_found": 2,
            "relevant_order_id": 1001,
            "payment_status": "completed",
            "facts": [
                "Order 1001 exists.",
                "Order 1001 is delivered.",
                "Payment is completed.",
            ],
        },

        # Deliberately invalid resolution for testing QA.
        "resolution_proposal": {
            "action": "refund",
            "amount": 2499.0,
            "reason": "Customer requested a refund.",
            "requires_approval": False,
            "next_step": "Process the refund.",
        },

        "approval_status": "not_required",

        "qa_result": None,

        "retry_count": 0,

        "final_response": None,
    }

    # Run deterministic QA.
    state = qa_node(state)

    print("\nQA RESULT:")
    print(state["qa_result"])

    assert state["qa_result"] is not None
    assert state["qa_result"]["passed"] is False

    assert (
        "Refund actions must require human approval."
        in state["qa_result"]["issues"]
    )

    # Verify routing.
    next_node = route_after_qa(state)

    print("\nNEXT NODE:")
    print(next_node)

    assert next_node == "rework"


def test_phase10_rework_increments_retry_count():
    """
    Verify that the rework node increments retry_count
    and resets approval_status.
    """

    state = {
        "user_request": "I want a refund for my order 1001",
        "customer_id": 1,
        "ticket_id": None,
        "issue_type": "refund",

        "investigation_results": {
            "summary": "Verified order 1001.",
            "customer_found": True,
            "orders_found": 2,
            "relevant_order_id": 1001,
            "payment_status": "completed",
            "facts": [
                "Order 1001 exists.",
                "Order 1001 is delivered.",
                "Payment is completed.",
            ],
        },

        "resolution_proposal": {
            "action": "refund",
            "amount": 2499.0,
            "reason": "Customer requested a refund.",
            "requires_approval": False,
            "next_step": "Process the refund.",
        },

        "approval_status": "not_required",

        "qa_result": {
            "passed": False,
            "reason": "Resolution failed deterministic QA checks.",
            "issues": [
                "Refund actions must require human approval."
            ],
        },

        "retry_count": 0,

        "final_response": None,
    }

    state = rework_node(state)

    print("\nREWORK STATE:")
    print(state)

    assert state["retry_count"] == 1
    assert state["approval_status"] is None


def test_phase10_max_retry_limit():
    """
    Verify that QA failure terminates safely once
    MAX_RETRIES has been reached.
    """

    state = {
        "user_request": "I want a refund for my order 1001",
        "customer_id": 1,
        "ticket_id": None,
        "issue_type": "refund",

        "investigation_results": {
            "summary": "Verified order 1001.",
            "customer_found": True,
            "orders_found": 2,
            "relevant_order_id": 1001,
            "payment_status": "completed",
            "facts": [],
        },

        "resolution_proposal": {
            "action": "refund",
            "amount": 2499.0,
            "reason": "Customer requested a refund.",
            "requires_approval": False,
            "next_step": "Process the refund.",
        },

        "approval_status": "not_required",

        "qa_result": {
            "passed": False,
            "reason": "Resolution failed deterministic QA checks.",
            "issues": [
                "Refund actions must require human approval."
            ],
        },

        # MAX_RETRIES = 2
        "retry_count": 2,

        "final_response": None,
    }

    next_node = route_after_qa(state)

    print("\nMAX RETRY NEXT NODE:")
    print(next_node)

    assert next_node == "qa_failure"