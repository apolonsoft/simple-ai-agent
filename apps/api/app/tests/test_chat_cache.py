# app/tests/test_chat_cache.py
import asyncio
import uuid
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.user import UserModel
from app.providers.base import BaseLLMProvider
from app.services.chat_cache_service import ChatCacheService
from app.services.chat_service import ChatService
from app.services.chat_stream_service import ChatStreamService


class InMemoryCachePipeline:
    def __init__(self, redis: "InMemorySimpleRedis"):
        self.redis = redis
        self.ops: list[tuple[Any, ...]] = []

    def exists(self, key: str):
        self.ops.append(("exists", key))
        return self

    def lrange(self, key: str, start: int, stop: int):
        self.ops.append(("lrange", key, start, stop))
        return self

    def delete(self, *keys: str):
        self.ops.append(("delete", keys))
        return self

    def rpush(self, key: str, *values: str):
        self.ops.append(("rpush", key, values))
        return self

    def expire(self, key: str, ttl: int):
        self.ops.append(("expire", key, ttl))
        return self

    async def execute(self):
        results = []
        for op in self.ops:
            cmd = op[0]
            if cmd == "exists":
                results.append(1 if op[1] in self.redis.lists else 0)
            elif cmd == "lrange":
                _, key, start, stop = op
                items = self.redis.lists.get(key, [])
                end = None if stop == -1 else stop + 1
                results.append(list(items[start:end]))
            elif cmd == "delete":
                removed = sum(
                    1 for k in op[1] if self.redis.lists.pop(k, None) is not None
                )
                results.append(removed)
            elif cmd == "rpush":
                _, key, values = op
                lst = self.redis.lists.setdefault(key, [])
                lst.extend(values)
                results.append(len(lst))
            elif cmd == "expire":
                results.append(True)
        return results


class InMemorySimpleRedis:
    """Mock Redis client supporting list, pipeline, and Lua append for ChatCacheService."""

    def __init__(self):
        self.lists: dict[str, list[str]] = {}

    def pipeline(self, transaction: bool = True):
        return InMemoryCachePipeline(self)

    def register_script(self, script: str):
        async def _run(keys: list[str], args: list[str]) -> int:
            key = keys[0]
            if key not in self.lists:
                return 0
            payload, window_str, _ttl = args
            window = int(window_str)
            self.lists[key].append(payload)
            if window > 0:
                self.lists[key] = self.lists[key][-window:]
            return 1

        return _run

    async def delete(self, *keys: str):
        return sum(1 for k in keys if self.lists.pop(k, None) is not None)


