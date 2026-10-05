import json
from pathlib import Path

from app.graph.nodes import route_after_triage


EVALUATION_FILE = (
    Path(__file__).parent
    / "evaluation_cases.json"
)


def load_evaluation_cases():
    with open(
        EVALUATION_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def test_evaluation_dataset_exists():
    cases = load_evaluation_cases()

    assert isinstance(cases, list)
    assert len(cases) >= 5


def test_evaluation_cases_have_required_fields():
    cases = load_evaluation_cases()

    required_fields = {
        "id",
        "category",
        "user_request",
        "customer_id",
        "expected_issue_type",
    }

    for case in cases:
        assert required_fields.issubset(
            case.keys()
        )

        assert case["user_request"].strip()
        assert case["customer_id"] > 0


def test_evaluation_issue_types_are_valid():
    cases = load_evaluation_cases()

    valid_issue_types = {
        "refund",
        "delivery",
        "general",
    }

    for case in cases:
        assert (
            case["expected_issue_type"]
            in valid_issue_types
        )


def test_evaluation_routing_cases():
    """
    Verify that every evaluation case maps to the
    expected controlled workflow route.
    """

    cases = load_evaluation_cases()

    for case in cases:
        state = {
            "user_request": case["user_request"],
            "customer_id": case["customer_id"],
            "ticket_id": None,
            "issue_type": case["expected_issue_type"],
            "investigation_results": None,
            "resolution_proposal": None,
            "approval_status": None,
            "qa_result": None,
            "retry_count": 0,
            "final_response": None,
        }

        next_node = route_after_triage(state)

        assert next_node == "investigation", (
            f"Evaluation case {case['id']} "
            f"did not enter investigation."
        )