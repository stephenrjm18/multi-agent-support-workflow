from typing import Literal

from pydantic import BaseModel, Field


class SupportRequest(BaseModel):
    """
    Input received when a customer starts a support request.
    """

    user_request: str = Field(
        min_length=1,
        description="The customer's support request.",
    )

    customer_id: int = Field(
        gt=0,
        description="ID of the customer making the request.",
    )

    ticket_id: int | None = Field(
        default=None,
        description="Optional existing support ticket ID.",
    )


class ApprovalRequest(BaseModel):
    """
    Human decision submitted when the workflow is paused
    for approval.
    """

    decision: Literal["approve", "reject"]


class ApprovalDetails(BaseModel):
    """
    Information exposed to the human reviewer.

    Internal workflow details are intentionally excluded.
    """

    type: str
    message: str
    action: str | None = None
    amount: float | None = None
    reason: str | None = None
    next_step: str | None = None
    options: list[str]


class SupportRequestResponse(BaseModel):
    """
    Response returned after starting or continuing a workflow.
    """

    thread_id: str

    status: Literal[
        "awaiting_approval",
        "completed",
    ]

    message: str

    approval_required: bool = False

    approval: ApprovalDetails | None = None

    final_response: str | None = None


class WorkflowStatusResponse(BaseModel):
    """
    Current externally visible workflow status.
    """

    thread_id: str

    status: Literal[
        "awaiting_approval",
        "completed",
    ]

    approval_required: bool = False

    approval: ApprovalDetails | None = None

    final_response: str | None = None