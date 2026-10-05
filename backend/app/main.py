from uuid import uuid4

from fastapi import FastAPI, HTTPException

from langgraph.types import Command
from fastapi.middleware.cors import CORSMiddleware

from app.graph.workflow import build_graph
from app.schemas import (
    ApprovalDetails,
    ApprovalRequest,
    SupportRequest,
    SupportRequestResponse,
    WorkflowStatusResponse,
)


app = FastAPI(
    title="Multi-Agent Customer Support API",
    version="0.2.0",
    description=(
        "API for the Multi-Agent Customer Support "
        "Automation & Operations Platform."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
         "https://multi-agent-support-workflow-6qm2tjn8i-stephen-a077.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Graph
# ---------------------------------------------------------

graph = build_graph()


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _make_config(thread_id: str) -> dict:
    """
    Create the LangGraph configuration for a workflow thread.
    """

    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def _extract_interrupt(result: dict) -> dict | None:
    """
    Extract the first LangGraph interrupt payload.

    Returns None when the workflow did not pause.
    """

    interrupts = result.get("__interrupt__", [])

    if not interrupts:
        return None

    interrupt_value = interrupts[0].value

    if not isinstance(interrupt_value, dict):
        raise ValueError(
            "Invalid workflow interrupt payload."
        )

    return interrupt_value


def _get_pending_interrupt(config: dict) -> dict | None:
    """
    Read the current checkpoint and determine whether the
    workflow is waiting for human approval.
    """

    snapshot = graph.get_state(config)

    for task in snapshot.tasks:

        interrupts = getattr(
            task,
            "interrupts",
            None,
        )

        if not interrupts:
            continue

        interrupt_value = interrupts[0].value

        if isinstance(interrupt_value, dict):
            return interrupt_value

    return None


def _approval_details(
    interrupt_value: dict,
) -> ApprovalDetails:
    """
    Convert the internal interrupt payload into the public
    API schema.
    """

    return ApprovalDetails(
        type=interrupt_value.get(
            "type",
            "human_approval_required",
        ),
        message=interrupt_value.get(
            "message",
            "Human approval is required.",
        ),
        action=interrupt_value.get("action"),
        amount=interrupt_value.get("amount"),
        reason=interrupt_value.get("reason"),
        next_step=interrupt_value.get("next_step"),
        options=interrupt_value.get(
            "options",
            ["approve", "reject"],
        ),
    )


def _build_completed_response(
    thread_id: str,
    result: dict,
) -> SupportRequestResponse:
    """
    Build a response for a completed workflow.
    """

    return SupportRequestResponse(
        thread_id=thread_id,
        status="completed",
        message="Support request completed.",
        approval_required=False,
        approval=None,
        final_response=result.get("final_response"),
    )


def _build_approval_response(
    thread_id: str,
    interrupt_value: dict,
) -> SupportRequestResponse:
    """
    Build a response when the workflow pauses for approval.
    """

    return SupportRequestResponse(
        thread_id=thread_id,
        status="awaiting_approval",
        message="Human approval is required before the workflow can continue.",
        approval_required=True,
        approval=_approval_details(
            interrupt_value
        ),
        final_response=None,
    )


def _build_status_response(
    thread_id: str,
    state_values: dict,
    interrupt_value: dict | None,
) -> WorkflowStatusResponse:
    """
    Build the externally visible workflow status.
    """

    if interrupt_value is not None:
        return WorkflowStatusResponse(
            thread_id=thread_id,
            status="awaiting_approval",
            approval_required=True,
            approval=_approval_details(
                interrupt_value
            ),
            final_response=None,
        )

    return WorkflowStatusResponse(
        thread_id=thread_id,
        status="completed",
        approval_required=False,
        approval=None,
        final_response=state_values.get(
            "final_response"
        ),
    )


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# ---------------------------------------------------------
# Start support request
# ---------------------------------------------------------

@app.post(
    "/support/request",
    response_model=SupportRequestResponse,
)
def create_support_request(
    request: SupportRequest,
):
    """
    Start a new customer support workflow.

    The workflow receives a unique thread ID so that
    LangGraph can persist and resume its state.
    """

    thread_id = uuid4().hex

    config = _make_config(
        thread_id
    )

    initial_state = {
        "user_request": request.user_request,
        "customer_id": request.customer_id,
        "ticket_id": request.ticket_id,
        "issue_type": None,
        "investigation_results": None,
        "resolution_proposal": None,
        "approval_status": None,
        "qa_result": None,
        "retry_count": 0,
        "final_response": None,
    }

    try:

        result = graph.invoke(
            initial_state,
            config=config,
        )

        interrupt_value = _extract_interrupt(
            result
        )

        if interrupt_value is not None:
            return _build_approval_response(
                thread_id=thread_id,
                interrupt_value=interrupt_value,
            )

        return _build_completed_response(
            thread_id=thread_id,
            result=result,
        )

    except HTTPException:
        raise

    except Exception as exc:

        print(
            "Support workflow failed:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Support workflow could not be completed.",
        ) from exc


# ---------------------------------------------------------
# Get workflow status
# ---------------------------------------------------------

@app.get(
    "/support/request/{thread_id}",
    response_model=WorkflowStatusResponse,
)
def get_support_request_status(
    thread_id: str,
):
    """
    Retrieve the current externally visible state of a
    support workflow.
    """

    config = _make_config(
        thread_id
    )

    try:

        snapshot = graph.get_state(
            config
        )

    except Exception as exc:

        print(
            "Workflow state lookup failed:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Workflow state could not be retrieved.",
        ) from exc

    if snapshot is None or not snapshot.values:

        raise HTTPException(
            status_code=404,
            detail="Support request not found.",
        )

    interrupt_value = _get_pending_interrupt(
        config
    )

    return _build_status_response(
        thread_id=thread_id,
        state_values=snapshot.values,
        interrupt_value=interrupt_value,
    )


# ---------------------------------------------------------
# Approve / reject
# ---------------------------------------------------------

@app.post(
    "/support/request/{thread_id}/approval",
    response_model=SupportRequestResponse,
)
def submit_approval(
    thread_id: str,
    request: ApprovalRequest,
):
    """
    Resume a paused LangGraph workflow with a human
    approval decision.
    """

    config = _make_config(
        thread_id
    )

    try:

        snapshot = graph.get_state(
            config
        )

    except Exception as exc:

        print(
            "Workflow state lookup failed:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Workflow state could not be retrieved.",
        ) from exc

    if snapshot is None or not snapshot.values:

        raise HTTPException(
            status_code=404,
            detail="Support request not found.",
        )

    pending_interrupt = _get_pending_interrupt(
        config
    )

    if pending_interrupt is None:

        raise HTTPException(
            status_code=409,
            detail=(
                "This support request is not currently "
                "waiting for human approval."
            ),
        )

    try:

        result = graph.invoke(
            Command(
                resume=request.decision
            ),
            config=config,
        )

        interrupt_value = _extract_interrupt(
            result
        )

        if interrupt_value is not None:
            return _build_approval_response(
                thread_id=thread_id,
                interrupt_value=interrupt_value,
            )

        return _build_completed_response(
            thread_id=thread_id,
            result=result,
        )

    except HTTPException:
        raise

    except Exception as exc:

        print(
            "Approval continuation failed:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Support workflow could not be resumed.",
        ) from exc