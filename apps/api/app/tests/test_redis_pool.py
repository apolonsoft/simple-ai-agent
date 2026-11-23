# app/tests/test_redis_pool.py
import time
from unittest.mock import patch

import httpx
import pytest
import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, status
from httpx import ASGITransport

import app.core.redis as redis_module
from app.core.config import settings
from app.core.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_redis_pool_uses_blocking_pool_with_timeouts():
    await redis_module.close_redis_pool()
    try:
        pool = redis_module.get_redis_pool()
        assert isinstance(pool, aioredis.BlockingConnectionPool)
        assert pool.connection_kwargs["socket_timeout"] == settings.REDIS_SOCKET_TIMEOUT
        assert (
            pool.connection_kwargs["socket_connect_timeout"]
            == settings.REDIS_SOCKET_TIMEOUT
        )
        assert pool.connection_kwargs["health_check_interval"] == 30
    finally:
        await redis_module.close_redis_pool()


@pytest.mark.asyncio
async def test_rate_limiter_fails_open_quickly_on_hung_redis():
    await redis_module.close_redis_pool()
    app = FastAPI()
    limiter = RateLimiter(max_requests=5, window_seconds=60, scope="hung-test")

    @app.get("/ping", dependencies=[Depends(limiter)])
    async def ping():
        return {"ok": True}

    try:
        with patch.object(settings, "REDIS_URL", "redis://10.255.255.1:6379/0"):
            transport = ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                start = time.monotonic()
                res = await client.get("/ping")
                elapsed = time.monotonic() - start

        assert res.status_code == status.HTTP_200_OK
        assert elapsed < 1.5
    finally:
        await redis_module.close_redis_pool()
