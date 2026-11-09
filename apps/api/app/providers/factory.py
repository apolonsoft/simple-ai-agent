# app/providers/factory.py

from app.core.config import settings
from app.providers.base import BaseLLMProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.ollama_provider import OllamaProvider


def get_llm_provider(
    provider_name: str | None = None,
    **kwargs,
) -> BaseLLMProvider:
    """
    Factory pattern returning the configured LLM provider strategy.
    Supports runtime provider selection or environment-default fallthrough.
    """
    provider = (provider_name or settings.LLM_PROVIDER).lower().strip()

    if provider == "gemini":
        return GeminiProvider(**kwargs)
    elif provider == "ollama":
        return OllamaProvider(**kwargs)
    else:
        raise ValueError(
            f"Unsupported LLM provider '{provider}'. Must be 'gemini' or 'ollama'."
        )
