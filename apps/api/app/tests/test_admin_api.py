# app/tests/test_admin_api.py
import asyncio
import uuid

import httpx
import pytest
from fastapi import status

from app.tests.conftest import make_user_helper


async def create_user_and_token(
    client: httpx.AsyncClient,
    email: str,
    role: str = "user",
    password: str = "password123",
    full_name: str | None = None,
) -> tuple[dict, str]:
    """Helper to insert a user directly via DB and return the user profile dict and JWT token."""
    return await make_user_helper(
        client=client,
        email=email,
        role=role,
        password=password,
        full_name=full_name,
    )


@pytest.mark.asyncio
async def test_admin_endpoints_unauthorized_and_forbidden_for_regular_user(
    client: httpx.AsyncClient,
):
    """Verify that unauthenticated and regular users cannot access administrative endpoints."""
    # 1. Unauthenticated request
    unauth_res = await client.get("/api/v1/admin/users")
    assert unauth_res.status_code == status.HTTP_401_UNAUTHORIZED

    # 2. Regular user request
    user_data, user_token = await create_user_and_token(
        client, "normal_user@example.com", role="user"
    )
    user_headers = {"Authorization": f"Bearer {user_token}"}
    target_id = str(uuid.uuid4())

    endpoints = [
        ("GET", "/api/v1/admin/users", None),
        ("GET", f"/api/v1/admin/users/{target_id}", None),
        ("POST", f"/api/v1/admin/users/{target_id}/ban", {"reason": "test"}),
        ("POST", f"/api/v1/admin/users/{target_id}/unban", None),
        ("PATCH", f"/api/v1/admin/users/{target_id}/role", {"role": "admin"}),
    ]

    for method, path, body in endpoints:
        if method == "GET":
            res = await client.get(path, headers=user_headers)
        elif method == "POST":
            res = await client.post(path, json=body, headers=user_headers)
        else:
            res = await client.patch(path, json=body, headers=user_headers)
        assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_admin_list_users_pagination_search_and_filters(
    client: httpx.AsyncClient,
):
    """Verify admin listing with page-based pagination, substring search, and role/status filtering."""
    _, admin_token = await create_user_and_token(
        client, "lead_admin@example.com", role="admin", full_name="Admin Chief"
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    u1, _ = await create_user_and_token(
        client, "alice.smith@example.com", role="user", full_name="Alice Smith"
    )
    u2, _ = await create_user_and_token(
        client, "bob.jones@example.com", role="user", full_name="Bob Jones"
    )
    u3, _ = await create_user_and_token(
        client, "charlie.admin@example.com", role="admin", full_name="Charlie Admin"
    )

    # 1. Standard listing
    list_res = await client.get(
        "/api/v1/admin/users?page=1&limit=10", headers=admin_headers
    )
    assert list_res.status_code == status.HTTP_200_OK
    body = list_res.json()
    assert body["total"] >= 4
    assert body["page"] == 1
    assert len(body["items"]) >= 4

    # 2. Search by name substring
    search_res = await client.get(
        "/api/v1/admin/users?search=Alice", headers=admin_headers
    )
    assert search_res.status_code == status.HTTP_200_OK
    search_body = search_res.json()
    assert search_body["total"] == 1
    assert search_body["items"][0]["email"] == "alice.smith@example.com"

    # 3. Search by email substring
    email_search = await client.get(
        "/api/v1/admin/users?search=bob.jones", headers=admin_headers
    )
    assert email_search.status_code == status.HTTP_200_OK
    assert email_search.json()["total"] == 1

    # 4. Filter by role
    role_res = await client.get("/api/v1/admin/users?role=admin", headers=admin_headers)
    assert role_res.status_code == status.HTTP_200_OK
    for item in role_res.json()["items"]:
        assert item["role"] == "admin"

    # 5. Filter by status: ban user Bob, then check active vs banned filters
    await client.post(
        f"/api/v1/admin/users/{u2['id']}/ban",
        json={"reason": "Inappropriate content"},
        headers=admin_headers,
    )

    banned_filter = await client.get(
        "/api/v1/admin/users?status=banned", headers=admin_headers
    )
    assert banned_filter.status_code == status.HTTP_200_OK
    banned_items = banned_filter.json()["items"]
    assert any(item["id"] == u2["id"] for item in banned_items)

    active_filter = await client.get(
        "/api/v1/admin/users?status=active", headers=admin_headers
    )
    assert active_filter.status_code == status.HTTP_200_OK
    active_items = active_filter.json()["items"]
    assert not any(item["id"] == u2["id"] for item in active_items)


@pytest.mark.asyncio
async def test_admin_get_user_detail_and_chat_sessions_count(
    client: httpx.AsyncClient,
):
    """Verify detailed user view with profile and chat sessions counter."""
    _, admin_token = await create_user_and_token(
        client, "inspect_admin@example.com", role="admin"
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    target_user, target_token = await create_user_and_token(
        client,
        "chatty_user@example.com",
        role="user",
        full_name="Chatty Person",
    )
    target_headers = {"Authorization": f"Bearer {target_token}"}

    # Create 2 chat sessions for target user
    await client.post(
        "/api/v1/chats", json={"title": "Session 1"}, headers=target_headers
    )
    await client.post(
        "/api/v1/chats", json={"title": "Session 2"}, headers=target_headers
    )

    detail_res = await client.get(
        f"/api/v1/admin/users/{target_user['id']}", headers=admin_headers
    )
    assert detail_res.status_code == status.HTTP_200_OK
    detail = detail_res.json()
    assert detail["id"] == target_user["id"]
    assert detail["email"] == "chatty_user@example.com"
    assert detail["full_name"] == "Chatty Person"
    assert detail["chat_sessions_count"] == 2
    assert detail["is_banned"] is False


@pytest.mark.asyncio
async def test_admin_ban_user_success_and_immediate_token_revocation(
    client: httpx.AsyncClient,
):
    """Verify banning a user records ban metadata and immediately invalidates active sessions in get_current_user."""
    _, admin_token = await create_user_and_token(
        client, "ban_admin@example.com", role="admin"
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    target_user, target_token = await create_user_and_token(
        client, "malicious_user@example.com", role="user"
    )
    target_headers = {"Authorization": f"Bearer {target_token}"}

    # Verify target user token currently works
    pre_ban = await client.get("/api/v1/users/me", headers=target_headers)
    assert pre_ban.status_code == status.HTTP_200_OK

    # Admin bans target user
    ban_res = await client.post(
        f"/api/v1/admin/users/{target_user['id']}/ban",
        json={"reason": "Spam and abuse violation"},
        headers=admin_headers,
    )
    assert ban_res.status_code == status.HTTP_200_OK
    ban_body = ban_res.json()
    assert ban_body["success"] is True
    assert ban_body["user"]["is_banned"] is True
    assert ban_body["user"]["ban_reason"] == "Spam and abuse violation"
    assert ban_body["user"]["banned_at"] is not None

    # Target user's token is immediately rejected with 403 Forbidden
    post_ban = await client.get("/api/v1/users/me", headers=target_headers)
    assert post_ban.status_code == status.HTTP_403_FORBIDDEN
    assert "Account has been suspended" in post_ban.json()["detail"]
    assert "Spam and abuse violation" in post_ban.json()["detail"]


@pytest.mark.asyncio
async def test_admin_unban_user_restores_access(
    client: httpx.AsyncClient,
):
    """Verify unbanning restores access for the target user."""
    _, admin_token = await create_user_and_token(
        client, "unban_admin@example.com", role="admin"
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    target_user, target_token = await create_user_and_token(
        client, "reformed_user@example.com", role="user"
    )
    target_headers = {"Authorization": f"Bearer {target_token}"}

    # Ban
    await client.post(
        f"/api/v1/admin/users/{target_user['id']}/ban",
        json={"reason": "Temporary suspension"},
        headers=admin_headers,
    )
    assert (
        await client.get("/api/v1/users/me", headers=target_headers)
    ).status_code == status.HTTP_403_FORBIDDEN

    # Unban
    unban_res = await client.post(
        f"/api/v1/admin/users/{target_user['id']}/unban",
        headers=admin_headers,
    )
    assert unban_res.status_code == status.HTTP_200_OK
    assert unban_res.json()["user"]["is_banned"] is False
    assert unban_res.json()["user"]["ban_reason"] is None

    # Target user can now access protected endpoints
    assert (
        await client.get("/api/v1/users/me", headers=target_headers)
    ).status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_admin_unban_does_not_revalidate_pre_ban_token(
    client: httpx.AsyncClient,
):
    """Tokens issued before a ban must stay 401 after unban; fresh login works."""
    _, admin_token = await create_user_and_token(
        client, "unban_revoke_admin@example.com", role="admin"
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    target_user, pre_ban_token = await create_user_and_token(
        client, "pre_ban_user@example.com", role="user", password="password123"
    )
    pre_ban_headers = {"Authorization": f"Bearer {pre_ban_token}"}

    # Ensure iat < tokens_valid_after
    await asyncio.sleep(1.05)

    ban_res = await client.post(
        f"/api/v1/admin/users/{target_user['id']}/ban",
        json={"reason": "Abuse"},
        headers=admin_headers,
    )
    assert ban_res.status_code == status.HTTP_200_OK

    unban_res = await client.post(
        f"/api/v1/admin/users/{target_user['id']}/unban",
        headers=admin_headers,
    )
    assert unban_res.status_code == status.HTTP_200_OK

    # Pre-ban token must remain rejected
    assert (
        await client.get("/api/v1/users/me", headers=pre_ban_headers)
    ).status_code == status.HTTP_401_UNAUTHORIZED

    # Fresh login after unban succeeds
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": "pre_ban_user@example.com", "password": "password123"},
    )
    assert login_res.status_code == status.HTTP_200_OK
    fresh_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}
    assert (
        await client.get("/api/v1/users/me", headers=fresh_headers)
    ).status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_regular_admin_cannot_unban_admin_but_super_admin_can(
    client: httpx.AsyncClient,
):
    """Regular admins cannot unban administrative accounts; super_admin can."""
    _, super_token = await create_user_and_token(
        client, "unban_hier_super@example.com", role="super_admin"
    )
    _, regular_admin_token = await create_user_and_token(
        client, "unban_hier_admin_y@example.com", role="admin"
    )
    target_admin, _ = await create_user_and_token(
        client, "unban_hier_admin_x@example.com", role="admin"
    )

    super_headers = {"Authorization": f"Bearer {super_token}"}
    regular_headers = {"Authorization": f"Bearer {regular_admin_token}"}

    # Super admin bans admin X
    ban_res = await client.post(
        f"/api/v1/admin/users/{target_admin['id']}/ban",
        json={"reason": "Policy violation"},
        headers=super_headers,
    )
    assert ban_res.status_code == status.HTTP_200_OK

    # Regular admin Y attempts to unban admin X -> 403 Forbidden
    forbidden_res = await client.post(
        f"/api/v1/admin/users/{target_admin['id']}/unban",
        headers=regular_headers,
    )
    assert forbidden_res.status_code == status.HTTP_403_FORBIDDEN

    # Super admin unbans admin X -> 200 OK
    unban_res = await client.post(
        f"/api/v1/admin/users/{target_admin['id']}/unban",
        headers=super_headers,
    )
    assert unban_res.status_code == status.HTTP_200_OK
    assert unban_res.json()["user"]["is_banned"] is False


@pytest.mark.asyncio
async def test_admin_self_ban_guardrail(
    client: httpx.AsyncClient,
):
    """Verify admins cannot ban their own account."""
    admin_data, admin_token = await create_user_and_token(
        client, "self_ban_admin@example.com", role="admin"
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    res = await client.post(
        f"/api/v1/admin/users/{admin_data['id']}/ban",
        json={"reason": "Testing self ban"},
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot ban their own account" in res.json()["detail"]


@pytest.mark.asyncio
async def test_regular_admin_cannot_ban_other_admin_or_super_admin(
    client: httpx.AsyncClient,
):
    """Verify regular admins are forbidden from banning other admins or super admins."""
    _, admin1_token = await create_user_and_token(
        client, "regular_admin1@example.com", role="admin"
    )
    admin2_data, _ = await create_user_and_token(
        client, "regular_admin2@example.com", role="admin"
    )
    super_admin_data, _ = await create_user_and_token(
        client, "super_boss@example.com", role="super_admin"
    )

    admin1_headers = {"Authorization": f"Bearer {admin1_token}"}

    # Admin 1 attempts to ban Admin 2 -> 403 Forbidden
    res1 = await client.post(
        f"/api/v1/admin/users/{admin2_data['id']}/ban",
        json={"reason": "Hostile takeover"},
        headers=admin1_headers,
    )
    assert res1.status_code == status.HTTP_403_FORBIDDEN
    assert "Insufficient permissions" in res1.json()["detail"]

    # Admin 1 attempts to ban Super Admin -> 403 Forbidden
    res2 = await client.post(
        f"/api/v1/admin/users/{super_admin_data['id']}/ban",
        json={"reason": "Mutiny"},
        headers=admin1_headers,
    )
    assert res2.status_code == status.HTTP_403_FORBIDDEN
    assert "Insufficient permissions" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_super_admin_can_ban_regular_admin_but_not_self_or_other_super_admin(
    client: httpx.AsyncClient,
):
    """Verify super admin can ban regular admin, but cannot ban themselves or another super admin."""
    super1_data, super1_token = await create_user_and_token(
        client, "super1@example.com", role="super_admin"
    )
    super2_data, _ = await create_user_and_token(
        client, "super2@example.com", role="super_admin"
    )
    admin_data, _ = await create_user_and_token(
        client, "sub_admin@example.com", role="admin"
    )

    super1_headers = {"Authorization": f"Bearer {super1_token}"}

    # 1. Super admin bans regular admin -> 200 OK
    ban_admin_res = await client.post(
        f"/api/v1/admin/users/{admin_data['id']}/ban",
        json={"reason": "Misconduct as admin"},
        headers=super1_headers,
    )
    assert ban_admin_res.status_code == status.HTTP_200_OK
    assert ban_admin_res.json()["user"]["is_banned"] is True

    # 2. Super admin attempts to ban themselves -> 400 Bad Request
    self_ban_res = await client.post(
        f"/api/v1/admin/users/{super1_data['id']}/ban",
        json={"reason": "Self ban"},
        headers=super1_headers,
    )
    assert self_ban_res.status_code == status.HTTP_400_BAD_REQUEST

    # 3. Super admin attempts to ban another super admin -> 403 Forbidden
    other_super_ban = await client.post(
        f"/api/v1/admin/users/{super2_data['id']}/ban",
        json={"reason": "Power struggle"},
        headers=super1_headers,
    )
    assert other_super_ban.status_code == status.HTTP_403_FORBIDDEN
    assert (
        "Super administrator accounts cannot be banned"
        in other_super_ban.json()["detail"]
    )


@pytest.mark.asyncio
async def test_super_admin_update_role_success_and_guardrails(
    client: httpx.AsyncClient,
):
    """Verify super admin can promote and demote roles, with self-demotion protection."""
    super_data, super_token = await create_user_and_token(
        client, "super_manager@example.com", role="super_admin"
    )
    regular_user, _ = await create_user_and_token(
        client, "member@example.com", role="user"
    )
    regular_admin, admin_token = await create_user_and_token(
        client, "standard_admin@example.com", role="admin"
    )

    super_headers = {"Authorization": f"Bearer {super_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Regular admin attempts to update role -> 403 Forbidden
    admin_role_attempt = await client.patch(
        f"/api/v1/admin/users/{regular_user['id']}/role",
        json={"role": "admin"},
        headers=admin_headers,
    )
    assert admin_role_attempt.status_code == status.HTTP_403_FORBIDDEN

    # 2. Super admin promotes user to admin -> 200 OK
    promote_res = await client.patch(
        f"/api/v1/admin/users/{regular_user['id']}/role",
        json={"role": "admin"},
        headers=super_headers,
    )
    assert promote_res.status_code == status.HTTP_200_OK
    assert promote_res.json()["user"]["role"] == "admin"

    # 3. Super admin demotes admin to user -> 200 OK
    demote_res = await client.patch(
        f"/api/v1/admin/users/{regular_admin['id']}/role",
        json={"role": "user"},
        headers=super_headers,
    )
    assert demote_res.status_code == status.HTTP_200_OK
    assert demote_res.json()["user"]["role"] == "user"

    # 4. Super admin attempts self-demotion -> 400 Bad Request
    self_demote = await client.patch(
        f"/api/v1/admin/users/{super_data['id']}/role",
        json={"role": "user"},
        headers=super_headers,
    )
    assert self_demote.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot modify or demote their own role" in self_demote.json()["detail"]


@pytest.mark.asyncio
async def test_nonexistent_user_admin_operations_return_404(
    client: httpx.AsyncClient,
):
    """Verify operations on non-existent UUIDs return 404 Not Found."""
    _, super_token = await create_user_and_token(
        client, "super_lookup@example.com", role="super_admin"
    )
    headers = {"Authorization": f"Bearer {super_token}"}
    fake_id = str(uuid.uuid4())

    assert (
        await client.get(f"/api/v1/admin/users/{fake_id}", headers=headers)
    ).status_code == status.HTTP_404_NOT_FOUND

    assert (
        await client.post(
            f"/api/v1/admin/users/{fake_id}/ban",
            json={"reason": "test"},
            headers=headers,
        )
    ).status_code == status.HTTP_404_NOT_FOUND

    assert (
        await client.post(f"/api/v1/admin/users/{fake_id}/unban", headers=headers)
    ).status_code == status.HTTP_404_NOT_FOUND

    assert (
        await client.patch(
            f"/api/v1/admin/users/{fake_id}/role",
            json={"role": "admin"},
            headers=headers,
        )
    ).status_code == status.HTTP_404_NOT_FOUND
