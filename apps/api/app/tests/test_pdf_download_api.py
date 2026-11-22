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
async def test_download_pdf_success_via_query_param(client: httpx.AsyncClient):
    """Verify that user can download a generated PDF using ?token= query parameter without Authorization header."""
    token = await get_auth_token(client, "pdf_query_token@example.com")

    raw_res = create_pdf(
        title="Query Param Test Document",
        content="Testing download via URL query parameter for browser direct navigation.",
        filename="test_query_token_doc.pdf",
    )
    data = json.loads(raw_res)
    assert data["status"] == "success"
    filename = data["filename"]

    # Request with ?token= query parameter and NO Authorization header
    download_res = await client.get(f"/api/v1/chats/files/pdf/{filename}?token={token}")
    assert download_res.status_code == status.HTTP_200_OK
    assert "application/pdf" in download_res.headers.get("content-type", "")
    assert download_res.content.startswith(b"%PDF")

    file_path = os.path.join(_get_output_dir(), filename)
    if os.path.exists(file_path):
        os.remove(file_path)
