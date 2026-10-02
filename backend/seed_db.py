from datetime import datetime, timedelta

from app.database import Base, SessionLocal, engine
from app.models import Customer, Order, Payment, Ticket, Refund


def seed_database():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        if db.query(Customer).count() > 0:
            print("Database already contains data.")
            return

        customers = [
            Customer(
                name="Arun Kumar",
                email="arun@example.com",
            ),
            Customer(
                name="Priya Sharma",
                email="priya@example.com",
            ),
            Customer(
                name="Rahul Menon",
                email="rahul@example.com",
            ),
        ]

        db.add_all(customers)
        db.flush()

        now = datetime.utcnow()

        orders = [
            Order(
                id=1001,
                customer_id=customers[0].id,
                status="delivered",
                amount=2499.00,
                order_date=now - timedelta(days=10),
                delivery_date=now - timedelta(days=5),
            ),
            Order(
                id=1002,
                customer_id=customers[0].id,
                status="shipped",
                amount=1599.00,
                order_date=now - timedelta(days=4),
                delivery_date=None,
            ),
            Order(
                id=1003,
                customer_id=customers[1].id,
                status="cancelled",
                amount=899.00,
                order_date=now - timedelta(days=7),
                delivery_date=None,
            ),
            Order(
                id=1004,
                customer_id=customers[2].id,
                status="delivered",
                amount=4999.00,
                order_date=now - timedelta(days=15),
                delivery_date=now - timedelta(days=10),
            ),
        ]

        db.add_all(orders)
        db.flush()

        payments = [
            Payment(
                order_id=1001,
                amount=2499.00,
                status="completed",
                payment_method="UPI",
            ),
            Payment(
                order_id=1002,
                amount=1599.00,
                status="completed",
                payment_method="Credit Card",
            ),
            Payment(
                order_id=1003,
                amount=899.00,
                status="refunded",
                payment_method="Debit Card",
            ),
            Payment(
                order_id=1004,
                amount=4999.00,
                status="completed",
                payment_method="UPI",
            ),
        ]

        tickets = [
            Ticket(
                customer_id=customers[0].id,
                issue_type="delivery_delay",
                status="open",
                description="Order 1002 has not been delivered yet.",
            ),
            Ticket(
                customer_id=customers[1].id,
                issue_type="refund",
                status="closed",
                description="Customer requested a refund for cancelled order 1003.",
            ),
        ]

        refunds = [
            Refund(
                order_id=1003,
                amount=899.00,
                reason="Order cancelled",
                status="completed",
            )
        ]

        db.add_all(payments)
        db.add_all(tickets)
        db.add_all(refunds)

        db.commit()

        print("Synthetic data seeded successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()