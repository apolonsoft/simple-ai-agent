# app/tests/test_chat_cache.py
import json
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.chat_cache_service import ChatCacheService
from app.services.chat_stream_service import ChatStreamService
from app.services.chat_service import ChatService
from app.models.chat import ChatSessionModel, ChatMessageModel
from app.providers.base import BaseLLMProvider


class InMemorySimpleRedis:
    """Mock Redis client for testing ChatCacheService operations."""
    def __init__(self):
        self.store = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int = None):
        self.store[key] = value
        return True

    async def delete(self, key: str):
        return self.store.pop(key, None) is not None


class MockLLMProvider(BaseLLMProvider):
    def __init__(self, token="Cached response"):
        self.token = token
        self.captured_messages = []

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate_stream(self, messages, **kwargs):
        self.captured_messages.append(messages)
        yield self.token

    async def health_check(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_chat_cache_set_and_get():
    mock_redis = InMemorySimpleRedis()
    cache_service = ChatCacheService(redis_client=mock_redis, ttl=300)
    session_id = uuid.uuid4()

    # 1. Cache miss initially
    assert await cache_service.get_messages(session_id) is None

    # 2. Set messages
    messages = [
        {"role": "user", "content": "What is Redis?", "created_at": "2026-11-08T10:00:00"},
        {"role": "assistant", "content": "Redis is an in-memory data store.", "created_at": "2026-11-08T10:00:01"},
    ]
    assert await cache_service.set_messages(session_id, messages) is True

    # 3. Cache hit
    cached = await cache_service.get_messages(session_id)
    assert cached is not None
    assert len(cached) == 2
    assert cached[0]["role"] == "user"
    assert cached[0]["content"] == "What is Redis?"
    assert cached[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_chat_cache_append_message():
    mock_redis = InMemorySimpleRedis()
    cache_service = ChatCacheService(redis_client=mock_redis)
    session_id = uuid.uuid4()

    # Seed initial turn
    await cache_service.set_messages(
        session_id,
        [{"role": "user", "content": "Turn 1"}]
    )

    # Append assistant reply
    appended = await cache_service.append_message(
        session_id,
        {"role": "assistant", "content": "Reply 1"}
    )
    assert appended is True

    cached = await cache_service.get_messages(session_id)
    assert len(cached) == 2
    assert cached[1]["content"] == "Reply 1"


@pytest.mark.asyncio
async def test_chat_cache_append_when_key_does_not_exist():
    mock_redis = InMemorySimpleRedis()
    cache_service = ChatCacheService(redis_client=mock_redis)
    session_id = uuid.uuid4()

    # Appending to non-existent cache returns False without creating partial state
    result = await cache_service.append_message(session_id, {"role": "user", "content": "Orphan"})
    assert result is False
    assert await cache_service.get_messages(session_id) is None


@pytest.mark.asyncio
async def test_chat_cache_invalidate():
    mock_redis = InMemorySimpleRedis()
    cache_service = ChatCacheService(redis_client=mock_redis)
    session_id = uuid.uuid4()

    await cache_service.set_messages(session_id, [{"role": "user", "content": "Delete me"}])
    assert await cache_service.get_messages(session_id) is not None

    # Invalidate cache
    assert await cache_service.invalidate(session_id) is True
    assert await cache_service.get_messages(session_id) is None


@pytest.mark.asyncio
async def test_chat_cache_fail_open_on_redis_error():
    broken_redis = MagicMock()
    broken_redis.get = AsyncMock(side_effect=Exception("Redis node down"))
    broken_redis.set = AsyncMock(side_effect=Exception("Redis node down"))
    broken_redis.delete = AsyncMock(side_effect=Exception("Redis node down"))

    cache_service = ChatCacheService(redis_client=broken_redis)
    session_id = uuid.uuid4()

    # Should not raise exceptions; returns None/False
    assert await cache_service.get_messages(session_id) is None
    assert await cache_service.set_messages(session_id, [{"role": "user", "content": "Test"}]) is False
    assert await cache_service.append_message(session_id, {"role": "user", "content": "Test"}) is False
    assert await cache_service.invalidate(session_id) is False


@pytest.mark.asyncio
async def test_stream_chat_redis_cache_hit_bypasses_postgres_get_messages(db_session):
    """
    Verifies that when conversation history is cached in Redis,
    ChatStreamService injects cached history into context without querying
    chat_service.get_messages from PostgreSQL.
    """
    user_id = uuid.uuid4()
    mock_redis = InMemorySimpleRedis()
    cache_service = ChatCacheService(redis_client=mock_redis)

    # 1. Create a real session in DB
    chat_service = ChatService(db_session, cache_service=cache_service)
    session = await chat_service.create_session(user_id=user_id, title="Cache Hit Test")

    # 2. Seed Redis cache with 2 prior turns
    cached_turns = [
        {"role": "user", "content": "Pre-cached user turn"},
        {"role": "assistant", "content": "Pre-cached assistant turn"},
    ]
    await cache_service.set_messages(session.id, cached_turns)

    # 3. Mock get_messages on ChatService to fail if called
    with patch.object(ChatService, "get_messages", side_effect=AssertionError("PostgreSQL get_messages should NOT be called on cache hit")):
        mock_provider = MockLLMProvider()
        stream_service = ChatStreamService(
            session_factory=lambda: db_session,
            cache_service=cache_service,
        )

        with patch("app.services.chat_stream_service.get_llm_provider", return_value=mock_provider):
            chunks = []
            async for event in stream_service.stream_chat(
                session_id=session.id,
                user_id=user_id,
                user_content="Third turn",
            ):
                chunks.append(event)

            assert len(chunks) > 0

            # 4. Verify the LLM provider received the pre-cached history
            captured_context = mock_provider.captured_messages[0]
            roles_and_contents = [(msg.role, msg.content) for msg in captured_context]

            assert ("user", "Pre-cached user turn") in roles_and_contents
            assert ("assistant", "Pre-cached assistant turn") in roles_and_contents
            assert ("user", "Third turn") in roles_and_contents

            # 5. Verify the cache was updated with the new user and assistant turns
            final_cache = await cache_service.get_messages(session.id)
            assert len(final_cache) == 4
            assert final_cache[2]["content"] == "Third turn"
            assert final_cache[3]["content"] == "Cached response"


@pytest.mark.asyncio
async def test_delete_session_invalidates_redis_cache(db_session):
    user_id = uuid.uuid4()
    mock_redis = InMemorySimpleRedis()
    cache_service = ChatCacheService(redis_client=mock_redis)

    chat_service = ChatService(db_session, cache_service=cache_service)
    session = await chat_service.create_session(user_id=user_id, title="To Delete")

    # Populate cache
    await cache_service.set_messages(session.id, [{"role": "user", "content": "Ephemeral"}])
    assert await cache_service.get_messages(session.id) is not None

    # Delete session
    deleted = await chat_service.delete_session(session.id, user_id)
    assert deleted is True

    # Cache must be invalidated
    assert await cache_service.get_messages(session.id) is None
