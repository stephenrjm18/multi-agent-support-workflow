import pytest

from app.agents.response import generate_customer_response
from app.graph.nodes import response_node
from app.graph.workflow import route_after_triage


class FakeStructuredLLM:
    def invoke(self, prompt):
        class Result:
            response = (
                "Your refund request has been approved. "
                "The refund will be processed according to the "
                "applicable payment processing timeline."
            )

        return Result()


class FakeLLM:
    def with_structured_output(self, schema):
        return FakeStructuredLLM()


def test_response_agent_generates_customer_response(monkeypatch):
    """
    Verify that the Response Agent can generate a
    customer-facing response from a QA-passed state.
    """

    monkeypatch.setattr(
        "app.agents.response.get_llm",
        lambda: FakeLLM(),
    )

    response = generate_customer_response(
        user_request="I want a refund for my order 1001",
        issue_type="refund",
        investigation_results={
            "relevant_order_id": 1001,
            "payment_status": "completed",
            "facts": [
                "Order 1001 exists.",
                "Order 1001 is delivered.",
            ],
        },
        resolution_proposal={
            "action": "refund",
            "amount": 2499.0,
            "reason": "Delivered order is eligible for refund.",
            "requires_approval": True,
            "next_step": "Process the approved refund.",
        },
        qa_result={
            "passed": True,
            "reason": "Resolution passed deterministic QA checks.",
            "issues": [],
        },
    )

    print("\nCUSTOMER RESPONSE:")
    print(response)

    assert isinstance(response, str)
    assert response.strip()


def test_response_agent_rejects_failed_qa(monkeypatch):
    """
    Verify that the Response Agent refuses to generate
    a response when QA has failed.
    """

    monkeypatch.setattr(
        "app.agents.response.get_llm",
        lambda: FakeLLM(),
    )

    with pytest.raises(
        ValueError,
        match="QA did not pass",
    ):
        generate_customer_response(
            user_request="I want a refund for my order 1001",
            issue_type="refund",
            investigation_results={
                "relevant_order_id": 1001,
            },
            resolution_proposal={
                "action": "refund",
                "amount": 2499.0,
                "reason": "Customer requested a refund.",
                "requires_approval": True,
                "next_step": "Process the refund.",
            },
            qa_result={
                "passed": False,
                "reason": "Resolution failed QA.",
                "issues": [
                    "Refund actions must require human approval."
                ],
            },
        )


def test_response_node_requires_qa():
    """
    Verify that the graph response node cannot generate
    a response when QA has not run.
    """

    state = {
        "user_request": "I want a refund for order 1001",
        "customer_id": 1,
        "ticket_id": None,
        "issue_type": "refund",
        "investigation_results": {
            "relevant_order_id": 1001,
        },
        "resolution_proposal": {
            "action": "refund",
            "amount": 2499.0,
            "reason": "Customer requested a refund.",
            "requires_approval": True,
            "next_step": "Process the refund.",
        },
        "approval_status": "approve",
        "qa_result": None,
        "retry_count": 0,
        "final_response": None,
    }

    with pytest.raises(
        ValueError,
        match="QA result is missing",
    ):
        response_node(state)


def test_response_node_rejects_failed_qa():
    """
    Verify that the graph response node cannot generate
    a response after QA failure.
    """

    state = {
        "user_request": "I want a refund for order 1001",
        "customer_id": 1,
        "ticket_id": None,
        "issue_type": "refund",
        "investigation_results": {
            "relevant_order_id": 1001,
        },
        "resolution_proposal": {
            "action": "refund",
            "amount": 2499.0,
            "reason": "Customer requested a refund.",
            "requires_approval": True,
            "next_step": "Process the refund.",
        },
        "approval_status": "approve",
        "qa_result": {
            "passed": False,
            "reason": "Resolution failed QA.",
            "issues": [
                "Example validation failure."
            ],
        },
        "retry_count": 0,
        "final_response": None,
    }

    with pytest.raises(
        ValueError,
        match="QA did not pass",
    ):
        response_node(state)


def test_general_requests_enter_controlled_workflow():
    """
    Verify that general requests no longer bypass
    investigation and QA.
    """

    state = {
        "user_request": "Can you help me with my account?",
        "customer_id": 1,
        "ticket_id": None,
        "issue_type": "general",
        "investigation_results": None,
        "resolution_proposal": None,
        "approval_status": None,
        "qa_result": None,
        "retry_count": 0,
        "final_response": None,
    }

    assert route_after_triage(state) == "investigation"