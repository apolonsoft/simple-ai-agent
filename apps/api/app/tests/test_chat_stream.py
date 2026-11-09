# app/tests/test_chat_stream.py
from unittest.mock import patch

import httpx
import pytest
from fastapi import status

from app.providers.base import BaseLLMProvider


class MockStreamingProvider(BaseLLMProvider):
    """Mock LLM provider yielding controlled tokens and capturing incoming context."""

    def __init__(self, token_chunks=None):
        self.token_chunks = token_chunks or [
            "Hello",
            " world,",
            " this is",
            " streaming!",
        ]
        self.captured_messages = []

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate_stream(
        self,
        messages,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ):
        self.captured_messages.append(messages)
        for chunk in self.token_chunks:
            yield chunk

    async def health_check(self) -> bool:
        return True


async def get_auth_token(
    client: httpx.AsyncClient, email: str = "streamer@example.com"
) -> str:
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "password123"}
    )
    login_res = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": "password123"}
    )
    return login_res.json()["access_token"]


@pytest.mark.asyncio
async def test_stream_chat_response_success(client: httpx.AsyncClient):
    token = await get_auth_token(client, "stream_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a session
    session_res = await client.post(
        "/api/v1/chats", json={"title": "Streaming Test"}, headers=headers
    )
    assert session_res.status_code == status.HTTP_201_CREATED
    session_id = session_res.json()["id"]

    mock_provider = MockStreamingProvider(["Hello", " world!"])

    # 2. Call SSE stream endpoint
    with patch(
        "app.services.chat_stream_service.get_llm_provider", return_value=mock_provider
    ):
        stream_res = await client.post(
            f"/api/v1/chats/{session_id}/stream",
            json={"content": "Hi AI!"},
            headers=headers,
        )

        assert stream_res.status_code == status.HTTP_200_OK
        assert "text/event-stream" in stream_res.headers["content-type"]

        # Parse SSE lines from response body
        text_body = stream_res.text
        assert "event: chunk" in text_body
        assert "Hello" in text_body
        assert "world!" in text_body
        assert "event: done" in text_body

    # 3. Verify messages are persisted in PostgreSQL
    messages_res = await client.get(
        f"/api/v1/chats/{session_id}/messages", headers=headers
    )
    assert messages_res.status_code == status.HTTP_200_OK
    messages = messages_res.json()

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hi AI!"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hello world!"


@pytest.mark.asyncio
async def test_stream_chat_multi_turn_context_memory(client: httpx.AsyncClient):
    """End-to-End Context Memory Test: Verifies LLM receives previous conversation turns."""
    token = await get_auth_token(client, "context_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    session_res = await client.post(
        "/api/v1/chats", json={"title": "Memory Test"}, headers=headers
    )
    session_id = session_res.json()["id"]

    mock_provider = MockStreamingProvider(["I noted ", "your favorite color is cyan."])

    # Turn 1: User says favorite color
    with patch(
        "app.services.chat_stream_service.get_llm_provider", return_value=mock_provider
    ):
        await client.post(
            f"/api/v1/chats/{session_id}/stream",
            json={"content": "My favorite color is cyan."},
            headers=headers,
        )

    # Turn 2: User asks what their favorite color is
    mock_provider_turn2 = MockStreamingProvider(["Your favorite color is cyan!"])
    with patch(
        "app.services.chat_stream_service.get_llm_provider",
        return_value=mock_provider_turn2,
    ):
        await client.post(
            f"/api/v1/chats/{session_id}/stream",
            json={"content": "What is my favorite color?"},
            headers=headers,
        )

        # Inspect the exact context passed to the LLM on Turn 2
        captured = mock_provider_turn2.captured_messages[0]
        # System prompt + Turn 1 User + Turn 1 Assistant + Turn 2 User
        roles = [m.role for m in captured]
        contents = [m.content for m in captured]

        assert roles == ["system", "user", "assistant", "user"]
        assert contents[1] == "My favorite color is cyan."
        assert contents[2] == "I noted your favorite color is cyan."
        assert contents[3] == "What is my favorite color?"


@pytest.mark.asyncio
async def test_stream_unauthorized_and_cross_user_isolation(client: httpx.AsyncClient):
    token_a = await get_auth_token(client, "stream_user_a@example.com")
    token_b = await get_auth_token(client, "stream_user_b@example.com")

    # User A creates session
    res_a = await client.post(
        "/api/v1/chats",
        json={"title": "Private"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    session_a_id = res_a.json()["id"]

    # 1. Unauthenticated request rejected
    no_auth_res = await client.post(
        f"/api/v1/chats/{session_a_id}/stream", json={"content": "hi"}
    )
    assert no_auth_res.status_code == status.HTTP_401_UNAUTHORIZED

    # 2. User B streaming into User A's session rejected with 404
    cross_res = await client.post(
        f"/api/v1/chats/{session_a_id}/stream",
        json={"content": "hacked"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert cross_res.status_code == status.HTTP_404_NOT_FOUND
