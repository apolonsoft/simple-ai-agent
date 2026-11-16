# Technical Architecture Plan: Admin User Management & Banning API

## 1. Architecture Overview
The admin subsystem introduces a dedicated administrative controller and service layer in `apps/api` protected by role-based authorization dependencies (`require_admin_role`, `require_super_admin_role`). Banning triggers immediate Redis token revocation, and database state transitions are managed via SQLAlchemy 2.0 async sessions.

---

## 2. Affected Files & Schema

### Database Layer
- **Model**: `apps/api/app/models/user.py`
  - `is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)`
  - `banned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)`
  - `ban_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)`
- **Migration**: `apps/api/alembic/versions/b1c2d3e4f5a6_add_ban_fields_to_users.py`

### Auth & RBAC Layer
- **Dependencies**: `apps/api/app/core/dependencies.py`
  - Update `get_current_user` to check `if user.is_banned: raise HTTPException(status_code=403, detail=f"Account has been suspended. Reason: {user.ban_reason or 'No reason provided.'}")`
  - Add `require_admin_role`: grants access to `admin` and `super_admin`.
  - Add `require_super_admin_role`: strictly requires `super_admin`.

### Schemas
- **File**: `apps/api/app/schemas/admin.py`
  - `AdminBanUserRequest(reason: str | None = None)`
  - `AdminUpdateRoleRequest(role: Literal["user", "admin", "super_admin"])`
  - `AdminUserListItem(id, email, full_name, role, is_active, is_banned, banned_at, ban_reason, created_at)`
  - `AdminUserListResponse(items: list[AdminUserListItem], total: int, page: int, limit: int, total_pages: int)`
  - `AdminUserDetailResponse(AdminUserListItem + avatar_url, bio, chat_sessions_count: int, updated_at)`

### Service & Controller Layers
- **Service**: `apps/api/app/services/admin_service.py`
- **Controller**: `apps/api/app/controllers/admin_controller.py`
- **Router**: `apps/api/app/routes/admin_routes.py`
- **Main App**: `apps/api/app/main.py` (mounts `/api/v1/admin`)

---

## 3. Testing Strategy
- Create `apps/api/app/tests/test_admin_api.py` covering:
  - Unauthorized and non-admin requests rejected (401 / 403).
  - User listing with pagination, search, role and status filtering.
  - User detail inspection including chat session counter.
  - Ban execution: database updates, Redis session revocation, and immediate rejection of user requests.
  - Unban execution: clearing ban state and restoring access.
  - Self-action guardrails: admin cannot ban self; super_admin cannot demote self.
  - Hierarchy guardrails: regular admin cannot ban or demote other admins or super_admin.
  - Super admin role promotion/demotion workflow.
