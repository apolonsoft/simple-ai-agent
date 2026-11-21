### Task 11: Move Token Revocation to PostgreSQL

- [ ] Pending

**Lesson:** [07 — Session revocation and fail-open vs fail-closed](../lessons/lesson-07-session-revocation-and-failure-modes.md)

#### Full Description
**HIGH + MEDIUM.** Current Redis-based revocation has four defects:
1. Fails open: any Redis error — including pool exhaustion at 50 connections — silently skips the check (`app/core/dependencies.py`, now `app/core/session_revocation.py` after Task 01).
2. `reset_password` (`app/services/auth_service.py:112-131`) revokes nothing, so an attacker's token survives account recovery; other unused reset tokens stay valid.
3. `change_password` silently skips writing the revocation if Redis is down.
4. `unban_user` deletes the key, re-validating tokens issued before a ban or a password change.

`get_current_user` already loads the `users` row, so a `tokens_valid_after` column gives reliable revocation with no extra query and no Redis dependency.

Depends on Task 01.

#### Technical Instructions
1. **Failing tests first**:
   - `test_password_reset.py`: token issued before reset → `401` after reset; second outstanding reset token → invalid after the first is used.
   - `test_change_password_api.py`: old token rejected with Redis patched to raise `ConnectionError`.
   - `test_admin_api.py`: token issued before ban → still `401` after unban; fresh login after unban works.
2. Migration `apps/api/alembic/versions/c7d8e9f0a1b2_add_tokens_valid_after_to_users.py` (`down_revision = "b1c2d3e4f5a6"`): add nullable `tokens_valid_after TIMESTAMPTZ`.
3. `app/models/user.py`: `tokens_valid_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)`.
4. Rewrite `app/core/session_revocation.py`:
   ```python
   def revoke_user_sessions(user: UserModel) -> None:
       user.tokens_valid_after = datetime.now(timezone.utc).replace(microsecond=0)

   def is_token_revoked(user: UserModel, payload: dict) -> bool:
       iat = payload.get("iat")
       if user.tokens_valid_after is None:
           return False
       return iat is None or int(iat) < int(user.tokens_valid_after.timestamp())
   ```
   Sync, no I/O — the caller commits. Delete `clear_user_revocation`.
5. `dependencies.get_current_user`: load the user first, then `if is_token_revoked(user, payload): raise 401`.
6. Callers (set before the existing `commit`):
   - `change_password`, `reset_password`, `ban_user` → `revoke_user_sessions(user)`.
   - `reset_password`: also `update(PasswordResetModel).where(user_id == ..., is_used.is_(False)).values(is_used=True, used_at=now)` in the same transaction.
   - `unban_user`: remove the revocation call entirely.
7. Remove Redis imports from `auth_service.py` and `admin_service.py`; drop the unused `redis_client` constructor argument from `AuthService` and its test usages.
8. Existing deployments: no backfill. Outstanding `revoked_user:*` keys expire on their own (max 30 days); note this in the commit body.

#### Files Touched
- `apps/api/alembic/versions/c7d8e9f0a1b2_add_tokens_valid_after_to_users.py` (Created)
- `apps/api/app/models/user.py` (Modified)
- `apps/api/app/core/session_revocation.py` (Modified)
- `apps/api/app/core/dependencies.py` (Modified)
- `apps/api/app/services/auth_service.py` (Modified)
- `apps/api/app/services/admin_service.py` (Modified)
- `apps/api/app/tests/test_password_reset.py`, `test_change_password_api.py`, `test_admin_api.py` (Modified)

#### Verification Strategy
- Command: `make migrate && make test-api && make lint-api && make typecheck-api`
- Manual: `cd apps/api && .venv/bin/alembic downgrade -1 && .venv/bin/alembic upgrade head` round-trips cleanly.

#### Prepared Git Commit
```text
fix(auth): store token revocation in PostgreSQL

- Add users.tokens_valid_after (migration c7d8e9f0a1b2) and compare it
  with the JWT iat in get_current_user
- Revoke sessions on change-password, reset-password and ban
- Invalidate all other outstanding reset tokens on successful reset
- Unban no longer re-validates tokens issued before the ban
- Remove Redis from the authentication path entirely
- Verification: make migrate, make test-api, make lint-api,
  make typecheck-api passed

Existing revoked_user:* Redis keys are no longer read and expire on
their own within 30 days.
```
