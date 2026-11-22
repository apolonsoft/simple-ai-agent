### Task 01: Refactor Session Revocation into One Module

- [x] Completed

**Lesson:** [07 — Session revocation and fail-open vs fail-closed](../lessons/lesson-07-session-revocation-and-failure-modes.md)

#### Full Description
Preparatory refactor with **zero functional change**. Revocation logic (`revoked_user:{id}` Redis keys) is currently spread across three files with different TTLs and duplicated try/except blocks:
- `app/core/dependencies.py:42-58` (read + compare against `iat`)
- `app/services/auth_service.py:157-165` (write on change-password, TTL = token lifetime)
- `app/services/admin_service.py:157-164` (write on ban, TTL = 30 days) and `:191-196` (delete on unban)

Consolidating it first means Task 11 changes one module instead of three. Behavior, TTLs, key names, ordering and fail-open semantics must stay identical.

#### Technical Instructions
1. Create `apps/api/app/core/session_revocation.py`:
   - `REVOCATION_KEY_PREFIX = "revoked_user:"`
   - `async def revoke_user_sessions(user_id: uuid.UUID, ttl_seconds: int) -> None` — writes `int(now)` with `ex=ttl_seconds`; swallows exceptions exactly like today.
   - `async def clear_user_revocation(user_id: uuid.UUID) -> None` — deletes the key; swallows exceptions.
   - `async def is_token_revoked(user_id: uuid.UUID, payload: dict) -> bool` — returns `True` when `iat` is missing or `< revoked_at`; returns `False` on any Redis error (current fail-open).
   - Import `get_redis_client` at module level so tests can patch `app.core.session_revocation.get_redis_client`.
2. `app/core/dependencies.py`: replace lines 42-58 with `if await is_token_revoked(user_id, payload): raise HTTPException(401, "Session revoked. Please log in again.", headers=...)`.
3. `app/services/auth_service.py`: replace the Redis block in `change_password` with `await revoke_user_sessions(user.id, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)`. Keep the `redis_client` constructor argument working: if `self.redis` is set, pass it through (add optional `client` parameter to the helpers).
4. `app/services/admin_service.py`: `ban_user` → `await revoke_user_sessions(target_user_id, 86400 * 30)` at the same position (before commit); `unban_user` → `await clear_user_revocation(target_user_id)`.
5. Update patch targets in `app/tests/test_change_password_api.py:90-95` to `app.core.session_revocation.get_redis_client`. No assertion changes.

#### Files Touched
- `apps/api/app/core/session_revocation.py` (Created)
- `apps/api/app/core/dependencies.py` (Modified)
- `apps/api/app/services/auth_service.py` (Modified)
- `apps/api/app/services/admin_service.py` (Modified)
- `apps/api/app/tests/test_change_password_api.py` (Modified — patch targets only)

#### Verification Strategy
- Command: `make test-api && make lint-api && make typecheck-api`
- Every existing test passes with no assertion changes. `git diff --stat` shows no other files.

#### Prepared Git Commit
```text
refactor(api): consolidate session revocation into core module

- Add app/core/session_revocation.py with revoke_user_sessions,
  clear_user_revocation and is_token_revoked
- Replace duplicated Redis revocation blocks in dependencies,
  auth_service and admin_service with the shared helpers
- Retarget get_redis_client patches in change-password tests
- No functional change: key names, TTLs and fail-open behavior preserved
- Verification: make test-api, make lint-api, make typecheck-api passed
```
