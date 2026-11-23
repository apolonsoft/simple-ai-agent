### Task 18: Remove Account-Enumeration Timing Signals

- [x] Completed

**Lesson:** [10 — Side channels: what response time reveals](../lessons/lesson-10-side-channels-and-enumeration.md)

#### Full Description
**MEDIUM.** Two endpoints reveal whether an email is registered through response time, despite generic messages:
- `forgot_password` (`app/controllers/auth_controller.py:43-46`) awaits the SMTP send (hundreds of ms) only when the account exists.
- `authenticate` (`app/services/auth_service.py:44-48`) skips Argon2 verification for unknown emails (~1 ms vs ~50+ ms).

Depends on Task 08 (async hashing).

#### Technical Instructions
1. **Failing tests first** in `app/tests/test_password_reset.py` and `test_auth_api.py`:
   - Patch `EmailService.send_password_reset_email` with an `AsyncMock`; assert it was **not awaited** within the request handler but scheduled as a background task (inspect via `BackgroundTasks` spy, or assert the response returns before a 1s mocked send finishes).
   - Patch `verify_password_async`; login with unknown email → called once (against the dummy hash).
2. `app/core/security.py`: `DUMMY_PASSWORD_HASH = password_hash.hash(secrets.token_urlsafe(16))` computed once at import.
3. `authenticate`:
   ```python
   user = await self.get_by_email(email)
   hashed = user.hashed_password if user else DUMMY_PASSWORD_HASH
   valid = await verify_password_async(password, hashed)
   return user if user and valid else None
   ```
4. `routes/auth_routes.py::forgot_password`: add `background_tasks: BackgroundTasks`; controller schedules `background_tasks.add_task(self.email_service.send_password_reset_email, email, raw_token)`. `send_password_reset_email` already catches and logs its own exceptions, so a failing SMTP server cannot raise inside the background task.
5. Token creation (DB insert) remains in-request; its cost is similar for both branches only if we also do a dummy query — not required (sub-ms difference, below network jitter). Document this decision in the commit body.

#### Files Touched
- `apps/api/app/core/security.py` (Modified)
- `apps/api/app/services/auth_service.py` (Modified)
- `apps/api/app/controllers/auth_controller.py` (Modified)
- `apps/api/app/routes/auth_routes.py` (Modified)
- `apps/api/app/tests/test_password_reset.py` (Modified)
- `apps/api/app/tests/test_auth_api.py` (Modified)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_password_reset.py app/tests/test_auth_api.py app/tests/test_auth_service.py -v && cd ../.. && make lint-api && make typecheck-api`

#### Prepared Git Commit
```text
fix(auth): remove timing signals that reveal registered emails

- Verify against a precomputed dummy hash when the login email is unknown
- Send password reset emails from a BackgroundTask so response time no
  longer depends on account existence
- Add tests for dummy verification and background email dispatch
- Remaining DB-insert timing delta is sub-millisecond and accepted
- Verification: pytest test_password_reset.py test_auth_api.py
  test_auth_service.py, make lint-api, make typecheck-api passed
```
