# Master Task Roadmap: Backend Audit Remediation

| Task ID | Name | Severity | Lesson | Status | Spec File |
|---|---|---|---|---|---|
| `task-01` | Refactor session revocation into one module | Refactor | 07 | `Completed` | [`task-01-refactor-session-revocation.md`](./task-01-refactor-session-revocation.md) |
| `task-02` | Block role mass assignment and enforce password policy | CRITICAL | 01 | `Completed` | [`task-02-block-role-mass-assignment.md`](./task-02-block-role-mass-assignment.md) |
| `task-03` | Release DB connections before SSE streaming | CRITICAL | 02 | `Completed` | [`task-03-release-db-before-streaming.md`](./task-03-release-db-before-streaming.md) |
| `task-04` | Replace cascading eager loads with explicit loading | HIGH | 03 | `Completed` | [`task-04-explicit-orm-loading.md`](./task-04-explicit-orm-loading.md) |
| `task-05` | Authorize and lock tool-call approvals | HIGH | 04, 05 | `Completed` | [`task-05-tool-approval-authorization.md`](./task-05-tool-approval-authorization.md) |
| `task-06` | Sandbox PDF tool file access | HIGH | 08 | `Completed` | [`task-06-sandbox-pdf-tools.md`](./task-06-sandbox-pdf-tools.md) |
| `task-07` | Restrict PDF downloads to the owner | HIGH | 04, 08 | `Completed` | [`task-07-pdf-download-ownership.md`](./task-07-pdf-download-ownership.md) |
| `task-08` | Move blocking work off the event loop | HIGH | 06 | `Completed` | [`task-08-offload-blocking-work.md`](./task-08-offload-blocking-work.md) |
| `task-09` | Trust only real client IPs and make rate limiting atomic | HIGH | 09, 05 | `Completed` | [`task-09-rate-limiter-ip-and-atomicity.md`](./task-09-rate-limiter-ip-and-atomicity.md) |
| `task-10` | Refuse to start with a default secret key | HIGH | 09 | `Completed` | [`task-10-secret-key-guard.md`](./task-10-secret-key-guard.md) |
| `task-11` | Move token revocation to PostgreSQL | HIGH | 07 | `Completed` | [`task-11-db-token-revocation.md`](./task-11-db-token-revocation.md) |
| `task-12` | Enforce hierarchy on unban | MEDIUM | 04 | `Completed` | [`task-12-unban-hierarchy.md`](./task-12-unban-hierarchy.md) |
| `task-13` | Harden the Redis connection pool | MEDIUM | 07 | `Completed` | [`task-13-redis-pool-hardening.md`](./task-13-redis-pool-hardening.md) |
| `task-14` | Make the chat cache an atomic bounded list | MEDIUM | 11 | `Pending` | [`task-14-atomic-chat-cache.md`](./task-14-atomic-chat-cache.md) |
| `task-15` | Accept JWTs only from the Authorization header | MEDIUM | 07 | `Pending` | [`task-15-header-only-jwt.md`](./task-15-header-only-jwt.md) |
| `task-16` | Bound chat queries with pagination and windowed context | MEDIUM | 03 | `Pending` | [`task-16-bounded-chat-queries.md`](./task-16-bounded-chat-queries.md) |
| `task-17` | Bound avatar uploads | MEDIUM | 06, 01 | `Pending` | [`task-17-bounded-avatar-upload.md`](./task-17-bounded-avatar-upload.md) |
| `task-18` | Remove account-enumeration timing signals | MEDIUM | 10 | `Pending` | [`task-18-enumeration-timing.md`](./task-18-enumeration-timing.md) |
| `task-19` | Cache MCP tool definitions | MEDIUM | 06 | `Pending` | [`task-19-cache-mcp-tools.md`](./task-19-cache-mcp-tools.md) |
| `task-20` | Input limits and error hygiene | LOW | 01, 05 | `Pending` | [`task-20-input-limits-error-hygiene.md`](./task-20-input-limits-error-hygiene.md) |
| `task-21` | Gemini key header and admin search escaping | LOW | 09, 01 | `Pending` | [`task-21-gemini-header-search-escape.md`](./task-21-gemini-header-search-escape.md) |
| `task-22` | Persist partial replies on client disconnect | LOW | 02 | `Pending` | [`task-22-disconnect-safe-persistence.md`](./task-22-disconnect-safe-persistence.md) |
| `task-23` | Docs, shared contracts and full verification | Gate | all | `Pending` | [`task-23-docs-contracts-verification.md`](./task-23-docs-contracts-verification.md) |
