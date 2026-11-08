# app/tests/conftest.py
import pytest_asyncio
from typing import AsyncGenerator
import httpx
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

import app.models  # Ensure all models are registered on Base.metadata
from app.db.session import Base, get_db, get_session_factory
from app.main import app as fastapi_app

# Isolated in-memory async SQLite for test execution
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    poolclass=StaticPool,
)

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
    fastapi_app.dependency_overrides[get_session_factory] = lambda: TestingAsyncSessionLocal

    transport = ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    fastapi_app.dependency_overrides.clear()
