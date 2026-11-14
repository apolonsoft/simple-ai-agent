# Technical Architecture & Implementation Plan: Change Password API

## 1. Architecture Overview
- **JWT Issued-At (iat)**:
  - `create_access_token` attaches `"iat": int(now.timestamp())`.
- **Session Revocation Mechanism**:
  - Redis key: `revoked_user:{user_id} = <unix_timestamp>`.
  - In `get_current_user` dependency:
    - Reads `revoked_user:{user_id}` from Redis.
    - If present and token `iat < int(revoked_timestamp)`, rejects token with 401 Unauthorized.
- **Service & Controller**:
  - `AuthService.change_password` validates current password, verifies new != current, updates Argon2 hash in DB, and sets `revoked_user:{user_id}` in Redis with TTL = `ACCESS_TOKEN_EXPIRE_MINUTES * 60`.
  - `AuthController.change_password` wraps service call and returns `MessageResponse`.
- **Endpoint**:
  - `POST /api/v1/auth/change-password` guarded by `RateLimiter(5, 60)` and `get_current_user`.

## 2. Affected Files
- `apps/api/app/core/security.py` (Modified)
- `apps/api/app/core/dependencies.py` (Modified)
- `apps/api/app/schemas/user.py` (Modified)
- `apps/api/app/services/auth_service.py` (Modified)
- `apps/api/app/controllers/auth_controller.py` (Modified)
- `apps/api/app/routes/auth_routes.py` (Modified)
- `apps/api/app/tests/test_change_password_api.py` (Created)
