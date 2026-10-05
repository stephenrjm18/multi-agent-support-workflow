from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy"
    }


def test_support_request_empty_user_request_returns_422():
    response = client.post(
        "/support/request",
        json={
            "user_request": "",
            "customer_id": 1,
        },
    )

    assert response.status_code == 422


def test_support_request_missing_customer_id_returns_422():
    response = client.post(
        "/support/request",
        json={
            "user_request": "I want a refund for my order",
        },
    )

    assert response.status_code == 422


def test_support_request_invalid_customer_id_returns_422():
    response = client.post(
        "/support/request",
        json={
            "user_request": "I want a refund for my order",
            "customer_id": 0,
        },
    )

    assert response.status_code == 422


def test_support_request_invalid_customer_id_type_returns_422():
    response = client.post(
        "/support/request",
        json={
            "user_request": "I want a refund for my order",
            "customer_id": "invalid",
        },
    )

    assert response.status_code == 422


def test_invalid_approval_value_returns_422():
    response = client.post(
        "/support/request/test-thread/approval",
        json={
            "decision": "invalid",
        },
    )

    assert response.status_code == 422


def test_missing_approval_decision_returns_422():
    response = client.post(
        "/support/request/test-thread/approval",
        json={},
    )

    assert response.status_code == 422


def test_missing_workflow_returns_404():
    response = client.get(
        "/support/request/non-existent-thread"
    )

    assert response.status_code == 404


def test_missing_workflow_approval_returns_404():
    response = client.post(
        "/support/request/non-existent-thread/approval",
        json={
            "decision": "approve",
        },
    )

    assert response.status_code == 404


def test_approval_for_completed_workflow_returns_409(
    monkeypatch,
):
    """
    Verify that approval cannot be submitted after the
    workflow is no longer waiting for human approval.
    """

    class FakeSnapshot:
        values = {
            "user_request": "Test request",
        }
        tasks = []

    monkeypatch.setattr(
        "app.main.graph.get_state",
        lambda config: FakeSnapshot(),
    )

    response = client.post(
        "/support/request/completed-thread/approval",
        json={
            "decision": "approve",
        },
    )

    assert response.status_code == 409


def test_status_endpoint_returns_awaiting_approval(
    monkeypatch,
):
    """
    Verify that the API exposes an approval-required state
    when LangGraph has a pending interrupt.
    """

    class FakeInterrupt:
        value = {
            "type": "human_approval_required",
            "message": "Approval required.",
            "action": "refund",
            "amount": 2499.0,
            "reason": "Refund requested.",
            "next_step": "Process refund.",
            "options": [
                "approve",
                "reject",
            ],
        }

    class FakeTask:
        interrupts = [FakeInterrupt()]

    class FakeSnapshot:
        values = {
            "user_request": "I want a refund",
        }
        tasks = [FakeTask()]

    monkeypatch.setattr(
        "app.main.graph.get_state",
        lambda config: FakeSnapshot(),
    )

    response = client.get(
        "/support/request/test-thread"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["thread_id"] == "test-thread"
    assert data["status"] == "awaiting_approval"
    assert data["approval_required"] is True
    assert data["approval"]["action"] == "refund"
    assert data["approval"]["amount"] == 2499.0
    assert data["approval"]["options"] == [
        "approve",
        "reject",
    ]


def test_status_endpoint_returns_completed_workflow(
    monkeypatch,
):
    """
    Verify that a completed workflow is exposed correctly
    by the status endpoint.
    """

    class FakeSnapshot:
        values = {
            "final_response": (
                "Your request has been completed."
            ),
        }
        tasks = []

    monkeypatch.setattr(
        "app.main.graph.get_state",
        lambda config: FakeSnapshot(),
    )

    response = client.get(
        "/support/request/test-thread"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["thread_id"] == "test-thread"
    assert data["status"] == "completed"
    assert data["approval_required"] is False
    assert data["approval"] is None
    assert data["final_response"] == (
        "Your request has been completed."
    )