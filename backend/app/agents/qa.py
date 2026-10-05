
from pydantic import BaseModel, Field

from app.services.llm import get_llm


class QAResult(BaseModel):
    passed: bool = Field(
        description="Whether the resolution passed QA"
    )
    reason: str = Field(
        description="Primary reason for the QA result"
    )
    issues: list[str] = Field(
        default_factory=list,
        description="List of detected QA issues."
    )


class GroundingCheck(BaseModel):
    supported: bool = Field(
        description=(
            "Whether the factual claims in the resolution "
            "are supported by the verified investigation data."
        )
    )
    reason: str = Field(
        description="Explanation for the grounding decision."
    )


VALID_ACTIONS = {
    "refund",
    "delivery_update",
    "no_action",
    "needs_more_information",
}


def validate_resolution_deterministically(
    investigation_results: dict | None,
    resolution_proposal: dict | None,
    approval_status: str | None,
) -> list[str]:
    """
    Validate hard business and workflow rules.

    These checks intentionally do not use an LLM.
    """

    issues: list[str] = []

    if investigation_results is None:
        issues.append(
            "Investigation results are missing."
        )

    if resolution_proposal is None:
        issues.append(
            "Resolution proposal is missing."
        )
        return issues

    action = resolution_proposal.get("action")

    if action not in VALID_ACTIONS:
        issues.append(
            f"Invalid resolution action: {action}"
        )

    reason = resolution_proposal.get("reason")

    if not isinstance(reason, str) or not reason.strip():
        issues.append(
            "Resolution reason is missing."
        )

    next_step = resolution_proposal.get("next_step")

    if not isinstance(next_step, str) or not next_step.strip():
        issues.append(
            "Resolution next_step is missing."
        )

    requires_approval = resolution_proposal.get(
        "requires_approval"
    )

    if not isinstance(requires_approval, bool):
        issues.append(
            "requires_approval must be a boolean."
        )

    # Refunds are sensitive actions and must require approval.
    if action == "refund":

        if requires_approval is not True:
            issues.append(
                "Refund actions must require human approval."
            )

        amount = resolution_proposal.get("amount")

        if amount is None:
            issues.append(
                "Refund action is missing the refund amount."
            )

        elif amount <= 0:
            issues.append(
                "Refund amount must be greater than zero."
            )

    # A request for more information is not a sensitive action.
    if action == "needs_more_information":

        if requires_approval is not False:
            issues.append(
                "needs_more_information must not require human approval."
            )

    # no_action is not a sensitive action.
    if action == "no_action":

        if requires_approval is not False:
            issues.append(
                "no_action must not require human approval."
            )

    # If approval is required, the workflow must have
    # reached an approved state before the action proceeds.
    if requires_approval is True:

        if approval_status == "rejected":
            issues.append(
                "Sensitive action was rejected by the human reviewer."
            )

        elif approval_status != "approve":
            issues.append(
                "Required human approval has not been completed."
            )

    return issues


def check_resolution_grounding(
    user_request: str,
    investigation_results: dict,
    resolution_proposal: dict,
) -> GroundingCheck:
    """
    Use the LLM only as a secondary natural-language
    grounding check.

    The LLM must not decide authorization, business
    eligibility, or whether the resolution is ideal.
    """

    llm = get_llm()

    structured_llm = llm.with_structured_output(
        GroundingCheck
    )

    prompt = f"""
You are performing a factual grounding check for a
customer support automation system.

Your task is VERY narrow.

Determine whether the factual statements made in the
resolution proposal contradict or invent information
relative to the verified investigation data.

Do NOT evaluate whether the proposed resolution is the
best solution.

Do NOT evaluate whether the customer deserves a refund.

Do NOT evaluate whether the action should be approved.

Do NOT decide business eligibility.

Do NOT require the proposal to completely solve the
customer's request.

Customer request:
{user_request}

VERIFIED INVESTIGATION DATA:
{investigation_results}

RESOLUTION PROPOSAL:
{resolution_proposal}

Grounding rules:

1. If the proposal repeats a fact that exists in the
   investigation data, it is supported.

2. If the proposal reasonably summarizes or derives
   information from the investigation data, it is supported.

3. If the proposal asks the customer for information
   that is genuinely unavailable, that is supported.

4. Only mark supported=False when the proposal contains
   a factual claim that contradicts the investigation
   data or clearly invents information that is not
   supported by the investigation.

5. Do NOT mark a proposal unsupported merely because
   you think a different resolution would be better.

6. Do NOT mark a proposal unsupported because it asks
   for additional information.

IMPORTANT EXAMPLE:

Investigation:
Order status = shipped

Resolution:
"The order status is shipped. Please provide additional
information."

Result:
supported=True

The resolution does not need to be the ideal business
decision. It only needs to be factually grounded.

Return only the structured grounding result.
"""

    return structured_llm.invoke(prompt)


def qa_resolution(
    user_request: str,
    investigation_results: dict | None,
    resolution_proposal: dict | None,
    approval_status: str | None,
) -> dict:
    """
    Complete deterministic QA validation.

    Hard business and workflow rules are validated before
    a resolution is allowed to continue.
    """

    deterministic_issues = validate_resolution_deterministically(
        investigation_results=investigation_results,
        resolution_proposal=resolution_proposal,
        approval_status=approval_status,
    )

    if deterministic_issues:
        result = QAResult(
            passed=False,
            reason="Resolution failed deterministic QA checks.",
            issues=deterministic_issues,
        )

        return result.model_dump()

    result = QAResult(
        passed=True,
        reason="Resolution passed deterministic QA checks.",
        issues=[],
    )

    return result.model_dump()