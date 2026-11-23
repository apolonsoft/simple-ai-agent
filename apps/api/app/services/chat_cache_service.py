# app/services/chat_cache_service.py
import contextlib
import json
import logging
import uuid
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)

DEFAULT_CACHE_TTL = 3600  # 1 hour

_APPEND_LUA = """
if redis.call('EXISTS', KEYS[1]) == 1 then
  redis.call('RPUSH', KEYS[1], ARGV[1])
  redis.call('LTRIM', KEYS[1], -tonumber(ARGV[2]), -1)
  redis.call('EXPIRE', KEYS[1], ARGV[3])
  return 1
end
return 0
"""


class ChatCacheService:
    """
    Distributed Redis list cache for active conversation histories.
    Mitigates PostgreSQL read contention and query latency by caching
    the bounded historical turn context during multi-turn LLM inference streams.
    Implements a strict fail-open pattern: any Redis disruption falls back
    to PostgreSQL gracefully without interrupting the user's conversation.
    Stampede locking is unnecessary because each cache key is scoped to a
    single user's session.
    """

    def __init__(
        self,
        redis_client: aioredis.Redis | None = None,
        ttl: int = DEFAULT_CACHE_TTL,
        window: int | None = None,
    ):
        self.redis = redis_client
        self.ttl = ttl
        self.window = window if window is not None else settings.CHAT_MEMORY_WINDOW_SIZE
        self._append_script: Any = None
        self._script_client: aioredis.Redis | None = None

    async def _get_client(self) -> aioredis.Redis | None:
        if self.redis is not None:
            return self.redis
        try:
            return await get_redis_client()
        except Exception as exc:
            logger.warning(f"Could not connect to Redis for chat caching: {exc}")
            return None

    def _key(self, session_id: uuid.UUID | str) -> str:
        return f"chat:history:v2:{str(session_id)}"

    def _legacy_key(self, session_id: uuid.UUID | str) -> str:
        return f"chat:history:{str(session_id)}"

    def _serialize_message(self, message: Any) -> dict:
        if isinstance(message, dict):
            res = {
                "role": str(message.get("role", "user")),
                "content": str(message.get("content", "")),
                "created_at": str(message.get("created_at", "")),
            }
            if "tool_calls" in message and message["tool_calls"] is not None:
                res["tool_calls"] = message["tool_calls"]
            return res

        tool_calls = getattr(message, "tool_calls", None)
        if isinstance(tool_calls, str):
            with contextlib.suppress(Exception):
                tool_calls = json.loads(tool_calls)

        res = {
            "role": str(getattr(message, "role", "user")),
            "content": str(getattr(message, "content", "")),
            "created_at": str(getattr(message, "created_at", "")),
        }
        if tool_calls is not None:
            res["tool_calls"] = tool_calls
        return res

    async def get_messages(self, session_id: uuid.UUID | str) -> list[dict] | None:
        """
        Retrieves cached conversation turns for the given session.
        Returns None on cache miss or Redis failure (fail-open).
        """
        try:
            client = await self._get_client()
            if client is None:
                return None

            key = self._key(session_id)
            pipe = client.pipeline(transaction=False)
            pipe.exists(key)
            pipe.lrange(key, 0, -1)
            exists, raw_items = await pipe.execute()
            if not exists:
                return None
            return [json.loads(item) for item in raw_items]
        except Exception as exc:
            logger.warning(
                f"Redis get_messages cache miss / error for session {session_id}: {exc}"
            )
            return None

    async def set_messages(
        self,
        session_id: uuid.UUID | str,
        messages: list[Any],
    ) -> bool:
        """
        Stores bounded historical message context into Redis with sliding TTL.
        """
        try:
            client = await self._get_client()
            if client is None:
                return False

            bounded = messages[-self.window :] if self.window > 0 else []
            serialized = [json.dumps(self._serialize_message(msg)) for msg in bounded]
            key = self._key(session_id)
            pipe = client.pipeline(transaction=True)
            pipe.delete(key)
            if serialized:
                pipe.rpush(key, *serialized)
                pipe.expire(key, self.ttl)
            await pipe.execute()
            return True
        except Exception as exc:
            logger.warning(f"Redis set_messages failed for session {session_id}: {exc}")
            return False

    async def append_message(
        self,
        session_id: uuid.UUID | str,
        message: Any,
    ) -> bool:
        """
        Atomically appends a newly added message to the existing cached session
        history and trims it to the configured window. Only mutates cache if
        the session key is already populated.
        """
        try:
            client = await self._get_client()
            if client is None:
                return False

            if self._append_script is None or self._script_client is not client:
                self._append_script = client.register_script(_APPEND_LUA)
                self._script_client = client

            key = self._key(session_id)
            payload = json.dumps(self._serialize_message(message))
            result = await self._append_script(
                keys=[key], args=[payload, str(self.window), str(self.ttl)]
            )
            return bool(result)
        except Exception as exc:
            logger.warning(
                f"Redis append_message failed for session {session_id}: {exc}"
            )
            return False

    async def invalidate(self, session_id: uuid.UUID | str) -> bool:
        """
        Deletes cached conversation history (v2 and legacy keys).
        """
        try:
            client = await self._get_client()
            if client is None:
                return False

            await client.delete(self._key(session_id), self._legacy_key(session_id))
            return True
        except Exception as exc:
            logger.warning(f"Redis invalidate failed for session {session_id}: {exc}")
            return False
