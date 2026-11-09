# app/providers/ollama_provider.py
import json
import logging
from collections.abc import AsyncGenerator

import httpx

from app.core.config import settings
from app.providers.base import BaseLLMProvider
from app.providers.exceptions import (
    LLMConnectionError,
    LLMProviderError,
)
from app.schemas.llm import LLMMessage

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Local Ollama LLM Provider adapter using NDJSON HTTP streaming.
    Communicates with local Ollama daemon (e.g. Docker container or local binary).
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    @property
    def provider_name(self) -> str:
        return "ollama"

    def _format_payload(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int | None,
    ) -> dict:
        formatted_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]
        options = {"temperature": temperature}
        if max_tokens:
            options["num_predict"] = max_tokens

        return {
            "model": self.model,
            "messages": formatted_messages,
            "stream": True,
            "options": options,
        }

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/api/chat"
        payload = self._format_payload(messages, temperature, max_tokens)

        timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code == 404:
                        raise LLMProviderError(
                            f"Ollama model '{self.model}' not found. Run `ollama pull {self.model}`."
                        )
                    elif response.status_code != 200:
                        body = await response.aread()
                        raise LLMProviderError(
                            f"Ollama error (HTTP {response.status_code}): {body.decode()}"
                        )

                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            data = json.loads(line)
                            chunk = data.get("message", {}).get("content", "")
                            if chunk:
                                yield chunk
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                raise LLMConnectionError(
                    f"Could not connect to Ollama daemon at {self.base_url}. Ensure Ollama container is running."
                ) from exc

    async def health_check(self) -> bool:
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url)
                return res.status_code == 200
        except Exception:
            return False
