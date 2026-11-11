# app/providers/base.py
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from app.schemas.llm import LLMMessage


class BaseLLMProvider(ABC):
    """
    Abstract Base Class for pluggable LLM provider adapters.
    Ensures uniform streaming and synchronous generation regardless of whether
    the provider is cloud-based (Gemini) or local (Ollama).
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'gemini', 'ollama')."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncGenerator[str | dict, None]:
        """
        Asynchronously streams completion tokens or tool call events chunk-by-chunk.
        Yields raw text deltas or tool call dictionaries.
        """
        if False:
            yield ""

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> str:
        """
        Convenience method that aggregates streamed chunks into a full response string.
        """
        chunks = []
        async for chunk in self.generate_stream(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            if isinstance(chunk, str):
                chunks.append(chunk)
        return "".join(chunks)

    @abstractmethod
    async def health_check(self) -> bool:
        """Verifies connectivity to the provider engine/API."""
        pass
