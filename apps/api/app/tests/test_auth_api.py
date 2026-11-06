# app/tests/test_auth_api.py
import pytest
from fastapi import status
import httpx


@pytest.mark.asyncio
async def test_register_user_success(client: httpx.AsyncClient):
    payload = {
        "email": "alice@example.com",
        "password": "mypassword123",
        "role": "user"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["role"] == "user"
    assert "hashed_password" not in data
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: httpx.AsyncClient):
    payload = {
        "email": "duplicate@example.com",
        "password": "password123"
    }
    # First registration
    await client.post("/api/v1/auth/register", json=payload)

    # Second registration with same email
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Email is already registered."


@pytest.mark.asyncio
async def test_login_success(client: httpx.AsyncClient):
    # Register user first
    await client.post("/api/v1/auth/register", json={"email": "login@example.com", "password": "password123"})

    # Login with OAuth2 form-data
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "login@example.com", "password": "password123"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: httpx.AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_get_current_user_me(client: httpx.AsyncClient):
    # Register and login
    await client.post("/api/v1/auth/register", json={"email": "profile@example.com", "password": "password123"})
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": "profile@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]

    # Request /me with Bearer token
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == "profile@example.com"


@pytest.mark.asyncio
async def test_get_me_unauthorized_without_token(client: httpx.AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_role_authorization_admin_allowed_and_regular_user_forbidden(client: httpx.AsyncClient):
    # 1. Register regular user
    await client.post("/api/v1/auth/register", json={"email": "regular@example.com", "password": "password", "role": "user"})
    user_login = await client.post("/api/v1/auth/login", data={"username": "regular@example.com", "password": "password"})
    user_token = user_login.json()["access_token"]

    # Regular user attempts to access admin endpoint -> 403 Forbidden
    forbidden_res = await client.get("/api/v1/auth/admin-only", headers={"Authorization": f"Bearer {user_token}"})
    assert forbidden_res.status_code == status.HTTP_403_FORBIDDEN

    # 2. Register admin user
    await client.post("/api/v1/auth/register", json={"email": "boss@example.com", "password": "password", "role": "admin"})
    admin_login = await client.post("/api/v1/auth/login", data={"username": "boss@example.com", "password": "password"})
    admin_token = admin_login.json()["access_token"]

    # Admin user accesses admin endpoint -> 200 OK
    allowed_res = await client.get("/api/v1/auth/admin-only", headers={"Authorization": f"Bearer {admin_token}"})
    assert allowed_res.status_code == status.HTTP_200_OK
    assert "Welcome Admin boss@example.com" in allowed_res.json()["message"]
