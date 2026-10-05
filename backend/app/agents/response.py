from typing import Literal

from pydantic import BaseModel, Field

from app.services.llm import get_llm


class CustomerResponse(BaseModel):
    response: str = Field(
        description=(
            "A concise, professional, customer-facing response. "
            "Do not expose internal workflow details."
        )
    )


def generate_customer_response(
    user_request: str,
    issue_type: str,
    investigation_results: dict,
    resolution_proposal: dict,
    qa_result: dict,
) -> str:
    """
    Generate the final customer-facing response.

    This function must only be called after the resolution
    has successfully passed QA.

    The response agent does not make business decisions.
    It only communicates an already-validated resolution.
    """

    if not qa_result.get("passed"):
        raise ValueError(
            "Customer response cannot be generated because QA did not pass."
        )

    action = resolution_proposal.get("action")

    valid_actions = {
        "refund",
        "delivery_update",
        "needs_more_information",
        "no_action",
    }

    if action not in valid_actions:
        raise ValueError(
            f"Invalid resolution action for response: {action}"
        )

    llm = get_llm()

    structured_llm = llm.with_structured_output(
        CustomerResponse
    )

    prompt = f"""
You are the final customer support response agent.

Your ONLY responsibility is to communicate the already
validated resolution to the customer.

You MUST NOT make a new business decision.

You MUST NOT change the resolution.

You MUST NOT invent information.

You MUST NOT expose internal system details.

Customer request:
{user_request}

Issue type:
{issue_type}

Verified investigation results:
{investigation_results}

VALIDATED resolution:
{resolution_proposal}

QA result:
{qa_result}

The QA result has already passed.

Supported resolution actions:

1. refund
   Explain that the refund request has been approved
   or is being processed according to the validated
   resolution.

2. delivery_update
   Explain the validated delivery-related outcome
   using only verified information.

3. needs_more_information
   Clearly and politely tell the customer what
   information is needed.

4. no_action
   Clearly explain the validated outcome without
   inventing additional actions.

Response rules:

- Be concise and professional.
- Speak directly to the customer.
- Use only verified information.
- Do not mention agents.
- Do not mention LangGraph.
- Do not mention QA.
- Do not mention retry/rework.
- Do not mention internal database records.
- Do not mention tools.
- Do not expose internal reasoning.
- Do not expose the raw resolution structure.
- Do not invent refund timelines unless they are
  explicitly present in the validated resolution.
- Do not claim an action was executed if the resolution
  only says it was approved or proposed.
- Do not add unsupported promises.

Return only the structured customer response.
"""

    result = structured_llm.invoke(prompt)

    return result.response