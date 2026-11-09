# app/services/chat_cache_service.py
import json
import logging
import uuid
from typing import Any

import redis.asyncio as aioredis

from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)

DEFAULT_CACHE_TTL = 3600  # 1 hour


class ChatCacheService:
    """
    Distributed Redis cache for active conversation histories.
    Mitigates PostgreSQL read contention and query latency by caching
    the historical turn context during multi-turn LLM inference streams.
    Implements a strict fail-open pattern: any Redis disruption falls back
    to PostgreSQL gracefully without interrupting the user's conversation.
    """

    def __init__(
        self,
        redis_client: aioredis.Redis | None = None,
        ttl: int = DEFAULT_CACHE_TTL,
    ):
        self.redis = redis_client
        self.ttl = ttl

    async def _get_client(self) -> aioredis.Redis | None:
        if self.redis is not None:
            return self.redis
        try:
            return await get_redis_client()
        except Exception as exc:
            logger.warning(f"Could not connect to Redis for chat caching: {exc}")
            return None

    def _key(self, session_id: uuid.UUID | str) -> str:
        return f"chat:history:{str(session_id)}"

    def _serialize_message(self, message: Any) -> dict:
        if isinstance(message, dict):
            return {
                "role": str(message.get("role", "user")),
                "content": str(message.get("content", "")),
                "created_at": str(message.get("created_at", "")),
            }
        return {
            "role": str(getattr(message, "role", "user")),
            "content": str(getattr(message, "content", "")),
            "created_at": str(getattr(message, "created_at", "")),
        }

    async def get_messages(self, session_id: uuid.UUID | str) -> list[dict] | None:
        """
        Retrieves cached conversation turns for the given session.
        Returns None on cache miss or Redis failure (fail-open).
        """
        try:
            client = await self._get_client()
            if client is None:
                return None

            raw_data = await client.get(self._key(session_id))
            if raw_data:
                return json.loads(raw_data)
            return None
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
        Stores complete historical message context into Redis with sliding TTL.
        """
        try:
            client = await self._get_client()
            if client is None:
                return False

            serialized = [self._serialize_message(msg) for msg in messages]
            await client.set(self._key(session_id), json.dumps(serialized), ex=self.ttl)
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
        Appends a newly added message to the existing cached session history.
        Only mutates cache if the session key is already populated.
        """
        try:
            client = await self._get_client()
            if client is None:
                return False

            key = self._key(session_id)
            raw_data = await client.get(key)
            if raw_data is not None:
                current_list = json.loads(raw_data)
                current_list.append(self._serialize_message(message))
                await client.set(key, json.dumps(current_list), ex=self.ttl)
                return True
            return False
        except Exception as exc:
            logger.warning(
                f"Redis append_message failed for session {session_id}: {exc}"
            )
            return False

    async def invalidate(self, session_id: uuid.UUID | str) -> bool:
        """
        Deletes cached conversation history (e.g. upon thread deletion).
        """
        try:
            client = await self._get_client()
            if client is None:
                return False

            await client.delete(self._key(session_id))
            return True
        except Exception as exc:
            logger.warning(f"Redis invalidate failed for session {session_id}: {exc}")
            return False
