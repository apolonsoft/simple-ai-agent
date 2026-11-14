# Feature Specification: Backend API for Password Reset (Forgot Password)

## 1. Overview & Problem Statement
Users who forget their account passwords currently have no self-service recovery mechanism. This feature implements a secure, asynchronous 3-step password recovery flow allowing users to request a password reset email, verify the validity of their reset token, and securely establish a new password.

---

## 2. Clarifications & Architecture Decisions
- **Email Delivery Mechanism**: Full SMTP mailer service integration utilizing Mailpit for local development and testing, configured via environment variables.
- **Token Persistence & State**: Stored in PostgreSQL in a dedicated `password_resets` table with token hashing (SHA-256), managed via Alembic migrations, tracking expiration timestamps (`expires_at`), usage flag (`is_used`), and timestamps (`used_at`).
- **Endpoint Structure**:
  - `POST /api/v1/auth/forgot-password` (triggers reset email)
  - `GET /api/v1/auth/verify-reset-token` (validates token before displaying form)
  - `POST /api/v1/auth/reset-password` (updates password and consumes token)
- **Security & Privacy**:
  - Prevent user enumeration by returning a generic HTTP 200 message regardless of whether the email exists.
  - Strict Redis sliding window rate limiter (5 requests / 15 minutes) applied to `forgot-password`.
  - Raw tokens are never stored plaintext in PostgreSQL; only their SHA-256 digest is stored.

---

## 3. User Stories & Acceptance Criteria

### Story 1: Request Password Reset
**As a** registered user who forgot their password,
**I want to** submit my email to request a reset link,
**So that** I can securely regain access to my account.

- **Acceptance Criteria**:
  - `POST /api/v1/auth/forgot-password` accepts valid email JSON payload `{"email": "user@example.com"}`.
  - If the user exists and is active, a cryptographically secure random token is generated (32 bytes URL-safe), hashed with SHA-256, stored in `password_resets` with a 15-minute expiration, and an email is dispatched via SMTP/Mailpit containing the reset link.
  - If the user does not exist or is inactive, no email is sent, but the endpoint still returns HTTP 200 with the exact same generic message.
  - Rate limiting enforces a maximum of 5 requests per 15 minutes per IP. Exceeding requests return HTTP 429.

### Story 2: Verify Reset Token
**As a** frontend application,
**I want to** verify whether a reset token from a URL is valid and unexpired,
**So that** I can show the password reset form or display an "expired link" error before the user types anything.

- **Acceptance Criteria**:
  - `GET /api/v1/auth/verify-reset-token?token=...` checks if token exists, has not expired (`expires_at > now`), and has not been used (`is_used == False`).
  - Returns HTTP 200 `{"valid": true, "email": "user@example.com"}` if valid.
  - Returns HTTP 400 `{"detail": "Invalid or expired reset token"}` if invalid, expired, or already used.

### Story 3: Reset Password
**As a** user with a valid reset token,
**I want to** submit my new password,
**So that** my account password is updated and I can log in.

- **Acceptance Criteria**:
  - `POST /api/v1/auth/reset-password` accepts `{"token": "...", "new_password": "..."}`.
  - Validates password length and token validity.
  - Hashes new password with Argon2 and updates user record in PostgreSQL.
  - Marks the reset token as used (`is_used = True`, `used_at = now`).
  - Returns HTTP 200 with confirmation message.
  - Immediate subsequent login with the new password succeeds.
  - Old password no longer authenticates.
  - Reusing the same reset token returns HTTP 400.

---

## 4. Boundaries & Non-Goals
- **Frontend UI**: Angular component implementation is out of scope.
- **SMS / MFA Reset**: Multi-factor or SMS reset codes are out of scope.
- **Session Revocation**: Revoking active JWT tokens across all devices upon reset is out of scope.
