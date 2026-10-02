from app.services.llm import get_llm


def main():
    llm = get_llm()

    response = llm.invoke(
        "Explain in one sentence what a customer support ticket is."
    )

    print("\nModel response:")
    print(response.content)


if __name__ == "__main__":
    main()