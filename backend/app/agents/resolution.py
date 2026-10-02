from typing import Literal

from pydantic import BaseModel, Field

from app.services.llm import get_llm
from app.tools.support_tools import check_refund_eligibility


class ResolutionProposal(BaseModel):
    action: Literal[
        "refund",
        "delivery_update",
        "no_action",
        "needs_more_information",
    ]

    amount: float | None = None

    reason: str

    requires_approval: bool

    next_step: str


def resolve_support_request(
    user_request: str,
    issue_type: str,
    investigation_results: dict,
) -> dict:
    """
    Uses verified investigation data to propose
    a resolution.

    Sensitive actions are proposed only.
    Nothing is executed here.
    """

    llm = get_llm()

    prompt = f"""
You are a customer support resolution agent.

Your job is to propose a resolution based ONLY on
the verified investigation data provided below.

Do not invent customer, order, payment, or refund information.

Customer request:
{user_request}

Issue type:
{issue_type}

Verified investigation results:
{investigation_results}

Rules:

1. For refund requests, use the refund eligibility
   tool before proposing a refund.

2. Never create or execute a refund.

3. A refund proposal must require human approval.

4. If the customer is not eligible for a refund,
   do not propose a refund.

5. For delivery issues, propose an appropriate
   next step based only on the investigation data.

6. If there is insufficient information, request
   more information instead of inventing facts.

Return only the structured resolution proposal.
"""

    if issue_type == "refund":
        order = investigation_results.get("order")

        if not order:
            proposal = ResolutionProposal(
                action="needs_more_information",
                amount=None,
                reason="No verified order was found.",
                requires_approval=False,
                next_step="Request the order details from the customer.",
            )

            return proposal.model_dump()

        eligibility = check_refund_eligibility(
            order_id=order["id"]
        )

        prompt += f"""

Refund eligibility result:

{eligibility}
"""

    structured_llm = llm.with_structured_output(
        ResolutionProposal
    )

    result = structured_llm.invoke(prompt)

    return result.model_dump()