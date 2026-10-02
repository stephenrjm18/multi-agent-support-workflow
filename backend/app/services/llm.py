import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv()


def get_llm():
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "ollama":
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b "),
            temperature=0,
        )

    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when LLM_PROVIDER=gemini"
            )

        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL"),
            temperature=0,
            google_api_key=api_key,
        )

    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is required when LLM_PROVIDER=groq"
            )

        return ChatGroq(
            model=os.getenv("GROQ_MODEL"),
            temperature=0,
            groq_api_key=api_key,
        )

    raise ValueError(
        f"Unsupported LLM_PROVIDER: {provider}"
    )