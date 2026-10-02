from app.graph.workflow import build_graph


graph = build_graph()


test_cases = [
    {
        "request": "I want a refund for my order",
        "customer_id": 1,
    },
    {
        "request": "My delivery is late",
        "customer_id": 1,
    },
    {
        "request": "Can you tell me about my recent order?",
        "customer_id": 1,
    },
    {
        "request": "The product I received was damaged and I want my money back.",
        "customer_id": 1,
    },
    {
        "request": "My package was supposed to arrive yesterday but it hasn't arrived.",
        "customer_id": 1,
    },
]


for test_case in test_cases:

    request = test_case["request"]
    customer_id = test_case["customer_id"]

    initial_state = {
        "user_request": request,
        "customer_id": customer_id,
        "ticket_id": None,
        "issue_type": None,
        "investigation_results": None,
        "resolution_proposal": None,
        "approval_status": None,
        "qa_result": None,
        "retry_count": 0,
        "final_response": None,
    }

    final_state = graph.invoke(initial_state)

    print("\n" + "=" * 70)

    print("User request:")
    print(request)

    print("\nCustomer ID:")
    print(customer_id)

    print("\nIssue type:")
    print(final_state["issue_type"])

    print("\nInvestigation results:")
    print(final_state["investigation_results"])

    print("\nFinal state:")
    print(final_state)