# app/tests/test_chat_api.py
import pytest
import uuid
from fastapi import status
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.chat_service import ChatService


async def get_auth_token(client: httpx.AsyncClient, email: str = "chat_user@example.com") -> str:
    await client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    login_res = await client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})
    return login_res.json()["access_token"]


@pytest.mark.asyncio
async def test_create_and_list_chat_sessions(client: httpx.AsyncClient):
    token = await get_auth_token(client, "alice_chat@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create two chat sessions
    res1 = await client.post("/api/v1/chats", json={"title": "Project Planning"}, headers=headers)
    assert res1.status_code == status.HTTP_201_CREATED
    session1_id = res1.json()["id"]
    assert res1.json()["title"] == "Project Planning"

    res2 = await client.post("/api/v1/chats", json={"title": "Code Review"}, headers=headers)
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

    create_res = await client.post("/api/v1/chats", json={"title": "Temporary Session"}, headers=headers)
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
async def test_session_message_history(client: httpx.AsyncClient, db_session: AsyncSession):
    token = await get_auth_token(client, "history_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await client.post("/api/v1/chats", json={"title": "History Test"}, headers=headers)
    session_id = uuid.UUID(create_res.json()["id"])
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])

    # Directly insert messages via ChatService
    service = ChatService(db=db_session)
    await service.add_message(session_id=session_id, user_id=user_id, role="user", content="Hello!")
    await service.add_message(session_id=session_id, user_id=user_id, role="assistant", content="Greetings! How can I help?")

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
    assert (await client.get("/api/v1/chats")).status_code == status.HTTP_401_UNAUTHORIZED
    assert (await client.post("/api/v1/chats", json={})).status_code == status.HTTP_401_UNAUTHORIZED
    assert (await client.get(f"/api/v1/chats/{random_id}")).status_code == status.HTTP_401_UNAUTHORIZED
    assert (await client.delete(f"/api/v1/chats/{random_id}")).status_code == status.HTTP_401_UNAUTHORIZED
