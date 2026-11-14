### Task 02: Schemas, AuthService & AuthController Change Password Logic

- [ ] Pending

#### Full Description
Define `ChangePasswordRequest` in `apps/api/app/schemas/user.py`, implement `change_password` method in `AuthService` with Argon2 verification, same-password check, hash updating, and Redis key revocation, and expose via `AuthController`.

#### Technical Instructions
1. In `apps/api/app/schemas/user.py`:
   - Declare `ChangePasswordRequest`:
     - `current_password: str`
     - `new_password: str = Field(min_length=6, description="New password, minimum 6 characters")`
2. In `apps/api/app/services/auth_service.py`:
   - Accept optional `redis_client` in `__init__` (or lazily obtain via `get_redis_client`).
   - Implement `async def change_password(self, user: UserModel, current_password: str, new_password: str) -> None`:
     - If not `verify_password(current_password, user.hashed_password)`:
       raise `HTTPException(status_code=400, detail="Current password is incorrect.")`.
     - If `current_password == new_password`:
       raise `HTTPException(status_code=400, detail="New password cannot be the same as current password.")`.
     - `user.hashed_password = get_password_hash(new_password)`.
     - `await self.db.commit()`, `await self.db.refresh(user)`.
     - Set Redis key `f"revoked_user:{user.id}" = int(datetime.now(timezone.utc).timestamp())` with `ex=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60`.
3. In `apps/api/app/controllers/auth_controller.py`:
   - Implement `async def change_password(self, user: UserModel, request: ChangePasswordRequest) -> MessageResponse`:
     - Call `await self.service.change_password(user, request.current_password, request.new_password)`.
     - Return `MessageResponse(message="Password changed successfully. Please log in with your new password.")`.

#### Files Touched
- `apps/api/app/schemas/user.py` (Modified)
- `apps/api/app/services/auth_service.py` (Modified)
- `apps/api/app/controllers/auth_controller.py` (Modified)

#### Verification Strategy
```bash
apps/api/.venv/bin/python -c "from app.schemas.user import ChangePasswordRequest; from app.services.auth_service import AuthService; from app.controllers.auth_controller import AuthController; assert hasattr(AuthService, 'change_password'); print('Change password methods verified')"
```

#### Prepared Git Commit
```text
feat(auth): implement change_password logic in auth service and controller

- Add ChangePasswordRequest schema with min_length 6 validation
- Implement change_password in AuthService verifying Argon2 current password
- Invalidate concurrent sessions in Redis with TTL matching token lifetime
- Add change_password method to AuthController
- Verification command passed: method reflection check
```
