### Task 01: Core Security JWT Issued-At & Redis Session Invalidation Dependency

- [x] Completed

#### Full Description
Update `create_access_token` in `apps/api/app/core/security.py` to embed `iat` timestamp in JWT payloads, and update `get_current_user` in `apps/api/app/core/dependencies.py` to check `revoked_user:{user_id}` in Redis and reject any token issued before the revocation timestamp.

#### Technical Instructions
1. In `apps/api/app/core/security.py`:
   - In `create_access_token`:
     - Calculate `now = datetime.now(timezone.utc)`.
     - Update payload with `"iat": int(now.timestamp())`.
     - Update `"exp"` using `now + expires_delta`.
2. In `apps/api/app/core/dependencies.py`:
   - Inject Redis dependency or use `get_redis_client()` from `app.core.redis`.
   - After decoding access token:
     - Check if Redis has key `f"revoked_user:{user_id}"`.
     - If `revoked_at` is set in Redis and token `payload.get("iat")` is missing or `< int(revoked_at)`:
       - Raise `HTTPException(status_code=401, detail="Session revoked. Please log in again.", headers={"WWW-Authenticate": "Bearer"})`.

#### Files Touched
- `apps/api/app/core/security.py` (Modified)
- `apps/api/app/core/dependencies.py` (Modified)

#### Verification Strategy
```bash
apps/api/.venv/bin/python -c "from app.core.security import create_access_token, decode_access_token; t = create_access_token({'sub': 'test-sub'}); p = decode_access_token(t); assert 'iat' in p; print('JWT iat verified successfully')"
```

#### Prepared Git Commit
```text
feat(security): embed iat in jwt and add redis session revocation check

- Add iat timestamp to access token generation in core/security.py
- Add Redis revoked_user check in get_current_user dependency
- Invalidate tokens issued prior to user's revocation timestamp
- Verification command passed: token iat decoding test
```
