# app/tests/test_pdf_download_api.py
import json
import os

import httpx
import pytest
from fastapi import status

from app.mcp_servers.pdf_server import _get_output_dir, create_pdf


async def get_auth_token(
    client: httpx.AsyncClient, email: str = "pdf_user@example.com"
) -> str:
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "password123"}
    )
    login_res = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": "password123"}
    )
    return login_res.json()["access_token"]


async def associate_file_with_user(
    client: httpx.AsyncClient, token: str, filename: str
) -> None:
    """Helper to record an executed create_pdf tool call in user's chat message."""
    import uuid

    from app.core.dependencies import decode_access_token
    from app.services.chat_service import ChatService
    from app.tests.conftest import TestingAsyncSessionLocal

    headers = {"Authorization": f"Bearer {token}"}
    sess_res = await client.post(
        "/api/v1/chats", json={"title": "PDF Session"}, headers=headers
    )
    session_id = sess_res.json()["id"]

    payload = decode_access_token(token)
    assert payload is not None
    user_id = uuid.UUID(payload["sub"])
    async with TestingAsyncSessionLocal() as session:
        chat_service = ChatService(session)
        msg = await chat_service.add_message(
            session_id=uuid.UUID(session_id),
            user_id=user_id,
            role="assistant",
            content="Generated PDF report",
        )
        assert msg is not None
        await chat_service.update_message_tool_call(
            message=msg,
            tool_call_id=f"call_{uuid.uuid4().hex[:8]}",
            status="executed",
            result=json.dumps({"filename": filename}),
        )


@pytest.mark.asyncio
async def test_download_pdf_unauthenticated(client: httpx.AsyncClient):
    """Verify that file download endpoint rejects unauthenticated requests with 401."""
    res = await client.get("/api/v1/chats/files/pdf/some_doc.pdf")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_download_pdf_not_found(client: httpx.AsyncClient):
    """Verify that requesting a non-existent PDF returns 404."""
    token = await get_auth_token(client, "pdf_notfound@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    res = await client.get(
        "/api/v1/chats/files/pdf/non_existent_doc_12345.pdf", headers=headers
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_download_pdf_invalid_extension(client: httpx.AsyncClient):
    """Verify that requesting non-PDF files is rejected with 400 Bad Request."""
    token = await get_auth_token(client, "pdf_invalid_ext@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    res = await client.get("/api/v1/chats/files/pdf/passwords.txt", headers=headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_download_pdf_path_traversal(client: httpx.AsyncClient):
    """Verify that path traversal attempts are rejected."""
    token = await get_auth_token(client, "pdf_traversal@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    res = await client.get(
        "/api/v1/chats/files/pdf/..%2F..%2Fetc%2Fpasswd.pdf", headers=headers
    )
    assert res.status_code in (
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_404_NOT_FOUND,
    )


@pytest.mark.asyncio
async def test_download_pdf_success(client: httpx.AsyncClient):
    """Verify that an authenticated user can download a generated PDF."""
    token = await get_auth_token(client, "pdf_success@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Generate test document via MCP create_pdf tool
    raw_res = create_pdf(
        title="Download Test Document",
        content="This is a test PDF to verify endpoint downloads.",
        filename="test_download_doc.pdf",
    )
    data = json.loads(raw_res)
    assert data["status"] == "success"
    assert "download_url" in data
    filename = data["filename"]

    # Record ownership in user's chat message
    await associate_file_with_user(client, token, filename)

    # Download file via API
    download_res = await client.get(
        f"/api/v1/chats/files/pdf/{filename}", headers=headers
    )
    assert download_res.status_code == status.HTTP_200_OK
    assert "application/pdf" in download_res.headers.get("content-type", "")
    assert download_res.content.startswith(b"%PDF")

    # Clean up test artifact
    file_path = os.path.join(_get_output_dir(), filename)
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.mark.asyncio
async def test_download_pdf_query_param_token_rejected(client: httpx.AsyncClient):
    """Query parameter ?token= must be rejected; only Authorization header is accepted."""
    token = await get_auth_token(client, "pdf_query_token@example.com")

    raw_res = create_pdf(
        title="Query Param Test Document",
        content="Testing download via URL query parameter is rejected.",
        filename="test_query_token_doc.pdf",
    )
    data = json.loads(raw_res)
    assert data["status"] == "success"
    filename = data["filename"]

    await associate_file_with_user(client, token, filename)

    # Request with ?token= query parameter and NO Authorization header must fail with 401
    download_res = await client.get(f"/api/v1/chats/files/pdf/{filename}?token={token}")
    assert download_res.status_code == status.HTTP_401_UNAUTHORIZED

    file_path = os.path.join(_get_output_dir(), filename)
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.mark.asyncio
async def test_download_pdf_cross_user_isolation(client: httpx.AsyncClient):
    """User A creates a PDF via approved create_pdf; User B requesting filename gets 404; User A gets 200."""
    from unittest.mock import patch

    from app.tests.test_calculator_tools import MockToolCallingProvider

    token_a = await get_auth_token(client, "user_a_pdf@example.com")
    token_b = await get_auth_token(client, "user_b_pdf@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    sess_res = await client.post(
        "/api/v1/chats", json={"title": "User A Session"}, headers=headers_a
    )
    session_id = sess_res.json()["id"]

    mock_pdf_call = {
        "type": "tool_call",
        "name": "create_pdf",
        "arguments": {
            "title": "Private Document",
            "content": "Secret content for user A only.",
            "filename": "private_doc.pdf",
        },
    }
    mock_provider = MockToolCallingProvider(
        tool_call_dict=mock_pdf_call,
        text_after_tool="Your PDF has been generated.",
    )

    with patch(
        "app.services.chat_stream_service.get_llm_provider", return_value=mock_provider
    ):
        await client.post(
            f"/api/v1/chats/{session_id}/stream",
            json={"content": "Generate private pdf"},
            headers=headers_a,
        )

    msgs_res = await client.get(
        f"/api/v1/chats/{session_id}/messages", headers=headers_a
    )
    assistant_msg = msgs_res.json()[1]
    tool_call = assistant_msg["tool_calls"][0]

    with patch(
        "app.services.chat_stream_service.get_llm_provider", return_value=mock_provider
    ):
        await client.post(
            f"/api/v1/chats/{session_id}/tool-calls/approval",
            json={
                "tool_call_id": tool_call["id"],
                "approved": True,
                "message_id": assistant_msg["id"],
            },
            headers=headers_a,
        )

    msgs_res2 = await client.get(
        f"/api/v1/chats/{session_id}/messages", headers=headers_a
    )
    updated_assistant_msg = msgs_res2.json()[1]
    raw_result = updated_assistant_msg["tool_calls"][0]["result"]
    parsed_result = json.loads(raw_result)
    filename = parsed_result["filename"]

    try:
        # User B requests User A's file -> 404
        res_b = await client.get(
            f"/api/v1/chats/files/pdf/{filename}", headers=headers_b
        )
        assert res_b.status_code == status.HTTP_404_NOT_FOUND

        # User A requests their own file -> 200
        res_a = await client.get(
            f"/api/v1/chats/files/pdf/{filename}", headers=headers_a
        )
        assert res_a.status_code == status.HTTP_200_OK
    finally:
        file_path = os.path.join(_get_output_dir(), filename)
        if os.path.exists(file_path):
            os.remove(file_path)
