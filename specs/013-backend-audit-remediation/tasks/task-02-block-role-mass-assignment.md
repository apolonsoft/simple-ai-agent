### Task 02: Block Role Mass Assignment and Enforce Password Policy

- [x] Completed

**Lesson:** [01 — Never trust the request body](../lessons/lesson-01-trust-boundaries-and-mass-assignment.md)

#### Full Description
**CRITICAL.** `UserCreate.role` (`app/schemas/user.py:11`) is copied into the database by `AuthService.register_user` (`app/services/auth_service.py:36-37`). Anyone can `POST /api/v1/auth/register` with `"role": "super_admin"` and get full admin access.

Scope: remove the field, hard-code `role="user"`, and apply one password policy (min 8 chars) to register, reset and change-password. Tests that currently create admins through `/register` must create them through the DB instead.

#### Technical Instructions
1. **Write the failing test first** in `app/tests/test_auth_api.py`: register with `{"role": "super_admin"}` and assert the response and DB row have `role == "user"`.
2. `app/schemas/user.py`:
   - Delete `role` from `UserCreate`.
   - Add `PASSWORD_MIN_LENGTH = 8` and use `Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)` on `UserCreate.password`, `ResetPasswordRequest.new_password`, `ChangePasswordRequest.new_password`.
   - Leave `extra` at Pydantic's default (`ignore`) so old clients sending `role` don't break.
3. `app/services/auth_service.py::register_user`: construct `UserModel(email=..., hashed_password=..., role="user")`.
4. `app/tests/conftest.py`: add a `make_user` fixture that inserts a `UserModel` with any role directly via `TestingAsyncSessionLocal`, then logs in through the API and returns `(user_dict, token)`.
5. Update callers that relied on `role` in the register payload:
   - `app/tests/test_admin_api.py:10-30` helper → use `make_user`.
   - `app/tests/test_auth_api.py:98,115` → admin user via `make_user`.
   - `app/tests/test_auth_service.py:18,43` → drop `role` from `UserCreate`; set `user.role` on the model where an admin is needed.
   - Replace any test password shorter than 8 characters.
6. Frontend alignment (min length 8):
   - `apps/web/src/app/features/auth/register/register.component.ts:35`
   - `apps/web/src/app/features/auth/reset-password/reset-password.component.ts:27`
   - `apps/web/src/app/features/profile/profile.component.ts:40`
   - Do **not** change the login form validator.

#### Files Touched
- `apps/api/app/schemas/user.py` (Modified)
- `apps/api/app/services/auth_service.py` (Modified)
- `apps/api/app/tests/conftest.py` (Modified)
- `apps/api/app/tests/test_auth_api.py` (Modified)
- `apps/api/app/tests/test_admin_api.py` (Modified)
- `apps/api/app/tests/test_auth_service.py` (Modified)
- `apps/api/app/tests/test_password_reset.py`, `test_change_password_api.py` (Modified — password lengths only, if needed)
- `apps/web/src/app/features/auth/register/register.component.ts` (Modified)
- `apps/web/src/app/features/auth/reset-password/reset-password.component.ts` (Modified)
- `apps/web/src/app/features/profile/profile.component.ts` (Modified)

#### Verification Strategy
- Command: `make test-api && make test-web && make lint-api && make typecheck-api`
- New test: `cd apps/api && .venv/bin/pytest app/tests/test_auth_api.py -k role -v` fails before step 2 and passes after.

#### Prepared Git Commit
```text
fix(auth)!: ignore client-supplied role on registration

- Remove role from UserCreate; register_user always stores role="user"
- Enforce 8-128 character passwords on register, reset and change-password
- Add make_user test fixture that creates privileged users via the DB
- Migrate admin and auth tests off role-in-register payloads
- Align frontend password validators to the new minimum
- Verification: make test-api, make test-web, make lint-api,
  make typecheck-api passed

BREAKING CHANGE: /auth/register no longer honors the role field.
Admins must be created with scripts/manage_admin.py or the admin API.
Passwords shorter than 8 characters are rejected with 422.
```
