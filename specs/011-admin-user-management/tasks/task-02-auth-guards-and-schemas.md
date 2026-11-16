### Task 02: Auth Guards & Admin Schemas

- [x] Completed

#### Full Description
Update authentication dependency `get_current_user` to automatically reject banned accounts with HTTP 403 Forbidden. Implement role-checking dependencies `require_admin_role` and `require_super_admin_role`. Define Pydantic request and response schemas for all administrative endpoints.

#### Technical Instructions
1. Update `apps/api/app/core/dependencies.py`:
   - In `get_current_user`, after retrieving user from database:
     ```python
     if user.is_banned:
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail=f"Account has been suspended. Reason: {user.ban_reason or 'No reason specified.'}",
         )
     ```
   - Add `require_admin_role`: checks `current_user.role in ("admin", "super_admin")`.
   - Add `require_super_admin_role`: checks `current_user.role == "super_admin"`.
2. Create `apps/api/app/schemas/admin.py`:
   - `AdminBanUserRequest(BaseModel)`: `reason: str | None = Field(default=None, max_length=500)`
   - `AdminUpdateRoleRequest(BaseModel)`: `role: Literal["user", "admin", "super_admin"]`
   - `AdminUserListItem(BaseModel)`: `id, email, full_name, role, is_active, is_banned, banned_at, ban_reason, created_at`
   - `AdminUserListResponse(BaseModel)`: `items: list[AdminUserListItem], total: int, page: int, limit: int, total_pages: int`
   - `AdminUserDetailResponse(AdminUserListItem)`: adds `avatar_url, bio, chat_sessions_count: int, updated_at`
   - `AdminActionResponse(BaseModel)`: `success: bool, message: str, user: AdminUserListItem`

#### Files Touched
- `apps/api/app/core/dependencies.py` (Modified)
- `apps/api/app/schemas/admin.py` (Created)

#### Verification Strategy
- Command: `make lint`

#### Prepared Git Commit
```text
feat(api): implement admin schemas and ban/role auth dependencies

- Enforce is_banned check in get_current_user dependency with 403 Forbidden
- Add require_admin_role and require_super_admin_role dependency factories
- Create admin schemas for user listing, detail inspection, banning, and role updates
- Verification: make lint passed
```
