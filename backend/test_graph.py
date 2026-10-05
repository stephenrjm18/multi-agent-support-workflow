from langgraph.types import Command

from app.graph.workflow import build_graph


graph = build_graph()


initial_state = {
    "user_request": "I want a refund for my order 1001",
    "customer_id": 1,
    "ticket_id": None,
    "issue_type": None,
    "investigation_results": None,
    "resolution_proposal": None,
    "approval_status": None,
    "qa_result": None,
    "retry_count": 0,
    "final_response": None,
}


config = {
    "configurable": {
        "thread_id": "phase-10-refund-test"
    }
}


print("\nStarting workflow...\n")

result = graph.invoke(
    initial_state,
    config=config,
)


print("=" * 70)
print("WORKFLOW PAUSED")
print("=" * 70)

print("\nCurrent state:")
print(result)


if "__interrupt__" in result:

    interrupt_value = result["__interrupt__"][0].value

    print("\nHuman approval required:")
    print(interrupt_value)


    decision = input(
        "\nEnter decision (approve/reject): "
    ).strip().lower()


    if decision not in {"approve", "reject"}:
        raise ValueError(
            "Invalid decision. Enter only 'approve' or 'reject'."
        )


    print("\nResuming workflow...\n")


    final_state = graph.invoke(
        Command(resume=decision),
        config=config,
    )


    print("=" * 70)
    print("WORKFLOW COMPLETED")
    print("=" * 70)

    print("\nApproval status:")
    print(final_state["approval_status"])

    print("\nFinal state:")
    print(final_state)

else:

    print("\nWorkflow completed without human approval.")
    print("\nFinal state:")
    print(result)