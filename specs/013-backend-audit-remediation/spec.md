# Feature Specification: Backend Audit Remediation

## 1. Overview
This specification covers the fixes for the findings of the staff-level backend audit of `apps/api` (FastAPI, SQLAlchemy async, PostgreSQL, Redis). It closes 2 critical, 7 high, 9 medium and 7 low findings across authorization, connection-pool lifetime, ORM loading, event-loop blocking, session revocation, Redis cache correctness, and agent-tool sandboxing.

Every fix is paired with a mentoring lesson in [`lessons/`](./lessons/index.md) that explains the underlying pattern, so the fixes double as a learning path.

---

## 2. User Stories & Acceptance Criteria

### US-1: No self-service privilege escalation (CRITICAL)
- **As a** platform operator, **I want** registration to always create a plain `user`, **so that** nobody can make themselves an admin.
- **Acceptance Criteria**:
  - `POST /api/v1/auth/register` ignores any `role` field and always stores `role="user"`.
  - Admins can only be created through `scripts/manage_admin.py` or `PATCH /admin/users/{id}/role`.
  - Register and reset-password enforce the same password policy as change-password (minimum 8 characters).

### US-2: Streaming never pins a database connection (CRITICAL)
- **As an** operator, **I want** SSE chat streams to hold zero DB connections during LLM inference and tool execution, **so that** concurrent chats cannot exhaust the pool.
- **Acceptance Criteria**:
  - The request-scoped `AsyncSession` used by `/stream` and `/tool-calls/approval` is closed before `EventSourceResponse` is returned.
  - `stream_tool_approval` releases its session before running a tool and opens a fresh one to persist the result.
  - A test proves no connection is checked out while the provider is generating.

### US-3: Authenticated requests do not load chat history (HIGH)
- **Acceptance Criteria**:
  - `UserModel.chat_sessions`, `UserModel.password_resets` and `ChatSessionModel.messages` default to `lazy="raise"`.
  - Only `GET /chats/{id}` eagerly loads messages, via an explicit `selectinload`.
  - `get_current_user` issues exactly one SQL statement.

### US-4: Tool approvals are authorized and run at most once (HIGH + MEDIUM)
- **Acceptance Criteria**:
  - A `message_id` that does not belong to the path `session_id` is treated as not found.
  - A tool call whose status is not `pending` cannot be approved or rejected again (`409`-style SSE `error` event).
  - Concurrent approvals of the same tool call execute the tool exactly once (row lock).

### US-5: Agent PDF tools are sandboxed and files are private (HIGH)
- **Acceptance Criteria**:
  - `inspect_pdf` and `merge_pdfs` reject any path outside the PDF output directory.
  - Generated filenames always contain a random component; user-supplied names cannot overwrite existing files.
  - `GET /chats/files/pdf/{filename}` returns `404` unless the file is referenced by a tool result in one of the caller's own sessions.

### US-6: The event loop is never blocked (HIGH + MEDIUM)
- **Acceptance Criteria**:
  - Argon2 hash/verify, local tool execution, and S3 uploads run in worker threads.
  - The boto3 client is created once per process, not per request.

### US-7: Abuse controls cannot be bypassed (HIGH + LOW)
- **Acceptance Criteria**:
  - The rate limiter identifies clients by `request.client.host`; `X-Forwarded-For` is honored only through uvicorn's `--forwarded-allow-ips`.
  - The sliding-window check and the insert happen atomically (no burst past `max_requests`).

### US-8: Safe production configuration (HIGH + LOW)
- **Acceptance Criteria**:
  - The app refuses to start when `ENVIRONMENT` is not `development`/`test` and `SECRET_KEY` is the default or shorter than 32 characters.
  - The Gemini API key is sent in the `x-goog-api-key` header, never in the URL.

### US-9: Session revocation is reliable (HIGH + MEDIUM)
- **Acceptance Criteria**:
  - Revocation is stored in PostgreSQL (`users.tokens_valid_after`), not Redis, so it works when Redis is down or saturated.
  - Change-password, reset-password and ban all revoke existing tokens.
  - Reset-password invalidates all other outstanding reset tokens for that user.
  - Unban never re-validates tokens issued before the ban.
  - Unban enforces the same hierarchy rules as ban.

### US-10: Redis is bounded, fast-failing and consistent (MEDIUM)
- **Acceptance Criteria**:
  - The Redis pool has connect/read timeouts and waits for a free connection instead of erroring.
  - Chat history cache is a Redis list, appended atomically and trimmed to `CHAT_MEMORY_WINDOW_SIZE`.

### US-11: Bounded queries and inputs (MEDIUM + LOW)
- **Acceptance Criteria**:
  - Session and message list endpoints accept `limit` (default 100, max 200) and a `before` cursor; existing clients keep working unchanged.
  - LLM context is fetched with `ORDER BY created_at DESC LIMIT window`.
  - Chat message content is capped at 32,000 characters.
  - Avatar uploads are read with a bounded `read()`; the stored extension is derived from the content type.

### US-12: No information leaks (MEDIUM + LOW)
- **Acceptance Criteria**:
  - JWTs are accepted only from the `Authorization` header.
  - Forgot-password response time does not depend on whether the email exists (email sent in a background task).
  - Login performs an Argon2 verification even for unknown emails.
  - `/health`, storage, and stream errors return generic messages; details go to logs only.
  - Duplicate registration races return `409`, never `500`.

### US-13: Lower-latency, resilient streaming (MEDIUM + LOW)
- **Acceptance Criteria**:
  - MCP tool definitions are cached in-process for 60 seconds.
  - If the client disconnects mid-stream, the partial assistant reply is still persisted.
  - Admin search escapes `%` and `_` in the search term.

---

## 3. Clarifications & Assumptions
The audit asked three questions that are still open. Until answered, the plan assumes:

| Question | Assumption used in this plan |
|---|---|
| Is there a reverse proxy in front of uvicorn, and does it overwrite `X-Forwarded-For`? | Yes, a single trusted proxy. Task 09 uses uvicorn `--proxy-headers --forwarded-allow-ips` configured by env var `FORWARDED_ALLOW_IPS`. |
| Workers / replicas / Postgres `max_connections`? | Unknown. Pool settings are left unchanged; Task 03 removes the pinning that made sizing critical. |
| Are MCP servers always deployed in production? | No. The in-process tool fallback stays, so it must be sandboxed (Task 06) and non-blocking (Task 08). |
| Password minimum length? | 8 characters on register, reset and change-password; frontend validators updated to match. |
| Is Redis-based revocation required by `AGENT.md` invariant 4 (fail-open)? | Fail-open stays for rate limiting and caching. Revocation moves to PostgreSQL, which is already queried on every request, so no fail-open trade-off remains for auth. |

---

## 4. Boundaries & Non-Goals
- **Non-Goal**: Replacing `HTTPException` in services with domain exceptions. Noted as tech debt; too broad for this effort.
- **Non-Goal**: Refresh tokens, token rotation, or moving JWTs out of `localStorage`.
- **Non-Goal**: Changing pool sizing or deployment topology.
- **Non-Goal**: A `generated_files` ownership table. Ownership is derived from existing chat messages (Task 07).
- **Non-Goal**: Full-text / trigram indexes for admin search.
- **Non-Goal**: Frontend changes beyond password-validator alignment and removing nothing the UI depends on.
