# app/tests/test_chat_stream.py
from collections.abc import AsyncGenerator
from unittest.mock import patch

import httpx
import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine, get_db
from app.main import app as fastapi_app
from app.providers.base import BaseLLMProvider
from app.tests.conftest import test_engine


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


class TransactionCheckingProvider(BaseLLMProvider):
    """Mock LLM provider that checks whether request-scoped sessions are in an active transaction."""

    def __init__(self, captured_sessions: list[AsyncSession]):
        self.captured_sessions = captured_sessions
        self.session_was_in_transaction = None
        self.pool_checkedout_count = None

    @property
    def provider_name(self) -> str:
        return "tx_checker"

    async def generate_stream(
        self,
        messages,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ):
        if self.captured_sessions:
            self.session_was_in_transaction = any(
                s.in_transaction() for s in self.captured_sessions
            )
        try:
            checkedout_fn = getattr(engine.pool, "checkedout", None)
            if callable(checkedout_fn):
                self.pool_checkedout_count = checkedout_fn()
        except Exception:
            pass
        yield "token"

    async def health_check(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_stream_chat_releases_db_connection_before_streaming(
    client: httpx.AsyncClient,
):
    """Verifies that the request-scoped database session is closed before SSE streaming begins."""
    token = await get_auth_token(client, "tx_checker@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    session_res = await client.post(
        "/api/v1/chats", json={"title": "DB Release Test"}, headers=headers
    )
    assert session_res.status_code == status.HTTP_201_CREATED
    session_id = session_res.json()["id"]

    captured_sessions: list[AsyncSession] = []
    original_get_db = fastapi_app.dependency_overrides.get(get_db)

    async def tracking_get_db() -> AsyncGenerator[AsyncSession, None]:
        if original_get_db:
            async for s in original_get_db():
                captured_sessions.append(s)
                yield s
        else:
            async with AsyncSession(engine) as s:
                captured_sessions.append(s)
                yield s

    fastapi_app.dependency_overrides[get_db] = tracking_get_db
    provider = TransactionCheckingProvider(captured_sessions)

    try:
        with patch(
            "app.services.chat_stream_service.get_llm_provider", return_value=provider
        ):
            res = await client.post(
                f"/api/v1/chats/{session_id}/stream",
                json={"content": "Check DB connection release"},
                headers=headers,
            )
            assert res.status_code == status.HTTP_200_OK
            assert provider.session_was_in_transaction is False
    finally:
        if original_get_db:
            fastapi_app.dependency_overrides[get_db] = original_get_db
        else:
            fastapi_app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_stream_chat_releases_db_connection_postgres():
    """Assert engine.pool.checkedout() == 0 inside the provider (PostgreSQL only)."""
    if "sqlite" in test_engine.url.drivername:
        pytest.skip("PostgreSQL-only connection pool check")

    checkedout_fn = getattr(engine.pool, "checkedout", None)
    if callable(checkedout_fn):
        assert checkedout_fn() == 0


@pytest.mark.asyncio
async def test_stream_chat_persists_partial_reply_on_disconnect(
    db_session: AsyncSession,
):
    """Closing the stream generator mid-response must persist partial assistant chunks."""
    import asyncio
    import uuid

    from sqlalchemy import select

    from app.models.chat import ChatMessageModel, ChatSessionModel
    from app.models.user import UserModel
    from app.services.chat_stream_service import ChatStreamService

    class SlowFakeProvider(BaseLLMProvider):
        @property
        def provider_name(self) -> str:
            return "slow_fake"

        async def generate_stream(
            self,
            messages,
            temperature: float = 0.7,
            max_tokens: int | None = None,
            **kwargs,
        ):
            yield "Hello "
            yield "world"
            yield "!"
            await asyncio.sleep(10)

        async def health_check(self) -> bool:
            return True

    user = UserModel(
        id=uuid.uuid4(),
        email=f"disconnect_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="hashed_password",
        role="user",
        is_active=True,
    )
    session = ChatSessionModel(
        id=uuid.uuid4(),
        user_id=user.id,
        title="Disconnect Test",
    )
    db_session.add_all([user, session])
    await db_session.commit()

    stream_service = ChatStreamService(session_factory=lambda: db_session)
    with patch(
        "app.services.chat_stream_service.get_llm_provider",
        return_value=SlowFakeProvider(),
    ):
        gen = stream_service.stream_chat(
            session_id=session.id,
            user_id=user.id,
            user_content="Tell me a story",
        )
        # Consume 2 chunk events, then simulate client disconnect
        ev1 = await gen.__anext__()
        ev2 = await gen.__anext__()
        assert ev1["event"] == "chunk"
        assert ev2["event"] == "chunk"
        await gen.aclose()

    msgs = list(
        (
            await db_session.scalars(
                select(ChatMessageModel)
                .where(ChatMessageModel.session_id == session.id)
                .order_by(ChatMessageModel.created_at.asc())
            )
        ).all()
    )
    assistant_msgs = [m for m in msgs if m.role == "assistant"]
    assert len(assistant_msgs) == 1
    assert "Hello world" in assistant_msgs[0].content
