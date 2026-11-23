### Task 23: Docs, Shared Contracts and Full Verification

- [x] Completed

**Lessons:** all — use [`lessons/index.md`](../lessons/index.md) as the review checklist.

#### Full Description
Final gate. Bring documentation and shared contracts in line with the new behavior and run the full monorepo verification. No application logic changes.

#### Technical Instructions
1. `AGENT.md`:
   - §3.1 `core/security.py`: "Non-blocking" → "Async wrappers offload Argon2 to threads".
   - Invariant 4: clarify that fail-open applies to rate limiting and caching only; auth revocation is DB-backed.
   - Invariant 3: correct the approval endpoint path to `/api/v1/chats/{session_id}/tool-calls/approval` and document `pending → executing → executed|failed|rejected`.
   - §7 checklist: add "No `lazy='selectin'` relationships" and "No tokens in query strings".
2. `docs/ARCHITECTURE_AND_CODE_WALKTHROUGH.md`: update the revocation, cache and streaming sections.
3. Regenerate `shared/openapi.json`:
   `cd apps/api && .venv/bin/python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))" > ../../shared/openapi.json`
4. Sync `shared/types/api.ts` (`UserCreate` without `role`, pagination params, tool statuses).
5. Run `make format-api` and commit any formatting-only diff separately if large.
6. Tick every box in `tasks.md` and set every row in `tasks/index.md` to `Completed`.

#### Files Touched
- `AGENT.md` (Modified)
- `docs/ARCHITECTURE_AND_CODE_WALKTHROUGH.md` (Modified)
- `shared/openapi.json` (Modified)
- `shared/types/api.ts` (Modified)
- `specs/013-backend-audit-remediation/tasks.md`, `tasks/index.md` (Modified)

#### Verification Strategy
- Command: `make lint && make test-all && make build-web`
- Manual: `rg "lazy=\"selectin\"|X-Forwarded-For|revoked_user|query_token" apps/api/app` returns nothing.

#### Prepared Git Commit
```text
docs: document audit remediation and sync shared API contracts

- Update AGENT.md invariants for DB-backed revocation, tool status
  lifecycle and async hashing
- Update architecture walkthrough for streaming, cache and auth changes
- Regenerate shared/openapi.json and sync shared/types/api.ts
- Mark all spec 013 tasks completed
- Verification: make lint, make test-all, make build-web passed
```
