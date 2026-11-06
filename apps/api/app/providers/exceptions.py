# app/providers/exceptions.py
class LLMProviderError(Exception):
    """Base exception for LLM provider failures."""
    pass


class LLMAuthenticationError(LLMProviderError):
    """Raised when provider credentials (API key) are invalid or missing."""
    pass


class LLMConnectionError(LLMProviderError):
    """Raised when provider service/daemon cannot be reached."""
    pass