class MockLLMProvider(BaseLLMProvider):
    def __init__(self, token="Cached response"):
        self.token = token
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
        yield self.token

    async def health_check(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_chat_cache_set_and_get():
    mock_redis = InMemorySimpleRedis()
    cache_service = ChatCacheService(redis_client=cast(Any, mock_redis), ttl=300)
    session_id = uuid.uuid4()

    # 1. Cache miss initially
    assert await cache_service.get_messages(session_id) is None

    # 2. Set messages
    messages = [
        {
            "role": "user",
            "content": "What is Redis?",
            "created_at": "2026-11-08T10:00:00",
        },
        {
            "role": "assistant",
            "content": "Redis is an in-memory data store.",
            "created_at": "2026-11-08T10:00:01",
        },
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
    cache_service = ChatCacheService(redis_client=cast(Any, mock_redis))
    session_id = uuid.uuid4()

    # Seed initial turn
    await cache_service.set_messages(
        session_id, [{"role": "user", "content": "Turn 1"}]
    )

    # Append assistant reply
    appended = await cache_service.append_message(
        session_id, {"role": "assistant", "content": "Reply 1"}
    )
    assert appended is True

    cached = await cache_service.get_messages(session_id)
    assert cached is not None
    assert len(cached) == 2
    assert cached[1]["content"] == "Reply 1"


@pytest.mark.asyncio
async def test_chat_cache_append_when_key_does_not_exist():
    mock_redis = InMemorySimpleRedis()
    cache_service = ChatCacheService(redis_client=cast(Any, mock_redis))
    session_id = uuid.uuid4()

    # Appending to non-existent cache returns False without creating partial state
    result = await cache_service.append_message(
        session_id, {"role": "user", "content": "Orphan"}
    )
    assert result is False
    assert await cache_service.get_messages(session_id) is None


@pytest.mark.asyncio
async def test_chat_cache_invalidate():
    mock_redis = InMemorySimpleRedis()
    cache_service = ChatCacheService(redis_client=cast(Any, mock_redis))
    session_id = uuid.uuid4()

    await cache_service.set_messages(
        session_id, [{"role": "user", "content": "Delete me"}]
    )
    assert await cache_service.get_messages(session_id) is not None

    # Invalidate cache
    assert await cache_service.invalidate(session_id) is True
    assert await cache_service.get_messages(session_id) is None


@pytest.mark.asyncio
async def test_chat_cache_fail_open_on_redis_error():
    broken_redis = MagicMock()
    broken_redis.pipeline.side_effect = Exception("Redis node down")
    broken_redis.register_script.side_effect = Exception("Redis node down")
    broken_redis.delete = AsyncMock(side_effect=Exception("Redis node down"))

    cache_service = ChatCacheService(redis_client=broken_redis)
    session_id = uuid.uuid4()

    # Should not raise exceptions; returns None/False
    assert await cache_service.get_messages(session_id) is None
    assert (
        await cache_service.set_messages(
            session_id, [{"role": "user", "content": "Test"}]
        )
        is False
    )
    assert (
        await cache_service.append_message(
            session_id, {"role": "user", "content": "Test"}
        )
        is False
    )
    assert await cache_service.invalidate(session_id) is False


@pytest.mark.asyncio
async def test_stream_chat_redis_cache_hit_bypasses_postgres_get_messages(db_session):
    """
    Verifies that when conversation history is cached in Redis,
    ChatStreamService injects cached history into context without querying
    chat_service.get_messages from PostgreSQL.
    """
    user = UserModel(
        id=uuid.uuid4(),
        email=f"cache_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="hashed_password",
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    user_id = user.id
    mock_redis = InMemorySimpleRedis()
    cache_service = ChatCacheService(redis_client=cast(Any, mock_redis))

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
    with patch.object(
        ChatService,
        "get_messages",
        side_effect=AssertionError(
            "PostgreSQL get_messages should NOT be called on cache hit"
        ),
    ):
        mock_provider = MockLLMProvider()
        stream_service = ChatStreamService(
            session_factory=lambda: db_session,
            cache_service=cache_service,
        )

        with patch(
            "app.services.chat_stream_service.get_llm_provider",
            return_value=mock_provider,
        ):
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
            assert final_cache is not None
            assert len(final_cache) == 4
            assert final_cache[2]["content"] == "Third turn"
            assert final_cache[3]["content"] == "Cached response"


@pytest.mark.asyncio
async def test_delete_session_invalidates_redis_cache(db_session):
    user = UserModel(
        id=uuid.uuid4(),
        email=f"cache_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="hashed_password",
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    user_id = user.id
    mock_redis = InMemorySimpleRedis()
    cache_service = ChatCacheService(redis_client=cast(Any, mock_redis))

    chat_service = ChatService(db_session, cache_service=cache_service)
    session = await chat_service.create_session(user_id=user_id, title="To Delete")

    # Populate cache
    await cache_service.set_messages(
        session.id, [{"role": "user", "content": "Ephemeral"}]
    )
    assert await cache_service.get_messages(session.id) is not None

    # Delete session
    deleted = await chat_service.delete_session(session.id, user_id)
    assert deleted is True

    # Cache must be invalidated
    assert await cache_service.get_messages(session.id) is None


@pytest.mark.asyncio
async def test_chat_cache_concurrent_append_preserves_all_messages():
    mock_redis = InMemorySimpleRedis()
    cache_service = ChatCacheService(redis_client=cast(Any, mock_redis), window=30)
    session_id = uuid.uuid4()

    await cache_service.set_messages(session_id, [{"role": "user", "content": "seed"}])
    results = await asyncio.gather(
        *[
            cache_service.append_message(
                session_id, {"role": "user", "content": f"msg-{i}"}
            )
            for i in range(20)
        ]
    )
    assert all(results)

    cached = await cache_service.get_messages(session_id)
    assert cached is not None
    assert len(cached) == 21


@pytest.mark.asyncio
async def test_chat_cache_trims_to_window_size():
    mock_redis = InMemorySimpleRedis()
    cache_service = ChatCacheService(redis_client=cast(Any, mock_redis), window=10)
    session_id = uuid.uuid4()

    messages = [{"role": "user", "content": f"m-{i}"} for i in range(50)]
    assert await cache_service.set_messages(session_id, messages) is True

    cached = await cache_service.get_messages(session_id)
    assert cached is not None
    assert len(cached) == 10
    assert cached[0]["content"] == "m-40"
    assert cached[-1]["content"] == "m-49"
