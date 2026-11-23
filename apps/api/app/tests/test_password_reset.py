# app/tests/test_password_reset.py
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import status
from sqlalchemy import select

from app.models.password_reset import PasswordResetModel
from app.tests.test_rate_limiter import InMemoryRedis


@pytest.mark.asyncio
async def test_forgot_password_success_sends_email(client: httpx.AsyncClient):
    # Register user first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "forgot@example.com", "password": "OriginalPassword123!"},
    )

    with patch(
        "app.services.email_service.EmailService.send_password_reset_email",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send_email:
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "forgot@example.com"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "password reset link has been sent" in data["message"]

        # Verify email was dispatched with recipient and generated token
        mock_send_email.assert_awaited_once()
        assert mock_send_email.await_args is not None
        recipient_arg, token_arg = mock_send_email.await_args[0]
        assert recipient_arg == "forgot@example.com"
        assert len(token_arg) > 20


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_user_anti_enumeration(
    client: httpx.AsyncClient,
):
    with patch(
        "app.services.email_service.EmailService.send_password_reset_email",
        new_callable=AsyncMock,
    ) as mock_send_email:
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nobody@example.com"},
        )
        # Anti-enumeration: still returns 200 with identical message
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "password reset link has been sent" in data["message"]

        # Ensure no email was sent
        mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_verify_reset_token_valid(client: httpx.AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "verify@example.com", "password": "OriginalPassword123!"},
    )

    token_captured = None
    with patch(
        "app.services.email_service.EmailService.send_password_reset_email",
        new_callable=AsyncMock,
    ) as mock_send_email:
        await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "verify@example.com"},
        )
        assert mock_send_email.await_args is not None
        token_captured = mock_send_email.await_args[0][1]

    # Verify the captured token
    response = await client.get(
        f"/api/v1/auth/verify-reset-token?token={token_captured}"
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["valid"] is True
    assert data["email"] == "verify@example.com"


@pytest.mark.asyncio
async def test_verify_reset_token_invalid(client: httpx.AsyncClient):
    response = await client.get(
        "/api/v1/auth/verify-reset-token?token=invalid_dummy_token"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid or expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verify_reset_token_expired(client: httpx.AsyncClient, db_session):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "expired@example.com", "password": "OriginalPassword123!"},
    )

    token_captured = None
    with patch(
        "app.services.email_service.EmailService.send_password_reset_email",
        new_callable=AsyncMock,
    ) as mock_send_email:
        await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "expired@example.com"},
        )
        assert mock_send_email.await_args is not None
        token_captured = mock_send_email.await_args[0][1]

    # Manually expire the token in the database
    from app.services.auth_service import AuthService

    token_hash = AuthService._hash_token(token_captured)
    stmt = select(PasswordResetModel).where(PasswordResetModel.token_hash == token_hash)
    record = (await db_session.scalars(stmt)).first()
    assert record is not None
    record.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    await db_session.commit()

    # Attempt to verify the expired token
    response = await client.get(
        f"/api/v1/auth/verify-reset-token?token={token_captured}"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid or expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_reset_password_success_and_login_flow(client: httpx.AsyncClient):
    # 1. Register
    await client.post(
        "/api/v1/auth/register",
        json={"email": "resetflow@example.com", "password": "OldPassword123!"},
    )

    # 2. Forgot Password
    token_captured = None
    with patch(
        "app.services.email_service.EmailService.send_password_reset_email",
        new_callable=AsyncMock,
    ) as mock_send_email:
        await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "resetflow@example.com"},
        )
        assert mock_send_email.await_args is not None
        token_captured = mock_send_email.await_args[0][1]

    # 3. Reset Password
    reset_response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token_captured, "new_password": "NewBrandPassword456!"},
    )
    assert reset_response.status_code == status.HTTP_200_OK
    assert "successfully reset" in reset_response.json()["message"]

    # 4. Old password must fail
    old_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "resetflow@example.com", "password": "OldPassword123!"},
    )
    assert old_login.status_code == status.HTTP_401_UNAUTHORIZED

    # 5. New password must succeed
    new_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "resetflow@example.com", "password": "NewBrandPassword456!"},
    )
    assert new_login.status_code == status.HTTP_200_OK
    assert "access_token" in new_login.json()


@pytest.mark.asyncio
async def test_reset_password_token_single_use(client: httpx.AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "singleuse@example.com", "password": "Password123!"},
    )

    token_captured = None
    with patch(
        "app.services.email_service.EmailService.send_password_reset_email",
        new_callable=AsyncMock,
    ) as mock_send_email:
        await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "singleuse@example.com"},
        )
        assert mock_send_email.await_args is not None
        token_captured = mock_send_email.await_args[0][1]

    # First reset succeeds
    first_res = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token_captured, "new_password": "FirstNewPassword!"},
    )
    assert first_res.status_code == status.HTTP_200_OK

    # Second reset with the same token MUST fail (single use)
    second_res = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token_captured, "new_password": "SecondNewPassword!"},
    )
    assert second_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid or expired" in second_res.json()["detail"]


@pytest.mark.asyncio
async def test_forgot_password_rate_limiting(client: httpx.AsyncClient):
    fake_redis = InMemoryRedis()
    with patch("app.core.rate_limiter.get_redis_client", return_value=fake_redis):
        # 5 requests allowed
        for _ in range(5):
            res = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "ratelimit@example.com"},
            )
            assert res.status_code == status.HTTP_200_OK

        # 6th request rejected with 429
        blocked = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "ratelimit@example.com"},
        )
        assert blocked.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Too many requests" in blocked.json()["detail"]


@pytest.mark.asyncio
async def test_reset_password_revokes_jwt_and_invalidates_sibling_reset_tokens(
    client: httpx.AsyncClient,
):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "revoke_reset@example.com", "password": "OldPassword123!"},
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": "revoke_reset@example.com", "password": "OldPassword123!"},
    )
    old_token = login_res.json()["access_token"]
    old_headers = {"Authorization": f"Bearer {old_token}"}

    # Request two reset tokens before using the first one
    reset_tokens: list[str] = []
    with patch(
        "app.services.email_service.EmailService.send_password_reset_email",
        new_callable=AsyncMock,
    ) as mock_send_email:
        await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "revoke_reset@example.com"},
        )
        assert mock_send_email.await_args is not None
        reset_tokens.append(mock_send_email.await_args[0][1])
        await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "revoke_reset@example.com"},
        )
        assert mock_send_email.await_args is not None
        reset_tokens.append(mock_send_email.await_args[0][1])

    # Advance 1 second so iat < tokens_valid_after
    await asyncio.sleep(1.05)

    # Consume the first reset token
    reset_res = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_tokens[0], "new_password": "BrandNewPassword456!"},
    )
    assert reset_res.status_code == status.HTTP_200_OK

    # Pre-reset JWT must now be rejected with 401
    me_res = await client.get("/api/v1/users/me", headers=old_headers)
    assert me_res.status_code == status.HTTP_401_UNAUTHORIZED

    # Sibling reset token must also be invalidated
    sibling_res = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_tokens[1], "new_password": "AnotherPassword789!"},
    )
    assert sibling_res.status_code == status.HTTP_400_BAD_REQUEST
