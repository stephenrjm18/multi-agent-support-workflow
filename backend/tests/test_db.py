from app.database import SessionLocal
from app.models import Customer, Order, Payment, Ticket, Refund


db = SessionLocal()

try:
    print("Customers:", db.query(Customer).count())
    print("Orders:", db.query(Order).count())
    print("Payments:", db.query(Payment).count())
    print("Tickets:", db.query(Ticket).count())
    print("Refunds:", db.query(Refund).count())

    customer = (
        db.query(Customer)
        .filter(Customer.email == "arun@example.com")
        .first()
    )

    print("\nCustomer:")
    print(customer.name, customer.email)

    orders = (
        db.query(Order)
        .filter(Order.customer_id == customer.id)
        .all()
    )

    print("\nOrders:")
    for order in orders:
        print(
            order.id,
            order.status,
            order.amount,
        )

finally:
    db.close()