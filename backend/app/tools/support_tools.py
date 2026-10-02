from typing import Any

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Customer, Order, Payment


def get_customer(customer_id: int) -> dict[str, Any]:
    """
    Retrieve basic customer information.
    """

    db = SessionLocal()

    try:
        customer = db.execute(
            select(Customer).where(Customer.id == customer_id)
        ).scalar_one_or_none()

        if customer is None:
            return {
                "found": False,
                "customer_id": customer_id,
                "message": "Customer not found.",
            }

        return {
            "found": True,
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
            },
        }

    finally:
        db.close()


def search_orders(customer_id: int) -> dict[str, Any]:
    """
    Retrieve all orders belonging to a customer.
    """

    db = SessionLocal()

    try:
        orders = db.execute(
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(Order.order_date.desc())
        ).scalars().all()

        return {
            "customer_id": customer_id,
            "count": len(orders),
            "orders": [
                {
                    "id": order.id,
                    "status": order.status,
                    "amount": float(order.amount),
                    "order_date": str(order.order_date),
                    "delivery_date": (
                        str(order.delivery_date)
                        if order.delivery_date
                        else None
                    ),
                }
                for order in orders
            ],
        }

    finally:
        db.close()


def get_order(order_id: int) -> dict[str, Any]:
    """
    Retrieve details for a specific order.
    """

    db = SessionLocal()

    try:
        order = db.execute(
            select(Order).where(Order.id == order_id)
        ).scalar_one_or_none()

        if order is None:
            return {
                "found": False,
                "order_id": order_id,
                "message": "Order not found.",
            }

        return {
            "found": True,
            "order": {
                "id": order.id,
                "customer_id": order.customer_id,
                "status": order.status,
                "amount": float(order.amount),
                "order_date": str(order.order_date),
                "delivery_date": (
                    str(order.delivery_date)
                    if order.delivery_date
                    else None
                ),
            },
        }

    finally:
        db.close()


def get_payment(order_id: int) -> dict[str, Any]:
    """
    Retrieve payment information for an order.
    """

    db = SessionLocal()

    try:
        payment = db.execute(
            select(Payment)
            .where(Payment.order_id == order_id)
        ).scalar_one_or_none()

        if payment is None:
            return {
                "found": False,
                "order_id": order_id,
                "message": "Payment information not found.",
            }

        return {
            "found": True,
            "payment": {
                "id": payment.id,
                "order_id": payment.order_id,
                "amount": float(payment.amount),
                "status": payment.status,
                "payment_method": payment.payment_method,
            },
        }

    finally:
        db.close()