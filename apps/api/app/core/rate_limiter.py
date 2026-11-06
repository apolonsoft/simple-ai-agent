# app/core/rate_limiter.py
import time
import uuid
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
import redis.asyncio as aioredis
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
        otherwise falls back to Client IP (respecting X-Forwarded-For).
        """
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                return f"user:{payload['sub']}"

        # Unauthenticated: use IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "127.0.0.1"

        return f"ip:{client_ip}"

    async def __call__(self, request: Request) -> None:
        identifier = self.get_identifier(request)
        redis_key = f"rate_limit:{self.scope}:{identifier}"
        now = time.time()
        window_start = now - self.window_seconds

        try:
            redis: aioredis.Redis = await get_redis_client()
            async with redis.client() as conn:
                # Use pipeline for atomic sliding window evaluation
                pipeline = conn.pipeline(transaction=True)
                # 1. Remove timestamps outside the sliding window
                pipeline.zremrangebyscore(redis_key, 0, window_start)
                # 2. Count requests remaining in the current window
                pipeline.zcard(redis_key)
                # 3. Fetch the oldest record to calculate exact Retry-After
                pipeline.zrange(redis_key, 0, 0, withscores=True)
                results = await pipeline.execute()

                current_count = results[1]
                oldest_entry = results[2]

                if current_count >= self.max_requests:
                    # Calculate retry delay based on the oldest request in the window
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

                # Add current request with a unique member and expire key
                member_id = f"{now}:{uuid.uuid4().hex[:8]}"
                add_pipeline = conn.pipeline(transaction=True)
                add_pipeline.zadd(redis_key, {member_id: now})
                add_pipeline.expire(redis_key, self.window_seconds + 5)
                await add_pipeline.execute()

        except HTTPException:
            # Re-raise rate limit exceptions
            raise
        except Exception as e:
            # Graceful degradation (fail-open): cache failures should not take down the entire API
            logger.error(f"Redis rate limiter error (failing open): {e}")
            return
