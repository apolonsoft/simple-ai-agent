### Task 20: Input Limits and Error Hygiene

- [x] Completed

**Lessons:** [01 — Never trust the request body](../lessons/lesson-01-trust-boundaries-and-mass-assignment.md), [05 — Check-then-act races](../lessons/lesson-05-check-then-act-races.md)

#### Full Description
**LOW.** Small, independent hardening items:
1. `ChatMessageCreate.content` (`app/schemas/chat.py:27`) has no maximum — unbounded rows, cache entries and LLM cost.
2. `AuthController.register` (`app/controllers/auth_controller.py:23-29`) checks then inserts; a concurrent duplicate hits the unique index (`ix_users_email`) and surfaces as `500`.
3. Internal error text reaches clients: `/health` (`app/main.py:61,71`), stream errors (`app/services/chat_stream_service.py:170`), provider error bodies (`app/providers/*`).

#### Technical Instructions
1. **Failing tests first**:
   - `test_chat_api.py`: 32,001-character message → `422`.
   - `test_auth_api.py`: patch `get_by_email` to return `None` for an existing email → register returns `409`, not `500`.
   - `test_health_api.py`: with DB patched to raise `RuntimeError("secret-host:5432")`, body does not contain `secret-host`.
2. `schemas/chat.py`: `content: str = Field(..., min_length=1, max_length=32_000)`.
3. `auth_service.register_user`: wrap `commit()` in `try/except IntegrityError` → `await self.db.rollback()` and raise `HTTPException(409, "Email is already registered.")`. Keep the pre-check for the common case.
4. `main.py`: report `"unhealthy"` without the exception; `logger.warning(..., exc_info=True)`.
5. `chat_stream_service.py`: SSE error payload becomes `{"error": "The assistant is temporarily unavailable."}` for unexpected exceptions; keep specific messages for `LLMAuthenticationError` / `LLMConnectionError` that contain no upstream body. Log full details.

#### Files Touched
- `apps/api/app/schemas/chat.py` (Modified)
- `apps/api/app/services/auth_service.py` (Modified)
- `apps/api/app/main.py` (Modified)
- `apps/api/app/services/chat_stream_service.py` (Modified)
- `apps/api/app/tests/test_chat_api.py`, `test_auth_api.py`, `test_health_api.py` (Modified)

#### Verification Strategy
- Command: `make test-api && make lint-api && make typecheck-api`

#### Prepared Git Commit
```text
fix(api): cap message size, map duplicate signup to 409, hide internals

- Limit chat message content to 32,000 characters
- Convert unique-email IntegrityError on registration into 409
- Stop returning exception text from /health and SSE error events;
  log details server-side instead
- Add tests for each case
- Verification: make test-api, make lint-api, make typecheck-api passed
```
