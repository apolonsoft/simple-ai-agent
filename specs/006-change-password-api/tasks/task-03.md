### Task 03: API Route & Comprehensive Pytest Test Suite

- [ ] Pending

#### Full Description
Expose `POST /api/v1/auth/change-password` in `apps/api/app/routes/auth_routes.py` with rate limiting and `get_current_user` dependency, and create a comprehensive pytest suite in `apps/api/app/tests/test_change_password_api.py`.

#### Technical Instructions
1. In `apps/api/app/routes/auth_routes.py`:
   - Add endpoint `POST /change-password`:
     - Dependencies: `RateLimiter(max_requests=5, window_seconds=60, scope="auth:change-password")`.
     - Parameters: `request_data: ChangePasswordRequest`, `current_user: UserModel = Depends(get_current_user)`, `controller: AuthController = Depends(get_auth_controller)`.
     - Returns `MessageResponse`.
2. In `apps/api/app/tests/test_change_password_api.py`:
   - `test_change_password_unauthorized`: Calling without Bearer token returns 401.
   - `test_change_password_success`: Successful change returns 200.
   - `test_change_password_revokes_old_token`: Subsequent request with the token used to change password returns 401 ("Session revoked. Please log in again.").
   - `test_login_with_new_password_success`: Login with new password succeeds and authenticates cleanly.
   - `test_change_password_incorrect_current_password`: Returns 400 Bad Request.
   - `test_change_password_same_password_rejected`: Returns 400 Bad Request.
   - `test_change_password_length_validation`: Length < 6 returns 422.
   - `test_change_password_rate_limiting`: Exceeding 5 requests in 60s returns 429.

#### Files Touched
- `apps/api/app/routes/auth_routes.py` (Modified)
- `apps/api/app/tests/test_change_password_api.py` (Created)

#### Verification Strategy
```bash
apps/api/.venv/bin/pytest apps/api/app/tests/test_change_password_api.py -v && apps/api/.venv/bin/ruff check .
```

#### Prepared Git Commit
```text
feat(auth): expose change-password endpoint and add comprehensive tests

- Add POST /api/v1/auth/change-password route with RateLimiter and get_current_user
- Add tests covering password change, session revocation, and security boundaries
- Verification command passed: pytest test_change_password_api.py and ruff check
```
