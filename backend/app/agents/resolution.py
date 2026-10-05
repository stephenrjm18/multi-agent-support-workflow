from typing import Literal

from pydantic import BaseModel

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
    previous_resolution_proposal: dict | None = None,
    qa_feedback: list[str] | None = None,
    retry_count: int = 0,
) -> dict:
    """
    Uses verified investigation data to propose a resolution.

    On a retry, the previous proposal and QA feedback are supplied
    so the LLM can correct the specific validation problems.

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

4. If the refund eligibility result says the customer
   is not eligible, the action MUST NOT be "refund".

5. If the refund eligibility result says the customer
   is eligible, the action may be "refund" and
   requires_approval MUST be True.

6. If the refund eligibility result is unclear or required
   information is missing, use "needs_more_information".

7. "needs_more_information" MUST have
   requires_approval set to False.

8. "no_action" MUST have requires_approval set to False.

9. For delivery issues, propose an appropriate
   next step based only on the investigation data.

10. For general requests, use "no_action" when the
    verified information is sufficient to answer the
    request without a specific support action.

11. For general requests, use "needs_more_information"
    when the verified information is insufficient.

12. Never invent a specific action for a general request.

13. If there is insufficient information, request
    more information instead of inventing facts.
"""

    if retry_count > 0:
        prompt += f"""

IMPORTANT: This is resolution rework attempt #{retry_count}.

The previous resolution proposal failed QA.

Previous resolution proposal:
{previous_resolution_proposal}

QA feedback/issues:
{qa_feedback}

Rework instructions:

1. Correct the specific QA issues listed above.
2. Do not ignore the QA issues.
3. Do not blindly repeat the previous proposal.
4. Preserve facts that are supported by the verified
   investigation data.
5. Do not invent new facts to satisfy QA.
6. Do not redo or replace the investigation.
7. Return a complete corrected resolution proposal.
"""

    if issue_type == "refund":

        relevant_order_id = investigation_results.get(
            "relevant_order_id"
        )

        if not relevant_order_id:
            proposal = ResolutionProposal(
                action="needs_more_information",
                amount=None,
                reason="No verified order was found.",
                requires_approval=False,
                next_step="Request the order details from the customer.",
            )

            return proposal.model_dump()

        eligibility = check_refund_eligibility(
            order_id=relevant_order_id
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