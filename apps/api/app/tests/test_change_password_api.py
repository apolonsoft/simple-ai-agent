# app/tests/test_change_password_api.py
import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import status

from app.tests.test_rate_limiter import InMemoryRedis


class AsyncFakeRedis:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = str(value)
        return True

    async def aclose(self):
        pass


async def get_auth_token(client: httpx.AsyncClient, email: str, password: str = "oldpass123") -> str:
    """Helper to register and login a user, returning a valid Bearer token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_change_password_unauthorized(client: httpx.AsyncClient):
    """Calling change-password without Bearer token must fail with 401."""
    res = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "any", "new_password": "newpassword123"},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_change_password_success_and_login_with_new_password(client: httpx.AsyncClient):
    """Valid change-password updates database credentials and allows logging in with new password."""
    token = await get_auth_token(client, "change_pw_user@example.com", "oldpassword123")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "oldpassword123", "new_password": "newpassword123"},
        headers=headers,
    )
    assert res.status_code == status.HTTP_200_OK
    assert "Password changed successfully" in res.json()["message"]

    # Old password must now fail
    old_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "change_pw_user@example.com", "password": "oldpassword123"},
    )
    assert old_login.status_code == status.HTTP_401_UNAUTHORIZED

    # New password must succeed
    new_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "change_pw_user@example.com", "password": "newpassword123"},
    )
    assert new_login.status_code == status.HTTP_200_OK
    assert "access_token" in new_login.json()


@pytest.mark.asyncio
async def test_change_password_revokes_old_session(client: httpx.AsyncClient):
    """Changing password must revoke the active token so subsequent requests fail with 401."""
    fake_redis = AsyncFakeRedis()

    with patch("app.core.dependencies.get_redis_client", new=AsyncMock(return_value=fake_redis)), \
         patch("app.services.auth_service.get_redis_client", new=AsyncMock(return_value=fake_redis)):

        token = await get_auth_token(client, "revoked_pw_user@example.com", "currentpass123")
        headers = {"Authorization": f"Bearer {token}"}

        # Token works initially
        initial_check = await client.get("/api/v1/users/me", headers=headers)
        assert initial_check.status_code == status.HTTP_200_OK

        # Ensure timestamp ticks forward by 1 second
        await asyncio.sleep(1.05)

        # Perform password change
        change_res = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "currentpass123", "new_password": "brandnewpass123"},
            headers=headers,
        )
        assert change_res.status_code == status.HTTP_200_OK

        # Subsequent request with old token must now be rejected (401 Session revoked)
        subsequent_check = await client.get("/api/v1/users/me", headers=headers)
        assert subsequent_check.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Session revoked" in subsequent_check.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_incorrect_current_password(client: httpx.AsyncClient):
    """Wrong current password must return 400 Bad Request."""
    token = await get_auth_token(client, "wrong_pw_user@example.com", "correctpass123")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "incorrectpassword", "new_password": "newpassword123"},
        headers=headers,
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Current password is incorrect" in res.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_same_password_rejected(client: httpx.AsyncClient):
    """Identical new password must be rejected with 400 Bad Request."""
    token = await get_auth_token(client, "same_pw_user@example.com", "mypassword123")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "mypassword123", "new_password": "mypassword123"},
        headers=headers,
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot be the same" in res.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_length_validation(client: httpx.AsyncClient):
    """New password shorter than 6 characters must fail schema validation with 422."""
    token = await get_auth_token(client, "short_pw_user@example.com", "mypassword123")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "mypassword123", "new_password": "123"},
        headers=headers,
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_change_password_rate_limiting(client: httpx.AsyncClient):
    """Exceeding 5 change-password requests within 60 seconds triggers 429 Too Many Requests."""
    token = await get_auth_token(client, "ratelimit_pw_user@example.com", "mypassword123")
    headers = {"Authorization": f"Bearer {token}"}

    fake_redis = InMemoryRedis()
    with patch("app.core.rate_limiter.get_redis_client", return_value=fake_redis):
        # 5 requests allowed
        for _ in range(5):
            res = await client.post(
                "/api/v1/auth/change-password",
                json={"current_password": "wrongpassword", "new_password": "newpassword123"},
                headers=headers,
            )
            assert res.status_code == status.HTTP_400_BAD_REQUEST

        # 6th request triggers 429
        blocked = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "wrongpassword", "new_password": "newpassword123"},
            headers=headers,
        )
        assert blocked.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Too many requests" in blocked.json()["detail"]
