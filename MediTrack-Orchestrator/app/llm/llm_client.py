from langchain_core.language_models import BaseChatModel

from app.config.settings import settings


def build_llm() -> BaseChatModel:
    """Builds the orchestration LLM, chosen by LLM_PROVIDER in .env.

    Low temperature and a bounded max_tokens keep this model focused on
    reasoning / tool selection rather than creative writing, regardless of
    provider.
    """
    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
            num_predict=settings.llm_max_tokens,
        )

    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq

        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq.")

        return ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: '{settings.llm_provider}' (expected 'groq' or 'ollama').")
