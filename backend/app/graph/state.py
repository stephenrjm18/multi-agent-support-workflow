from typing import TypedDict


# class SupportState(TypedDict):
#     user_request: str
#     issue_type: str
#     response: str

class SupportState(TypedDict):
    user_request: str
    customer_id: int | None
    ticket_id: int | None
    issue_type: str | None
    investigation_results: dict[str, any] | None
    resolution_proposal: dict[str, any] | None
    approval_status: str | None
    qa_result: dict[str, any] | None
    retry_count: int
    final_response: str | None