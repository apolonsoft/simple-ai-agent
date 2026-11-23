# app/core/redis.py
import logging

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_pool: aioredis.BlockingConnectionPool | None = None


def get_redis_pool() -> aioredis.BlockingConnectionPool:
    """Singleton blocking connection pool for Redis with bounded timeouts."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.BlockingConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            timeout=settings.REDIS_POOL_TIMEOUT,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.REDIS_SOCKET_TIMEOUT,
            health_check_interval=30,
            decode_responses=True,
        )
    return _redis_pool


async def get_redis_client() -> aioredis.Redis:
    """Returns an active Redis client using the connection pool."""
    return aioredis.Redis(connection_pool=get_redis_pool())


async def close_redis_pool() -> None:
    """Closes all connections in the Redis pool cleanly on shutdown."""
    global _redis_pool
    if _redis_pool is not None:
        try:
            await _redis_pool.disconnect()
            logger.info("Redis connection pool disconnected successfully.")
        except Exception as e:
            logger.error(f"Error disconnecting Redis connection pool: {e}")
        finally:
            _redis_pool = None
