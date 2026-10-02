from typing import Any

from pydantic import BaseModel, Field

from app.services.llm import get_llm
from app.tools.support_tools import (
    get_customer,
    search_orders,
    get_order,
    get_payment,
)


class InvestigationResult(BaseModel):
    summary: str = Field(
        description="Concise summary of the verified investigation."
    )

    customer_found: bool = Field(
        description="Whether the customer was found."
    )

    orders_found: int = Field(
        description="Number of orders found for the customer."
    )

    relevant_order_id: int | None = Field(
        default=None,
        description="Most relevant order ID identified during investigation."
    )

    payment_status: str | None = Field(
        default=None,
        description="Payment status for the relevant order, if available."
    )

    facts: list[str] = Field(
        default_factory=list,
        description="Important verified facts from the investigation."
    )


def investigate(
    user_request: str,
    customer_id: int,
    issue_type: str,
) -> dict[str, Any]:
    """
    Perform a controlled investigation using approved support tools.
    """

    customer_data = get_customer(customer_id)

    orders_data = search_orders(customer_id)

    orders = orders_data.get("orders", [])

    relevant_order_id = None
    order_data = None
    payment_data = None

    if orders:
        relevant_order_id = orders[0]["id"]

        order_data = get_order(relevant_order_id)

        if issue_type == "refund":
            payment_data = get_payment(relevant_order_id)

        elif issue_type == "delivery":
            payment_data = get_payment(relevant_order_id)

    investigation_data = {
        "customer": customer_data,
        "orders": orders_data,
        "relevant_order": order_data,
        "payment": payment_data,
    }

    llm = get_llm()

    structured_llm = llm.with_structured_output(
        InvestigationResult
    )

    prompt = f"""
You are a customer support investigation agent.

Your job is to summarize ONLY the verified information
returned by the support tools.

Do not invent customer information.
Do not invent order information.
Do not invent payment information.
Do not make assumptions that are not supported by the data.

Customer request:
{user_request}

Issue type:
{issue_type}

Verified tool results:
{investigation_data}

Create a concise investigation summary.

Important rules:

1. Use only the verified tool results.
2. If information is missing, say that it is unavailable.
3. Identify the most relevant order when one is available.
4. For refund requests, include payment status when available.
5. For delivery requests, include order status and delivery date
   when available.
6. Do not decide whether a refund should be approved.
   That decision belongs to a later resolution stage.
"""

    result = structured_llm.invoke(prompt)

    return result.model_dump()