from app.graph.state import SupportState
from app.services.llm import get_llm
from langgraph.types import interrupt

from app.agents.triage import TriageResult
from app.agents.investigation import investigate
from app.agents.resolution import resolve_support_request
from app.agents.qa import qa_resolution
from app.agents.response import generate_customer_response


def triage_node(state: SupportState) -> SupportState:
    user_request = state["user_request"]

    llm = get_llm()

    structured_llm = llm.with_structured_output(TriageResult)

    prompt = f"""
You are a customer support triage agent.

Classify the customer's request into exactly one of these categories:

- refund
- delivery
- general

Definitions:

refund:
The customer wants a refund, return-related resolution, or money back.

delivery:
The customer is asking about a late, missing, delayed, or delivery-related issue.

general:
The request does not clearly belong to refund or delivery.

Customer request:
{user_request}
"""

    result = structured_llm.invoke(prompt)

    return {
        **state,
        "issue_type": result.issue_type,
    }


def response_node(state: SupportState) -> SupportState:
    """
    Generate the final customer-facing response.

    The response is allowed only after QA has passed.
    """

    qa_result = state["qa_result"]

    if qa_result is None:
        raise ValueError(
            "QA result is missing. Cannot generate customer response."
        )

    if qa_result.get("passed") is not True:
        raise ValueError(
            "QA did not pass. Cannot generate customer response."
        )

    issue_type = state["issue_type"]
    investigation_results = state["investigation_results"]
    resolution_proposal = state["resolution_proposal"]

    if issue_type is None:
        raise ValueError(
            "Issue type is missing."
        )

    if investigation_results is None:
        raise ValueError(
            "Investigation results are missing."
        )

    if resolution_proposal is None:
        raise ValueError(
            "Resolution proposal is missing."
        )

    final_response = generate_customer_response(
        user_request=state["user_request"],
        issue_type=issue_type,
        investigation_results=investigation_results,
        resolution_proposal=resolution_proposal,
        qa_result=qa_result,
    )

    return {
        **state,
        "final_response": final_response,
    }


def route_after_triage(state: SupportState) -> str:
    issue_type = state["issue_type"]

    if issue_type not in {
        "refund",
        "delivery",
        "general",
    }:
        raise ValueError(
            f"Invalid issue type: {issue_type}"
        )

    # Every request enters the controlled workflow so that
    # every final customer response is QA-gated.
    return "investigation"


def investigation_node(state: SupportState) -> SupportState:
    user_request = state["user_request"]
    customer_id = state["customer_id"]
    issue_type = state["issue_type"]

    if customer_id is None:
        raise ValueError(
            "customer_id is required for investigation"
        )

    if issue_type is None:
        raise ValueError(
            "issue_type is required for investigation"
        )

    investigate_results = investigate(
        user_request=user_request,
        customer_id=customer_id,
        issue_type=issue_type,
    )

    return {
        **state,
        "investigation_results": investigate_results,
    }


def resolution_node(state: SupportState) -> SupportState:
    user_request = state["user_request"]
    issue_type = state["issue_type"]
    investigation_results = state["investigation_results"]
    retry_count = state["retry_count"]
    previous_resolution_proposal = state["resolution_proposal"]
    qa_result = state["qa_result"]

    if issue_type is None:
        raise ValueError(
            "Issue type is missing."
        )

    if investigation_results is None:
        raise ValueError(
            "Investigation results are missing."
        )

    qa_feedback = None

    if retry_count > 0:
        if previous_resolution_proposal is None:
            raise ValueError(
                "Previous resolution proposal is missing for rework."
            )

        if qa_result is None:
            raise ValueError(
                "QA result is missing for rework."
            )

        qa_feedback = qa_result.get("issues", [])

    resolution_proposal = resolve_support_request(
        user_request=user_request,
        issue_type=issue_type,
        investigation_results=investigation_results,
        previous_resolution_proposal=previous_resolution_proposal,
        qa_feedback=qa_feedback,
        retry_count=retry_count,
    )

    return {
        **state,
        "resolution_proposal": resolution_proposal,
    }


def approval_node(state: SupportState) -> SupportState:
    resolution_proposal = state["resolution_proposal"]

    if resolution_proposal is None:
        raise ValueError(
            "Resolution proposal is missing."
        )

    requires_approval = resolution_proposal.get(
        "requires_approval",
        False,
    )

    # No human approval is required.
    if not requires_approval:
        return {
            **state,
            "approval_status": "not_required",
        }

    # Pause the graph and request a human decision.
    decision = interrupt(
        {
            "type": "human_approval_required",
            "message": "A sensitive action requires human approval.",
            "action": resolution_proposal.get("action"),
            "amount": resolution_proposal.get("amount"),
            "reason": resolution_proposal.get("reason"),
            "next_step": resolution_proposal.get("next_step"),
            "options": ["approve", "reject"],
        }
    )

    # Validate the human decision.
    if not isinstance(decision, str):
        raise ValueError(
            "Invalid approval decision. Expected 'approve' or 'reject'."
        )

    decision = decision.strip().lower()

    if decision not in {"approve", "reject"}:
        raise ValueError(
            "Invalid approval decision. Expected 'approve' or 'reject'."
        )

    return {
        **state,
        "approval_status": decision,
    }


def handle_rejection_node(state: SupportState) -> SupportState:
    return {
        **state,
        "approval_status": "rejected",
    }


def qa_node(state: SupportState) -> SupportState:
    user_request = state["user_request"]
    investigation_results = state["investigation_results"]
    resolution_proposal = state["resolution_proposal"]
    approval_status = state["approval_status"]

    qa_result = qa_resolution(
        user_request=user_request,
        investigation_results=investigation_results,
        resolution_proposal=resolution_proposal,
        approval_status=approval_status,
    )

    return {
        **state,
        "qa_result": qa_result,
    }


def rework_node(state: SupportState) -> SupportState:
    qa_result = state["qa_result"]
    retry_count = state["retry_count"]

    if qa_result is None:
        raise ValueError(
            "QA result is missing. Cannot start rework."
        )

    if qa_result.get("passed") is not False:
        raise ValueError(
            "Rework can only start after a QA failure."
        )

    return {
        **state,
        "retry_count": retry_count + 1,
        "approval_status": None,
    }


def qa_failure_node(state: SupportState) -> SupportState:
    qa_result = state["qa_result"]

    if qa_result is None:
        raise ValueError(
            "QA result is missing."
        )

    return {
        **state,
        "final_response": (
            "The proposed resolution could not be completed "
            "because it did not pass the required validation."
        ),
    }