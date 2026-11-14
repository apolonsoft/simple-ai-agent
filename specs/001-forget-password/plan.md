# Technical Architecture & Implementation Plan: Password Reset API

## 1. System Architecture

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend as Web Client
    participant AuthRoutes as Auth API Router
    participant Controller as AuthController
    participant Service as AuthService
    participant Email as EmailService
    participant DB as PostgreSQL
    participant Mailpit as Mailpit (SMTP :1025)

    %% Flow 1: Request
    User->>Frontend: Submit Forgot Password Form
    Frontend->>AuthRoutes: POST /api/v1/auth/forgot-password
    Note over AuthRoutes: RateLimiter (5 req / 15 min)
    AuthRoutes->>Controller: forgot_password(request)
    Controller->>Service: initiate_password_reset(email)
    Service->>DB: Query user by email
    alt User exists & active
        Service->>DB: Insert PasswordResetModel (token_hash, expires_at)
        Service->>Email: send_reset_email(email, raw_token)
        Email->>Mailpit: SMTP Send (port 1025)
    end
    Service-->>Controller: Completed
    Controller-->>AuthRoutes: MessageResponse
    AuthRoutes-->>Frontend: 200 OK (Generic anti-enumeration message)

    %% Flow 2: Verify
    User->>Frontend: Clicks link (?token=XYZ)
    Frontend->>AuthRoutes: GET /api/v1/auth/verify-reset-token?token=XYZ
    AuthRoutes->>Controller: verify_reset_token(token)
    Controller->>Service: validate_reset_token(token)
    Service->>DB: Check token_hash, expires_at, is_used
    alt Valid & Active
        Service-->>Controller: (valid=true, email=user.email)
        Controller-->>Frontend: 200 OK
    else Invalid / Expired / Used
        Service-->>Controller: None
        Controller-->>Frontend: 400 Bad Request
    end

    %% Flow 3: Reset
    User->>Frontend: Enter New Password & Submit
    Frontend->>AuthRoutes: POST /api/v1/auth/reset-password (token, new_password)
    AuthRoutes->>Controller: reset_password(token, new_password)
    Controller->>Service: execute_password_reset(token, new_password)
    Service->>DB: Update user.hashed_password & reset_token.is_used=true
    Controller-->>Frontend: 200 OK ("Password successfully reset")
```

---

## 2. Affected Files & Schemas

### Infrastructure & Config
- `docker-compose.yml`: Adds `mailpit` container service (`axllent/mailpit:latest` on ports 1025 and 8025).
- `.env.example` / `.env`: Sets `SMTP_HOST=localhost`, `SMTP_PORT=1025`, `SMTP_FROM_EMAIL=noreply@example.com`, `SMTP_USE_TLS=false`, `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=15`.
- `apps/api/app/core/config.py`: Adds SMTP and reset token configuration attributes to Pydantic `Settings`.

### Database & Models
- `apps/api/app/models/password_reset.py`: Defines `PasswordResetModel` inheriting `Base` and `TimestampMixin`.
- `apps/api/app/models/user.py`: Adds `password_resets` one-to-many relationship with cascade delete.
- `apps/api/app/models/__init__.py`: Exports `PasswordResetModel`.
- `apps/api/alembic/versions/*_create_password_resets_table.py`: Database migration.

### Services & Schemas
- `apps/api/app/services/email_service.py`: `EmailService` utilizing `smtplib.SMTP` in `asyncio.to_thread` for asynchronous email dispatch.
- `apps/api/app/schemas/user.py`: Pydantic models `ForgotPasswordRequest`, `ResetPasswordRequest`, `VerifyResetTokenResponse`, `MessageResponse`.
- `apps/api/app/services/auth_service.py`: Methods for generating, hashing, storing, verifying tokens, and updating user passwords.
- `apps/api/app/controllers/auth_controller.py`: Controller methods coordinating service calls and HTTP exceptions.
- `apps/api/app/routes/auth_routes.py`: Exposing endpoints with rate limiting.

### Tests
- `apps/api/app/tests/test_password_reset.py`: Unit and end-to-end integration tests for all 3 endpoints, edge cases, expiration, and rate limiting.

---

## 3. Dependencies
- Standard library: `hashlib` (SHA-256 for token hashing), `secrets` (cryptographically strong token generation), `smtplib` + `email.message.EmailMessage` (SMTP email building and delivery).
- No new external pip packages required; utilizes existing async framework, Pydantic, SQLAlchemy, and Redis.
