# app/core/rate_limiter.py
import logging
import time
import uuid

import redis.asyncio as aioredis
from fastapi import HTTPException, Request, status

from app.core.redis import get_redis_client
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Distributed Sliding Window Rate Limiter powered by Redis.
    Uses Redis Sorted Sets (ZSET) to track requests with microsecond precision,
    preventing edge-burst attacks inherent in fixed-window algorithms.
    """

    def __init__(
        self,
        max_requests: int = 30,
        window_seconds: int = 60,
        scope: str = "default",
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.scope = scope

    def get_identifier(self, request: Request) -> str:
        """
        Extracts client identifier:
        Prefers authenticated user ID if Bearer token is present,
        otherwise falls back to Client IP from request.client.host.
        """
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                return f"user:{payload['sub']}"

        # Unauthenticated: trust only the ASGI peer/proxy-resolved client host
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    async def __call__(self, request: Request) -> None:
        identifier = self.get_identifier(request)
        redis_key = f"rate_limit:{self.scope}:{identifier}"
        now = time.time()
        window_start = now - self.window_seconds

        try:
            redis: aioredis.Redis = await get_redis_client()
            async with redis.client() as conn:
                member_id = f"{now}:{uuid.uuid4().hex[:8]}"
                # Single atomic transaction: prune, add, count, peek oldest, expire
                pipeline = conn.pipeline(transaction=True)
                pipeline.zremrangebyscore(redis_key, 0, window_start)
                pipeline.zadd(redis_key, {member_id: now})
                pipeline.zcard(redis_key)
                pipeline.zrange(redis_key, 0, 0, withscores=True)
                pipeline.expire(redis_key, self.window_seconds + 5)
                _, _, current_count, oldest_entry, _ = await pipeline.execute()

                if current_count > self.max_requests:
                    # Remove rejected member so rejected attempts do not extend the window
                    await conn.zrem(redis_key, member_id)
                    oldest_score = oldest_entry[0][1] if oldest_entry else now
                    reset_time = int(oldest_score + self.window_seconds)
                    retry_after = max(1, reset_time - int(now))

                    logger.warning(
                        f"Rate limit exceeded for {identifier} on scope '{self.scope}'. "
                        f"Limit: {self.max_requests}/{self.window_seconds}s. Retry-After: {retry_after}s"
                    )

                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many requests. Please slow down and try again later.",
                        headers={
                            "Retry-After": str(retry_after),
                            "X-RateLimit-Limit": str(self.max_requests),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(reset_time),
                        },
                    )

        except HTTPException:
            # Re-raise rate limit exceptions
            raise
        except Exception as e:
            # Graceful degradation (fail-open): cache failures should not take down the entire API
            logger.error(f"Redis rate limiter error (failing open): {e}")
            return
