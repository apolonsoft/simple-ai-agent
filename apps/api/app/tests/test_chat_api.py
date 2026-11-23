# app/tests/test_chat_api.py
import uuid

import httpx
import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chat_service import ChatService


async def get_auth_token(
    client: httpx.AsyncClient, email: str = "chat_user@example.com"
) -> str:
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "password123"}
    )
    login_res = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": "password123"}
    )
    return login_res.json()["access_token"]


@pytest.mark.asyncio
async def test_create_and_list_chat_sessions(client: httpx.AsyncClient):
    token = await get_auth_token(client, "alice_chat@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create two chat sessions
    res1 = await client.post(
        "/api/v1/chats", json={"title": "Project Planning"}, headers=headers
    )
    assert res1.status_code == status.HTTP_201_CREATED
    session1_id = res1.json()["id"]
    assert res1.json()["title"] == "Project Planning"

    res2 = await client.post(
        "/api/v1/chats", json={"title": "Code Review"}, headers=headers
    )
    assert res2.status_code == status.HTTP_201_CREATED
    session2_id = res2.json()["id"]

    # 2. List sessions
    list_res = await client.get("/api/v1/chats", headers=headers)
    assert list_res.status_code == status.HTTP_200_OK
    sessions = list_res.json()
    assert len(sessions) == 2
    session_ids = [s["id"] for s in sessions]
    assert session1_id in session_ids
    assert session2_id in session_ids


@pytest.mark.asyncio
async def test_get_and_delete_chat_session(client: httpx.AsyncClient):
    token = await get_auth_token(client, "bob_chat@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await client.post(
        "/api/v1/chats", json={"title": "Temporary Session"}, headers=headers
    )
    session_id = create_res.json()["id"]

    # Get session details
    get_res = await client.get(f"/api/v1/chats/{session_id}", headers=headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == session_id
    assert get_res.json()["title"] == "Temporary Session"

    # Delete session
    del_res = await client.delete(f"/api/v1/chats/{session_id}", headers=headers)
    assert del_res.status_code == status.HTTP_200_OK

    # Fetching deleted session returns 404
    not_found_res = await client.get(f"/api/v1/chats/{session_id}", headers=headers)
    assert not_found_res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_multi_user_isolation(client: httpx.AsyncClient):
    """Critical Security Test: Verify User A cannot access User B's sessions."""
    token_a = await get_auth_token(client, "user_a@example.com")
    token_b = await get_auth_token(client, "user_b@example.com")

    # User A creates a session
    res_a = await client.post(
        "/api/v1/chats",
        json={"title": "User A Private Notes"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    session_a_id = res_a.json()["id"]

    # User B attempts to access User A's session -> must return 404 Not Found
    hacked_get = await client.get(
        f"/api/v1/chats/{session_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert hacked_get.status_code == status.HTTP_404_NOT_FOUND

    # User B attempts to delete User A's session -> must return 404 Not Found
    hacked_del = await client.delete(
        f"/api/v1/chats/{session_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert hacked_del.status_code == status.HTTP_404_NOT_FOUND

    # User B lists sessions -> User A's session is not listed
    list_b = await client.get(
        "/api/v1/chats",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert all(s["id"] != session_a_id for s in list_b.json())


@pytest.mark.asyncio
async def test_session_message_history(
    client: httpx.AsyncClient, db_session: AsyncSession
):
    token = await get_auth_token(client, "history_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await client.post(
        "/api/v1/chats", json={"title": "History Test"}, headers=headers
    )
    session_id = uuid.UUID(create_res.json()["id"])
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])

    # Directly insert messages via ChatService
    service = ChatService(db=db_session)
    await service.add_message(
        session_id=session_id, user_id=user_id, role="user", content="Hello!"
    )
    await service.add_message(
        session_id=session_id,
        user_id=user_id,
        role="assistant",
        content="Greetings! How can I help?",
    )

    # Fetch messages through API
    msg_res = await client.get(f"/api/v1/chats/{session_id}/messages", headers=headers)
    assert msg_res.status_code == status.HTTP_200_OK
    messages = msg_res.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello!"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Greetings! How can I help?"


@pytest.mark.asyncio
async def test_unauthenticated_chat_access_rejected(client: httpx.AsyncClient):
    random_id = uuid.uuid4()
    assert (
        await client.get("/api/v1/chats")
    ).status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        await client.post("/api/v1/chats", json={})
    ).status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        await client.get(f"/api/v1/chats/{random_id}")
    ).status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        await client.delete(f"/api/v1/chats/{random_id}")
    ).status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_list_sessions_pagination_and_limit_bounds(
    client: httpx.AsyncClient, db_session: AsyncSession
):
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    from app.models.chat import ChatSessionModel
    from app.models.user import UserModel

    token = await get_auth_token(client, "paginate_chat@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    user = await db_session.scalar(
        select(UserModel).where(UserModel.email == "paginate_chat@example.com")
    )
    assert user is not None

    base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i in range(150):
        db_session.add(
            ChatSessionModel(
                id=uuid.uuid4(),
                user_id=user.id,
                title=f"Session {i:03d}",
                created_at=base_time + timedelta(seconds=i),
                updated_at=base_time + timedelta(seconds=i),
            )
        )
    await db_session.commit()

    # Default limit returns 100
    default_res = await client.get("/api/v1/chats", headers=headers)
    assert default_res.status_code == status.HTTP_200_OK
    assert len(default_res.json()) == 100

    # Cursor pagination with limit=10 & before=<created_at of 10th>
    page1 = await client.get("/api/v1/chats?limit=10", headers=headers)
    assert page1.status_code == status.HTTP_200_OK
    page1_items = page1.json()
    assert len(page1_items) == 10
    assert page1_items[0]["title"] == "Session 149"

    cursor = page1_items[-1]["created_at"]
    page2 = await client.get(
        "/api/v1/chats", params={"limit": 10, "before": cursor}, headers=headers
    )
    assert page2.status_code == status.HTTP_200_OK
    page2_items = page2.json()
    assert len(page2_items) == 10
    assert page2_items[0]["title"] == "Session 139"
    assert {x["id"] for x in page1_items}.isdisjoint({x["id"] for x in page2_items})

    # Limit > 200 rejected with 422
    over_limit = await client.get("/api/v1/chats?limit=500", headers=headers)
    assert over_limit.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_message_content_over_32000_chars_rejected(client: httpx.AsyncClient):
    """Messages longer than 32,000 characters must fail schema validation (422)."""
    token = await get_auth_token(client, "longmsg_chat@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await client.post(
        "/api/v1/chats", json={"title": "Limit Test"}, headers=headers
    )
    session_id = create_res.json()["id"]

    res = await client.post(
        f"/api/v1/chats/{session_id}/stream",
        json={"content": "a" * 32_001},
        headers=headers,
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
