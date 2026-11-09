# app/tests/test_llm_providers.py
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.providers.exceptions import (
    LLMAuthenticationError,
    LLMConnectionError,
)
from app.providers.factory import get_llm_provider
from app.providers.gemini_provider import GeminiProvider
from app.providers.ollama_provider import OllamaProvider
from app.schemas.llm import LLMMessage


def test_factory_returns_expected_provider():
    gemini = get_llm_provider("gemini")
    assert isinstance(gemini, GeminiProvider)
    assert gemini.provider_name == "gemini"

    ollama = get_llm_provider("ollama")
    assert isinstance(ollama, OllamaProvider)
    assert ollama.provider_name == "ollama"

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_llm_provider("invalid_provider")


# ==============================================================================
# GEMINI PROVIDER TESTS
# ==============================================================================


def test_gemini_format_payload():
    provider = GeminiProvider(api_key="test_key", model="gemini-1.5-flash")
    messages = [
        LLMMessage(role="system", content="You are a helpful assistant."),
        LLMMessage(role="user", content="Hello!"),
        LLMMessage(role="assistant", content="Hi there!"),
        LLMMessage(role="user", content="How are you?"),
    ]
    payload = provider._format_payload(messages, temperature=0.5, max_tokens=100)

    assert "systemInstruction" in payload
    assert (
        payload["systemInstruction"]["parts"][0]["text"]
        == "You are a helpful assistant."
    )

    assert len(payload["contents"]) == 3
    assert payload["contents"][0] == {"role": "user", "parts": [{"text": "Hello!"}]}
    assert payload["contents"][1] == {"role": "model", "parts": [{"text": "Hi there!"}]}
    assert payload["contents"][2] == {
        "role": "user",
        "parts": [{"text": "How are you?"}],
    }

    assert payload["generationConfig"]["temperature"] == 0.5
    assert payload["generationConfig"]["maxOutputTokens"] == 100


@pytest.mark.asyncio
async def test_gemini_missing_api_key_raises_auth_error():
    provider = GeminiProvider(api_key="")
    messages = [LLMMessage(role="user", content="Test")]

    with pytest.raises(
        LLMAuthenticationError, match="Gemini API key is not configured"
    ):
        async for _ in provider.generate_stream(messages):
            pass


@pytest.mark.asyncio
async def test_gemini_stream_yields_tokens():
    provider = GeminiProvider(api_key="valid_key", model="gemini-1.5-flash")
    messages = [LLMMessage(role="user", content="Tell me a joke")]

    # Simulated SSE chunks from Gemini API
    sse_lines = [
        'data: {"candidates": [{"content": {"parts": [{"text": "Why did "}]}}]}',
        'data: {"candidates": [{"content": {"parts": [{"text": "the chicken "}]}}]}',
        'data: {"candidates": [{"content": {"parts": [{"text": "cross the road?"}]}}]}',
    ]

    async def mock_aiter_lines():
        for line in sse_lines:
            yield line

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.aiter_lines = mock_aiter_lines
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_client = MagicMock()
    mock_client.stream = MagicMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        chunks = []
        async for chunk in provider.generate_stream(messages):
            chunks.append(chunk)

        assert chunks == ["Why did ", "the chicken ", "cross the road?"]
        full_text = await provider.generate(messages)
        assert full_text == "Why did the chicken cross the road?"


@pytest.mark.asyncio
async def test_gemini_connection_error():
    provider = GeminiProvider(api_key="valid_key")
    messages = [LLMMessage(role="user", content="Hi")]

    mock_client = MagicMock()
    mock_client.stream = MagicMock(side_effect=httpx.ConnectError("Connection failed"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(LLMConnectionError, match="Failed to connect to Gemini API"):
            async for _ in provider.generate_stream(messages):
                pass


# ==============================================================================
# OLLAMA PROVIDER TESTS
# ==============================================================================


def test_ollama_format_payload():
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")
    messages = [
        LLMMessage(role="system", content="System instruction"),
        LLMMessage(role="user", content="Hello"),
    ]
    payload = provider._format_payload(messages, temperature=0.8, max_tokens=256)

    assert payload["model"] == "llama3.2"
    assert payload["stream"] is True
    assert len(payload["messages"]) == 2
    assert payload["messages"][0] == {"role": "system", "content": "System instruction"}
    assert payload["messages"][1] == {"role": "user", "content": "Hello"}
    assert payload["options"]["temperature"] == 0.8
    assert payload["options"]["num_predict"] == 256


@pytest.mark.asyncio
async def test_ollama_stream_yields_tokens():
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")
    messages = [LLMMessage(role="user", content="Count to two")]

    # Simulated NDJSON chunks from Ollama
    ndjson_lines = [
        json.dumps(
            {"message": {"role": "assistant", "content": "One, "}, "done": False}
        ),
        json.dumps({"message": {"role": "assistant", "content": "two!"}, "done": True}),
    ]

    async def mock_aiter_lines():
        for line in ndjson_lines:
            yield line

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.aiter_lines = mock_aiter_lines
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_client = MagicMock()
    mock_client.stream = MagicMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        chunks = []
        async for chunk in provider.generate_stream(messages):
            chunks.append(chunk)

        assert chunks == ["One, ", "two!"]
        full_text = await provider.generate(messages)
        assert full_text == "One, two!"


@pytest.mark.asyncio
async def test_ollama_connection_error():
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")
    messages = [LLMMessage(role="user", content="Hello")]

    mock_client = MagicMock()
    mock_client.stream = MagicMock(side_effect=httpx.ConnectError("Daemon offline"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(
            LLMConnectionError, match="Could not connect to Ollama daemon"
        ):
            async for _ in provider.generate_stream(messages):
                pass
