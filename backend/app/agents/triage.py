from pydantic import BaseModel, Field
from typing import Literal


class TriageResult(BaseModel):
    issue_type: Literal[
        "refund",
        "delivery",
        "general",
    ] = Field(
        description="The category of the customer's support request."
    )