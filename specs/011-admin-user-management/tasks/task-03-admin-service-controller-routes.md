### Task 03: Admin Service, Controller & Routes

- [x] Completed

#### Full Description
Implement `AdminService`, `AdminController`, and `admin_routes` providing the REST endpoints for listing users with pagination and search, retrieving detailed user info, banning users with Redis token revocation, unbanning users, and updating roles, enforced by administrative guardrails.

#### Technical Instructions
1. Create `apps/api/app/services/admin_service.py`:
   - `list_users(page, limit, search, role, status)`:
     - Applies `page` (1-indexed) and `limit` (max 100).
     - Filters by `role` if provided.
     - Filters by `is_banned` if `status == "banned"`, `is_banned == False` if `status == "active"`.
     - Filters by `email.ilike(f"%{search}%") | full_name.ilike(f"%{search}%")` if search provided.
     - Computes `total` and `total_pages`.
   - `get_user_detail(user_id)`:
     - Fetches user and counts chat sessions via `select(func.count(ChatSessionModel.id)).where(ChatSessionModel.user_id == user_id)`.
     - Raises `404 Not Found` if user does not exist.
   - `ban_user(admin_user, target_user_id, reason)`:
     - Guardrails:
       - If `admin_user.id == target_user_id`: raise `400 Bad Request` ("Admins cannot ban their own account.").
       - If `admin_user.role != "super_admin"` and target user is `admin` or `super_admin`: raise `403 Forbidden` ("Insufficient permissions to ban administrative accounts.").
     - Action:
       - Set `is_banned = True`, `banned_at = datetime.now(timezone.utc)`, `ban_reason = reason`.
       - Write Redis session revocation timestamp: `redis.set(f"revoked_user:{target_user_id}", int(datetime.now(timezone.utc).timestamp()), ex=86400 * 30)`.
       - Commit and return updated user.
   - `unban_user(admin_user, target_user_id)`:
     - Guardrail: Target must exist.
     - Action: Set `is_banned = False`, `banned_at = None`, `ban_reason = None`. Remove Redis revocation key or update state.
     - Commit and return updated user.
   - `update_role(super_admin_user, target_user_id, new_role)`:
     - Guardrails:
       - If `super_admin_user.id == target_user_id`: raise `400 Bad Request` ("Super admins cannot modify their own role.").
     - Action: Update `role = new_role`, commit and return updated user.
2. Create `apps/api/app/controllers/admin_controller.py`:
   - Wraps service methods and maps outputs to `AdminUserListResponse`, `AdminUserDetailResponse`, `AdminActionResponse`.
3. Create `apps/api/app/routes/admin_routes.py`:
   - Router with prefix `/admin/users`, tags `["Admin"]`.
   - `GET /` -> `list_users` (requires `require_admin_role`).
   - `GET /{user_id}` -> `get_user_detail` (requires `require_admin_role`).
   - `POST /{user_id}/ban` -> `ban_user` (requires `require_admin_role`).
   - `POST /{user_id}/unban` -> `unban_user` (requires `require_admin_role`).
   - `PATCH /{user_id}/role` -> `update_role` (requires `require_super_admin_role`).
4. Mount `admin_routes.router` in `apps/api/app/main.py`.

#### Files Touched
- `apps/api/app/services/admin_service.py` (Created)
- `apps/api/app/controllers/admin_controller.py` (Created)
- `apps/api/app/routes/admin_routes.py` (Created)
- `apps/api/app/main.py` (Modified)

#### Verification Strategy
- Command: `make lint`

#### Prepared Git Commit
```text
feat(api): implement AdminService, controller, and admin_routes endpoints

- Implement paginated search, filter, and user inspection in AdminService
- Implement ban_user with self-action guardrails and Redis session revocation
- Implement unban_user and super_admin update_role endpoints
- Mount admin_routes under /api/v1/admin/users
- Verification: make lint passed
```
