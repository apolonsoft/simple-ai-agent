# Feature Specification: User Change Password API with Redis Session Invalidation

## 1. Overview & Context
This specification outlines the backend requirements for an authenticated change-password endpoint (`POST /api/v1/auth/change-password`) with Redis-based distributed session revocation across concurrent devices.

## 2. User Stories
- **Change Password**: As an authenticated user, I want to change my account password by providing my current password and a new password, so that my account credentials remain secure.
- **Revoke Existing Sessions**: As an authenticated user changing my password, I want all active sessions across all devices to be immediately invalidated so that unauthorized or compromised devices cannot continue using old tokens.
- **Log In with New Password**: As an authenticated user whose password was changed, I want to be able to immediately log in with my new password and receive a valid session token.

## 3. Scope & Boundaries
- **In Scope**:
  - Embedding `iat` in JWT tokens in `app/core/security.py`.
  - Checking `revoked_user:{user_id}` in `get_current_user` dependency in `app/core/dependencies.py`.
  - `ChangePasswordRequest` schema validation (`current_password`, `new_password` min length 6).
  - Verifying `current_password` with Argon2, rejecting identical new passwords, updating hash, and setting Redis revocation timestamp in `AuthService`.
  - Rate limiting (5 requests per 60s) on `/api/v1/auth/change-password`.
  - Comprehensive automated pytest suite.
- **Out of Scope (Non-Goals)**:
  - Frontend UI for password change (deferred to separate frontend task).
  - Password complexity regex rules beyond length >= 6.
  - Email notification upon password change.

## 4. Acceptance Criteria
1. `POST /api/v1/auth/change-password` requires valid Bearer token; unauthenticated calls return HTTP 401.
2. If `current_password` does not match the user's stored Argon2 hash, return HTTP 400 ("Current password is incorrect.").
3. If `new_password` is identical to `current_password`, return HTTP 400 ("New password cannot be the same as current password.").
4. If `new_password` has fewer than 6 characters, return HTTP 422 Unprocessable Entity.
5. On valid change, update password hash in DB, record revocation timestamp in Redis (`revoked_user:{user.id}`), and return HTTP 200 with `MessageResponse`.
6. Any subsequent request made with a token issued prior to the revocation timestamp returns HTTP 401 ("Session revoked. Please log in again.").
7. Logging in with the new password generates a new token that authenticates successfully.
8. Exceeding 5 requests in 60s returns HTTP 429 Too Many Requests.
