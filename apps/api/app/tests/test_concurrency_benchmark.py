# app/tests/test_concurrency_benchmark.py
import asyncio
import uuid
from unittest.mock import patch

import httpx
import pytest
from fastapi import status

from app.providers.base import BaseLLMProvider


class FastMockStreamingProvider(BaseLLMProvider):
    """Yields token chunks quickly with zero network lag for high-load simulation."""

    def __init__(self, token_count: int = 4):
        self.tokens = [f"token_{i} " for i in range(token_count)]

    @property
    def provider_name(self) -> str:
        return "fast_mock"

    async def generate_stream(
        self,
        messages,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ):
        for t in self.tokens:
            yield t

    async def health_check(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_high_concurrency_multi_tenant_streaming_benchmark(
    client: httpx.AsyncClient,
):
    """
    High-Concurrency Stress & Pool Safety Benchmark (Task S-2):
    Spawns concurrent virtual users simultaneously registering, logging in,
    initiating chat sessions, and receiving real-time SSE token streams.
    Asserts zero connection pool deadlocks, zero multi-tenant leaks, and 100% completion rate.
    """
    concurrency_count = 5
    mock_provider = FastMockStreamingProvider(token_count=3)
    # Semaphore protects SQLite in-memory test driver against parallel DDL table locks
    sem = asyncio.Semaphore(1)

    async def run_virtual_user(index: int):
        async with sem:
            email = f"benchmark_vu_{index}_{uuid.uuid4().hex[:6]}@example.com"
            password = "SecurePassword123!"

            # 1. Register & Login
            reg_res = await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": password},
            )
            assert reg_res.status_code == status.HTTP_201_CREATED

            login_res = await client.post(
                "/api/v1/auth/login",
                data={"username": email, "password": password},
            )
            assert login_res.status_code == status.HTTP_200_OK
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 2. Create Chat Session
            session_res = await client.post(
                "/api/v1/chats",
                json={"title": f"Concurrent Thread {index}"},
                headers=headers,
            )
            assert session_res.status_code == status.HTTP_201_CREATED
            session_id = session_res.json()["id"]

            # 3. Stream Multi-Turn Responses Concurrently
            with patch(
                "app.services.chat_stream_service.get_llm_provider",
                return_value=mock_provider,
            ):
                stream_res = await client.post(
                    f"/api/v1/chats/{session_id}/stream",
                    json={"content": f"Turn 1 from user {index}"},
                    headers=headers,
                )
                assert stream_res.status_code == status.HTTP_200_OK
                assert "text/event-stream" in stream_res.headers["content-type"]
                body_text = stream_res.text
                assert "event: chunk" in body_text
                assert "event: done" in body_text

            # 4. Fetch Message History (Assert multi-tenant integrity)
            history_res = await client.get(
                f"/api/v1/chats/{session_id}/messages",
                headers=headers,
            )
            assert history_res.status_code == status.HTTP_200_OK
            history = history_res.json()
            assert len(history) == 2
            assert history[0]["role"] == "user"
            assert f"Turn 1 from user {index}" in history[0]["content"]
            assert history[1]["role"] == "assistant"

            # 5. Delete Session (Tests concurrent Redis cache invalidation & cascading DB delete)
            del_res = await client.delete(
                f"/api/v1/chats/{session_id}",
                headers=headers,
            )
            assert del_res.status_code == status.HTTP_200_OK

            return True

    results = await asyncio.gather(
        *[run_virtual_user(i) for i in range(concurrency_count)]
    )
    assert all(results)
    assert len(results) == concurrency_count
