### Task 04: Password Reset Schemas & AuthService Logic

- [ ] Pending

#### Full Description
Define the Pydantic request and response schemas for forgot-password and reset-password flows in `app/schemas/user.py`, and implement the password reset core methods in `app/services/auth_service.py`.

#### Technical Instructions
1. Update `apps/api/app/schemas/user.py`:
   - `ForgotPasswordRequest(BaseModel)`: `email: EmailStr`
   - `ResetPasswordRequest(BaseModel)`: `token: str`, `new_password: str`
   - `VerifyResetTokenResponse(BaseModel)`: `valid: bool`, `email: EmailStr | None = None`
   - `MessageResponse(BaseModel)`: `message: str`
2. Update `apps/api/app/services/auth_service.py`:
   - Add helper `_hash_token(token: str) -> str` using SHA-256 (`hashlib.sha256`).
   - `create_password_reset(email: str) -> str | None`:
     - Looks up user by email. If not found or inactive, returns `None`.
     - Generates random token (`secrets.token_urlsafe(32)`).
     - Insets `PasswordResetModel` with `token_hash`, `expires_at = now + settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`.
     - Commits and returns the raw token.
   - `verify_reset_token(raw_token: str) -> PasswordResetModel | None`:
     - Hashes raw token, queries `PasswordResetModel` where `token_hash == hash`, `is_used == False`, `expires_at > now`.
     - Returns model or `None`.
   - `reset_password(raw_token: str, new_password: str) -> bool`:
     - Validates token using `verify_reset_token`.
     - If invalid, returns `False`.
     - Updates user's `hashed_password` using `get_password_hash(new_password)`.
     - Marks reset record `is_used = True`, `used_at = now`.
     - Commits and returns `True`.

#### Files Touched
- `apps/api/app/schemas/user.py` (Modified)
- `apps/api/app/services/auth_service.py` (Modified)

#### Verification Strategy
```bash
apps/api/.venv/bin/pytest apps/api/app/tests/test_auth_api.py -v
```

#### Prepared Git Commit
```text
feat(auth): add password reset schemas and service methods

- Add ForgotPasswordRequest, ResetPasswordRequest, and VerifyResetTokenResponse schemas
- Implement token generation, SHA-256 token hashing, verification, and password reset in AuthService
- Enforce token single-use and expiration checks
- Verification command passed: existing auth tests pass
```
