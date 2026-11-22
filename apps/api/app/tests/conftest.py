# app/tests/conftest.py
from collections.abc import AsyncGenerator, Callable

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import get_password_hash
from app.db.session import Base, get_db, get_session_factory
from app.main import app as fastapi_app
from app.models.user import UserModel

# Isolated in-memory async SQLite for test execution
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    poolclass=StaticPool,
)


@event.listens_for(test_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Creates fresh database tables before each test and drops them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingAsyncSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async httpx client that automatically overrides get_db with the test async session."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestingAsyncSessionLocal() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_session_factory] = lambda: (
        TestingAsyncSessionLocal
    )

    transport = ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as async_client:
        yield async_client

    fastapi_app.dependency_overrides.clear()


async def make_user_helper(
    client: httpx.AsyncClient,
    email: str,
    role: str = "user",
    password: str = "password123",
    full_name: str | None = None,
) -> tuple[dict, str]:
    """Inserts a UserModel with any role directly via TestingAsyncSessionLocal, then logs in through the API and returns (user_dict, token)."""
    async with TestingAsyncSessionLocal() as session:
        user = UserModel(
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
            full_name=full_name,
            is_active=True,
            is_banned=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_dict = {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "full_name": user.full_name,
        }

    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return user_dict, token


@pytest.fixture(scope="function")
def make_user(client: httpx.AsyncClient) -> Callable:
    """Fixture returning an async factory that creates users directly in the database."""

    async def _make_user(
        email: str,
        role: str = "user",
        password: str = "password123",
        full_name: str | None = None,
    ) -> tuple[dict, str]:
        return await make_user_helper(
            client=client,
            email=email,
            role=role,
            password=password,
            full_name=full_name,
        )

    return _make_user
