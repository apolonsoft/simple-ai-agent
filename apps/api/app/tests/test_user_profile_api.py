# app/tests/test_user_profile_api.py
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import status


async def get_auth_token(
    client: httpx.AsyncClient, email: str = "profile@example.com"
) -> str:
    """Helper to register and login a user, returning a valid Bearer token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "securepassword123"},
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "securepassword123"},
    )
    return login_res.json()["access_token"]


@pytest.mark.asyncio
async def test_get_profile_unauthorized(client: httpx.AsyncClient):
    """Accessing profile without Bearer token must fail with 401."""
    res = await client.get("/api/v1/users/me")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_profile_success(client: httpx.AsyncClient):
    """Authenticated user retrieves their full profile."""
    token = await get_auth_token(client, "alice_profile@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/users/me", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["email"] == "alice_profile@example.com"
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert data["full_name"] is None
    assert data["avatar_url"] is None
    assert data["bio"] is None
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_update_profile_success(client: httpx.AsyncClient):
    """Authenticated user updates full_name and bio."""
    token = await get_auth_token(client, "bob_profile@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "full_name": "Bob Builder",
        "bio": "Building robust scalable systems.",
    }
    patch_res = await client.patch(
        "/api/v1/users/me", json=update_payload, headers=headers
    )
    assert patch_res.status_code == status.HTTP_200_OK
    data = patch_res.json()
    assert data["full_name"] == "Bob Builder"
    assert data["bio"] == "Building robust scalable systems."

    # Verify retrieval reflects the updated data
    get_res = await client.get("/api/v1/users/me", headers=headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["full_name"] == "Bob Builder"
    assert get_res.json()["bio"] == "Building robust scalable systems."


@pytest.mark.asyncio
async def test_update_profile_validation_length(client: httpx.AsyncClient):
    """Overly long full_name or bio must fail schema validation (422)."""
    token = await get_auth_token(client, "charlie_profile@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # full_name max length is 100
    res = await client.patch(
        "/api/v1/users/me",
        json={"full_name": "A" * 105},
        headers=headers,
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # bio max length is 500
    res = await client.patch(
        "/api/v1/users/me",
        json={"bio": "B" * 505},
        headers=headers,
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_upload_avatar_success(client: httpx.AsyncClient):
    """Valid image upload calls StorageService and updates avatar_url."""
    token = await get_auth_token(client, "david_profile@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    fake_avatar_url = "http://localhost:8333/avatars/custom-uuid.png"
    with patch(
        "app.services.storage_service.StorageService.upload_file",
        new=AsyncMock(return_value=fake_avatar_url),
    ):
        files = {
            "file": ("avatar.png", b"\x89PNG\r\n\x1a\nfakeimagebytes", "image/png"),
        }
        res = await client.post("/api/v1/users/me/avatar", files=files, headers=headers)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["avatar_url"] == fake_avatar_url

    # Check persistence
    get_res = await client.get("/api/v1/users/me", headers=headers)
    assert get_res.json()["avatar_url"] == fake_avatar_url


@pytest.mark.asyncio
async def test_upload_avatar_invalid_type(client: httpx.AsyncClient):
    """Unsupported MIME type must be rejected with 400 Bad Request."""
    token = await get_auth_token(client, "eve_profile@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    files = {
        "file": ("notes.txt", b"just some text", "text/plain"),
    }
    res = await client.post("/api/v1/users/me/avatar", files=files, headers=headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid image format" in res.json()["detail"]


@pytest.mark.asyncio
async def test_upload_avatar_empty_file(client: httpx.AsyncClient):
    """Empty image upload must be rejected with 400 Bad Request."""
    token = await get_auth_token(client, "frank_profile@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    files = {
        "file": ("empty.png", b"", "image/png"),
    }
    res = await client.post("/api/v1/users/me/avatar", files=files, headers=headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "empty" in res.json()["detail"]


@pytest.mark.asyncio
async def test_upload_avatar_oversized(client: httpx.AsyncClient):
    """Image exceeding MAX_AVATAR_SIZE_BYTES must be rejected with 400."""
    token = await get_auth_token(client, "grace_profile@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.core.config.settings.MAX_AVATAR_SIZE_BYTES", 100):
        files = {
            "file": ("large.png", b"x" * 200, "image/png"),
        }
        res = await client.post("/api/v1/users/me/avatar", files=files, headers=headers)
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceeds maximum allowed size" in res.json()["detail"]
