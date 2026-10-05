from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy"
    }


def test_support_request_validation():
    response = client.post(
        "/support/request",
        json={
            "user_request": "",
            "customer_id": 1,
        },
    )

    assert response.status_code == 422


def test_approval_validation():
    response = client.post(
        "/support/request/test-thread/approval",
        json={
            "decision": "invalid"
        },
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
            "decision": "approve"
        },
    )

    assert response.status_code == 404