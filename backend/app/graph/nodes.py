from app.graph.state import SupportState
from app.services.llm import get_llm
from app.agents.triage import TriageResult

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
    issue_type = state["issue_type"]

    return {
        **state,
        "final_response": f"Your request was identified as: {issue_type}",
    }

def route_after_triage(state: SupportState) -> str:
    issue_type = state["issue_type"]

    if issue_type == "refund":
        return "investigation"

    if issue_type == "delivery":
        return "investigation"

    return "response"

def investigation_node(state: SupportState) -> SupportState:
    issue_type = state["issue_type"]

    return {
        **state,
        "investigation_results": {
            "status": "demo",
            "message": f"Investigation required for: {issue_type}",
        },
    }