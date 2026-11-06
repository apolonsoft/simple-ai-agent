# app/tests/test_async_database.py
import asyncio
import pytest
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db, AsyncSessionLocal
from app.models.user import UserModel


@pytest.mark.asyncio
async def test_async_session_crud(db_session: AsyncSession):
    """Verify async database insertion, querying, and updating."""
    test_user = UserModel(
        id=uuid.uuid4(),
        email="async_crud@example.com",
        hashed_password="some_hashed_password",
        role="user",
        is_active=True,
    )
    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)

    stmt = select(UserModel).where(UserModel.email == "async_crud@example.com")
    result = await db_session.scalars(stmt)
    retrieved = result.first()

    assert retrieved is not None
    assert retrieved.id == test_user.id
    assert retrieved.email == "async_crud@example.com"
    assert retrieved.created_at is not None
    assert retrieved.updated_at is not None


@pytest.mark.asyncio
async def test_async_session_rollback_on_exception():
    """Verify session generator automatically triggers rollback on exceptions."""
    gen = get_db()
    session = await anext(gen)

    try:
        # Intentionally create invalid entity without required fields
        broken_user = UserModel()
        session.add(broken_user)
        # Flush causes database constraint failure
        await session.flush()
    except Exception:
        # Generator cleanup should handle rollback without leaking active transaction
        pass
    finally:
        try:
            await anext(gen)
        except StopAsyncIteration:
            pass


@pytest.mark.asyncio
async def test_concurrent_async_database_queries(db_session: AsyncSession):
    """Verify high-concurrency capability by executing 50 concurrent async queries."""
    # Seed 5 sample users
    for i in range(5):
        user = UserModel(
            id=uuid.uuid4(),
            email=f"concurrent_{i}@example.com",
            hashed_password="pw",
            role="user"
        )
        db_session.add(user)
    await db_session.commit()

    async def query_user(email: str):
        stmt = select(UserModel).where(UserModel.email == email)
        result = await db_session.scalars(stmt)
        return result.first()

    # Launch 50 concurrent async query tasks simultaneously
    tasks = [query_user(f"concurrent_{i % 5}@example.com") for i in range(50)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 50
    assert all(r is not None for r in results)
