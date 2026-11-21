# Technical Architecture Plan: Backend Audit Remediation

## 1. Architecture Overview
The remediation keeps the existing route → controller → service layering and changes behavior in four places:

1. **Request lifetime**: stream routes release their request-scoped DB session before returning `EventSourceResponse`; `ChatStreamService` never holds a session across LLM or tool I/O (restores `AGENT.md` invariant 1).
2. **Auth state**: token revocation moves from Redis keys (`revoked_user:{id}`) to a `users.tokens_valid_after` column. `get_current_user` already loads the user row, so this costs no extra query and removes Redis from the auth path.
3. **Tool safety**: tool approvals are bound to the session, locked with `SELECT ... FOR UPDATE`, and only run from `pending`. PDF tools are confined to the output directory and downloads are restricted to files referenced in the caller's own sessions.
4. **Redis**: one hardened pool (timeouts, blocking pool); chat cache becomes an atomically appended, trimmed list; rate limiter becomes a single atomic pipeline keyed on the real client IP.

Execution order follows severity, preceded by one zero-behavior-change refactor (rule `single-file-tasks.md` §2).

---

## 2. Affected Files & Schema

### Database Layer
- **Model**: `apps/api/app/models/user.py`
  - `tokens_valid_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)`
  - `chat_sessions`, `password_resets` → `lazy="raise"`
- **Model**: `apps/api/app/models/chat.py`
  - `ChatSessionModel.messages` → `lazy="raise"`
- **Migration**: `apps/api/alembic/versions/c7d8e9f0a1b2_add_tokens_valid_after_to_users.py` (down_revision `b1c2d3e4f5a6`, the current head)

### Core
- `app/core/config.py`: `SECRET_KEY` production validator.
- `app/core/security.py`: `hash_password_async`, `verify_password_async`, `DUMMY_PASSWORD_HASH`.
- `app/core/session_revocation.py` (**new**, Task 01): `revoke_user_sessions(user)`, `is_token_revoked(user, payload)`.
- `app/core/dependencies.py`: header-only token; DB-based revocation.
- `app/core/redis.py`: `BlockingConnectionPool` with timeouts.
- `app/core/rate_limiter.py`: atomic pipeline; no `X-Forwarded-For` parsing.

### Services
- `auth_service.py`: async hashing, dummy-hash login, revocation on reset, invalidate sibling reset tokens, `IntegrityError` → 409.
- `admin_service.py`: DB revocation on ban, unban hierarchy, no revocation deletion, escaped search.
- `chat_service.py`: `get_session_with_messages`, `get_recent_messages`, paginated lists, locked tool-call lookup.
- `chat_stream_service.py`: session-bound approvals, status check, release DB before tools, thread offload, disconnect-safe persistence.
- `chat_cache_service.py`: Redis list implementation.
- `mcp_client_service.py`: 60s TTL cache for tool definitions.
- `storage_service.py`: process-wide lazy boto3 client; generic errors.
- `user_service.py`: bounded avatar read; extension from content type.
- `controllers/auth_controller.py`: forgot-password email via `BackgroundTasks`.

### Tools
- `app/mcp_servers/pdf_server.py`: `_resolve_in_output_dir()`; random filename suffix; no overwrite.
- `app/providers/gemini_provider.py`: API key header.

### Routes & Schemas
- `routes/chat_routes.py`: close session before streaming; pagination params; PDF ownership check.
- `routes/auth_routes.py`: `BackgroundTasks` for forgot-password.
- `schemas/user.py`: remove `UserCreate.role`; password `min_length=8`.
- `schemas/chat.py`: `content` `max_length=32000`.
- `main.py`: generic health errors.

### Frontend (validator alignment only)
- `apps/web/src/app/features/auth/register/register.component.ts`
- `apps/web/src/app/features/auth/reset-password/reset-password.component.ts`
- `apps/web/src/app/features/profile/profile.component.ts`

### Ops / Docs
- `Makefile`, `dev.sh`: uvicorn `--proxy-headers --forwarded-allow-ips "$FORWARDED_ALLOW_IPS"`.
- `.env.example`: `FORWARDED_ALLOW_IPS`, `SECRET_KEY` guidance.
- `AGENT.md`, `docs/ARCHITECTURE_AND_CODE_WALKTHROUGH.md`, `shared/openapi.json`, `shared/types/api.ts`.

### Dependencies
No new packages. Uses `redis.asyncio.BlockingConnectionPool`, `asyncio.to_thread`, `fastapi.BackgroundTasks`, `sqlalchemy.exc.IntegrityError`.

---

## 3. Testing Strategy
Every task adds a regression test that fails on the current code before the fix (write the test first).

| Area | Test file | New tests |
|---|---|---|
| Registration | `test_auth_api.py` | `role` in body is ignored; short password → 422; duplicate race → 409 |
| Fixtures | `conftest.py` | `make_user(role=...)` creates admins via DB, replacing `role` in register payloads |
| Pool pinning | `test_chat_stream.py` | Fake provider asserts `engine.pool.checkedout() == 0` mid-stream (Postgres-only; skipped on SQLite) and session `is_active` / `in_transaction()` is False |
| Eager loading | `test_async_database.py` | SQL statement counter on `get_current_user` == 1 |
| Tool approval | `test_calculator_tools.py` | Foreign `message_id` → error; second approval → error; concurrent approvals execute once |
| PDF | `test_pdf_server.py`, `test_pdf_download_api.py` | Path outside dir rejected; filename collision avoided; other user's PDF → 404 |
| Event loop | `test_auth_service.py` | `verify_password_async` runs via `asyncio.to_thread` (patched) |
| Rate limiter | `test_rate_limiter.py` | Spoofed `X-Forwarded-For` shares one bucket; N concurrent requests admit exactly `max_requests` |
| Config | new `test_config.py` | Production + default key raises `ValidationError` |
| Revocation | `test_change_password_api.py`, `test_password_reset.py`, `test_admin_api.py` | Old token rejected after reset; still rejected after ban→unban; admin can't unban admin; works with Redis down |
| Redis | `test_chat_cache.py` | Concurrent appends keep all messages; list trimmed to window |
| Queries | `test_chat_api.py` | `limit`/`before` pagination; context fetch uses LIMIT |
| Leaks | `test_auth_api.py`, `test_health_api.py` | `?token=` rejected; health hides exception text |
| Streaming | `test_chat_stream.py` | Cancelled generator still persists partial reply |

Per-task gate: the task's targeted pytest command, then `make lint-api && make typecheck-api`. Final gate (Task 23): `make test-all`.

---

## 4. Non-Goals
See `spec.md` §4.
