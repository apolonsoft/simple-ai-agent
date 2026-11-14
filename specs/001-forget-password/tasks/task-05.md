### Task 05: AuthController, API Routes & Comprehensive Tests

- [x] Completed

#### Full Description
Expose the 3 password reset endpoints in `AuthController` and `auth_routes.py` with sliding window rate limiting on forgot-password, wire up `EmailService`, and write comprehensive automated tests in `test_password_reset.py`.

#### Technical Instructions
1. Update `apps/api/app/controllers/auth_controller.py`:
   - Inject `EmailService` into `AuthController` (default instance).
   - Method `forgot_password(email: str) -> MessageResponse`:
     - Calls `service.create_password_reset(email)`.
     - If raw token generated, dispatches email via `email_service.send_password_reset_email(email, token)`.
     - Always returns uniform `MessageResponse(message="If an account with that email exists, a password reset link has been sent.")`.
   - Method `verify_reset_token(token: str) -> VerifyResetTokenResponse`:
     - Calls `service.verify_reset_token(token)`.
     - If None, raises `HTTPException(status_code=400, detail="Invalid or expired reset token")`.
     - Returns `VerifyResetTokenResponse(valid=True, email=reset_record.user.email)`.
   - Method `reset_password(token: str, new_password: str) -> MessageResponse`:
     - Calls `service.reset_password(token, new_password)`.
     - If False, raises `HTTPException(status_code=400, detail="Invalid or expired reset token")`.
     - Returns `MessageResponse(message="Password has been successfully reset.")`.
2. Update `apps/api/app/routes/auth_routes.py`:
   - `POST /forgot-password` with `RateLimiter(max_requests=5, window_seconds=900, scope="auth:forgot-password")`
   - `GET /verify-reset-token` with `token: str = Query(...)`
   - `POST /reset-password`
3. Create `apps/api/app/tests/test_password_reset.py`:
   - Test forgot-password returns 200 for existing user and invokes email delivery.
   - Test forgot-password returns 200 for non-existent user without error.
   - Test verify-reset-token succeeds with valid token.
   - Test verify-reset-token fails (400) with invalid or expired token.
   - Test reset-password succeeds, user can log in with new password, old password fails.
   - Test reset-password fails when reusing an already used token.
   - Test rate limiter triggers 429 when threshold exceeded.
4. Run Ruff formatting and lint check.

#### Files Touched
- `apps/api/app/controllers/auth_controller.py` (Modified)
- `apps/api/app/routes/auth_routes.py` (Modified)
- `apps/api/app/tests/test_password_reset.py` (Created)

#### Verification Strategy
```bash
apps/api/.venv/bin/pytest apps/api/app/tests/test_password_reset.py apps/api/app/tests/test_auth_api.py -v && apps/api/.venv/bin/ruff check apps/api
```

#### Prepared Git Commit
```text
feat(auth): add forgot-password, verify, and reset endpoints with tests

- Add forgot_password, verify_reset_token, and reset_password to AuthController
- Add endpoints to auth_routes with Redis sliding window rate limiting
- Wire EmailService to dispatch reset links to Mailpit / SMTP
- Add comprehensive unit and integration test suite in test_password_reset.py
- Verification command passed: all auth and reset tests pass, ruff clean
```
