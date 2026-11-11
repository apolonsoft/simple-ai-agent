# app/providers/gemini_provider.py
import json
import logging
from collections.abc import AsyncGenerator

import httpx

from app.core.config import settings
from app.providers.base import BaseLLMProvider
from app.providers.exceptions import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMProviderError,
)
from app.schemas.llm import LLMMessage

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini Cloud LLM Provider adapter using asynchronous HTTP streaming.
    Supports system instructions, role formatting, and SSE token chunking.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _format_payload(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int | None,
        tools: list[dict] | None = None,
    ) -> dict:
        contents = []
        system_instruction = None

        for msg in messages:
            if msg.role == "system":
                system_instruction = {"parts": [{"text": msg.content}]}
            elif msg.role == "user":
                contents.append({"role": "user", "parts": [{"text": msg.content}]})
            elif msg.role == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg.content}]})

        payload: dict = {"contents": contents}

        if system_instruction:
            payload["systemInstruction"] = system_instruction

        generation_config = {"temperature": temperature}
        if max_tokens:
            generation_config["maxOutputTokens"] = max_tokens
        payload["generationConfig"] = generation_config

        if tools:
            gemini_tools = []
            for tool in tools:
                if tool.get("type") == "function" and "function" in tool:
                    fn = tool["function"]
                    gemini_tools.append(
                        {
                            "name": fn["name"],
                            "description": fn.get("description", ""),
                            "parameters": fn.get("parameters", {}),
                        }
                    )
            if gemini_tools:
                payload["tools"] = [{"functionDeclarations": gemini_tools}]

        return payload

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncGenerator[str | dict, None]:
        tools = kwargs.get("tools")
        if not self.api_key or self.api_key.startswith("your_"):
            raise LLMAuthenticationError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in your environment."
            )

        url = f"{self.base_url}/models/{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"
        payload = self._format_payload(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        )

        timeout = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code == 400:
                        body = await response.aread()
                        raise LLMProviderError(
                            f"Gemini API bad request: {body.decode()}"
                        )
                    elif response.status_code in (401, 403):
                        raise LLMAuthenticationError(
                            "Gemini API key is invalid or unauthorized."
                        )
                    elif response.status_code != 200:
                        body = await response.aread()
                        raise LLMProviderError(
                            f"Gemini API error (HTTP {response.status_code}): {body.decode()}"
                        )

                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data:"):
                            continue

                        json_str = line[5:].strip()
                        try:
                            data = json.loads(json_str)
                            candidates = data.get("candidates", [])
                            if not candidates:
                                continue
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for part in parts:
                                text_chunk = part.get("text", "")
                                if text_chunk:
                                    yield text_chunk
                                func_call = part.get("functionCall")
                                if func_call:
                                    yield {
                                        "type": "tool_call",
                                        "name": func_call.get("name"),
                                        "arguments": func_call.get("args", {}),
                                    }
                        except json.JSONDecodeError:
                            continue

            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                raise LLMConnectionError(
                    f"Failed to connect to Gemini API: {exc}"
                ) from exc

    async def health_check(self) -> bool:
        if not self.api_key or self.api_key.startswith("your_"):
            return False
        url = f"{self.base_url}/models/{self.model}?key={self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url)
                return res.status_code == 200
        except Exception:
            return False
