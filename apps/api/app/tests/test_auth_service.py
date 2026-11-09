# app/tests/test_auth_service.py
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_register_and_authenticate_user(db_session: AsyncSession):
    service = AuthService(db=db_session)

    # 1. Register
    user_data = UserCreate(
        email="mentor@example.com", password="securepassword123", role="user"
    )
    user = await service.register_user(user_data)

    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)
    assert user.email == "mentor@example.com"
    assert user.hashed_password != "securepassword123"  # Password must be hashed

    # 2. Authenticate with correct password
    authenticated = await service.authenticate(
        "mentor@example.com", "securepassword123"
    )
    assert authenticated is not None
    assert authenticated.id == user.id

    # 3. Authenticate with wrong password
    invalid_auth = await service.authenticate("mentor@example.com", "wrongpassword")
    assert invalid_auth is None


@pytest.mark.asyncio
async def test_generate_and_decode_token(db_session: AsyncSession):
    service = AuthService(db=db_session)
    user = await service.register_user(
        UserCreate(email="jwt@example.com", password="pass", role="admin")
    )

    token = service.generate_token(user)
    assert token is not None

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == str(user.id)
    assert payload["email"] == "jwt@example.com"
    assert payload["role"] == "admin"
