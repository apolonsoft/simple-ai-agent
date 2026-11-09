# app/tests/test_rate_limiter.py
from unittest.mock import patch

import httpx
import pytest
from fastapi import Depends, FastAPI, Request, status
from httpx import ASGITransport

from app.core.rate_limiter import RateLimiter
from app.core.security import create_access_token


class InMemoryRedis:
    """Mock Redis client tracking ZSET scores in-memory for deterministic rate limit testing."""

    def __init__(self):
        self.zsets = {}

    async def aclose(self):
        pass

    def client(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def pipeline(self, transaction=True):
        return InMemoryPipeline(self)


class InMemoryPipeline:
    def __init__(self, redis: InMemoryRedis):
        self.redis = redis
        self.operations = []

    def zremrangebyscore(self, key, min_val, max_val):
        self.operations.append(("zremrangebyscore", key, min_val, max_val))
        return self

    def zcard(self, key):
        self.operations.append(("zcard", key))
        return self

    def zrange(self, key, start, stop, withscores=False):
        self.operations.append(("zrange", key, start, stop, withscores))
        return self

    def zadd(self, key, mapping):
        self.operations.append(("zadd", key, mapping))
        return self

    def expire(self, key, seconds):
        self.operations.append(("expire", key, seconds))
        return self

    async def execute(self):
        results: list = []
        for op in self.operations:
            name = op[0]
            if name == "zremrangebyscore":
                _, key, min_val, max_val = op
                items = self.redis.zsets.setdefault(key, {})
                to_del = [m for m, s in items.items() if min_val <= s <= max_val]
                for m in to_del:
                    del items[m]
                results.append(len(to_del))
            elif name == "zcard":
                _, key = op
                results.append(len(self.redis.zsets.get(key, {})))
            elif name == "zrange":
                _, key, start, stop, withscores = op
                items = sorted(
                    self.redis.zsets.get(key, {}).items(), key=lambda x: x[1]
                )
                sliced = items[start : stop + 1 if stop != -1 else None]
                results.append(sliced if withscores else [m for m, _ in sliced])
            elif name == "zadd":
                _, key, mapping = op
                items = self.redis.zsets.setdefault(key, {})
                items.update(mapping)
                results.append(len(mapping))
            elif name == "expire":
                results.append(True)
        return results


@pytest.fixture
def fake_redis():
    return InMemoryRedis()


@pytest.fixture
def test_app(fake_redis):
    app = FastAPI()
    limiter = RateLimiter(max_requests=3, window_seconds=60, scope="test")

    @app.get("/limited", dependencies=[Depends(limiter)])
    async def limited_endpoint():
        return {"message": "ok"}

    return app


@pytest.mark.asyncio
async def test_rate_limiter_allows_up_to_limit(test_app, fake_redis):
    with patch("app.core.rate_limiter.get_redis_client", return_value=fake_redis):
        transport = ASGITransport(app=test_app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            for _ in range(3):
                res = await client.get("/limited")
                assert res.status_code == status.HTTP_200_OK
                assert res.json() == {"message": "ok"}


@pytest.mark.asyncio
async def test_rate_limiter_blocks_excess_requests(test_app, fake_redis):
    with patch("app.core.rate_limiter.get_redis_client", return_value=fake_redis):
        transport = ASGITransport(app=test_app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # 3 requests allowed
            for _ in range(3):
                res = await client.get("/limited")
                assert res.status_code == status.HTTP_200_OK

            # 4th request must be rejected with 429
            blocked_res = await client.get("/limited")
            assert blocked_res.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            assert "Too many requests" in blocked_res.json()["detail"]
            assert "Retry-After" in blocked_res.headers
            assert blocked_res.headers["X-RateLimit-Limit"] == "3"
            assert blocked_res.headers["X-RateLimit-Remaining"] == "0"


@pytest.mark.asyncio
async def test_rate_limiter_identifies_user_via_bearer_token(test_app):
    limiter = RateLimiter(max_requests=5, window_seconds=60, scope="chat")
    token = create_access_token(
        data={"sub": "user-uuid-123", "email": "test@example.com"}
    )

    # Simulated Request with Bearer Token
    request = Request(
        scope={
            "type": "http",
            "headers": [(b"authorization", f"Bearer {token}".encode())],
            "client": ("192.168.1.10", 12345),
        }
    )

    identifier = limiter.get_identifier(request)
    assert identifier == "user:user-uuid-123"


@pytest.mark.asyncio
async def test_rate_limiter_identifies_client_ip_when_unauthenticated(test_app):
    limiter = RateLimiter(max_requests=5, window_seconds=60, scope="public")

    # Request without Authorization header
    request = Request(
        scope={
            "type": "http",
            "headers": [(b"x-forwarded-for", b"203.0.113.195, 70.41.3.18")],
            "client": ("127.0.0.1", 12345),
        }
    )

    identifier = limiter.get_identifier(request)
    assert identifier == "ip:203.0.113.195"


@pytest.mark.asyncio
async def test_rate_limiter_fails_open_on_redis_connection_error(test_app):
    """Resilience test: If Redis is offline, requests must still succeed (fail-open)."""
    with patch(
        "app.core.rate_limiter.get_redis_client",
        side_effect=Exception("Redis connection refused"),
    ):
        transport = ASGITransport(app=test_app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            res = await client.get("/limited")
            assert res.status_code == status.HTTP_200_OK
