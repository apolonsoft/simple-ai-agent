### Task 04: UserService, UserController, API Routes & Tests

- [ ] Pending

#### Full Description
Implement `UserService` and `UserController` for profile fetching, updates, and avatar uploads, expose endpoints under `/api/v1/users/me` (`GET`, `PATCH`, `POST /avatar`), and verify with automated pytest integration tests.

#### Technical Instructions
1. Implement `apps/api/app/services/user_service.py`:
   - `get_profile(user: UserModel) -> UserModel`
   - `update_profile(user: UserModel, profile_in: UserProfileUpdate) -> UserModel`
   - `upload_avatar(user: UserModel, file: UploadFile) -> UserModel`: Validate MIME type (`image/jpeg`, `image/png`, `image/webp`) and size limit (<= 5MB), upload via `StorageService`, update `user.avatar_url`.
2. Implement `apps/api/app/controllers/user_controller.py`:
   - Coordinate request parameters and return Pydantic schemas.
3. Implement `apps/api/app/routes/user_routes.py`:
   - `GET /me` -> `UserProfileResponse` (protected with `get_current_user`)
   - `PATCH /me` -> `UserProfileResponse`
   - `POST /me/avatar` -> `UserProfileResponse`
4. Register `user_routes.router` in `apps/api/app/main.py` under prefix `/users`.
5. Create `apps/api/app/tests/test_user_profile_api.py` covering:
   - Authenticated profile retrieval and 401 when unauthorized.
   - Profile update with validation edge cases.
   - Avatar upload success and rejection of invalid file types and oversized files.

#### Files Touched
- `apps/api/app/services/user_service.py` (Created)
- `apps/api/app/controllers/user_controller.py` (Created)
- `apps/api/app/routes/user_routes.py` (Created)
- `apps/api/app/main.py` (Modified)
- `apps/api/app/tests/test_user_profile_api.py` (Created)

#### Verification Strategy
```bash
cd apps/api && uv run pytest app/tests/test_user_profile_api.py -v && uv run ruff check .
```

#### Prepared Git Commit
```text
feat(users): implement user profile endpoints and comprehensive tests

- Add UserService and UserController for profile operations
- Expose GET, PATCH, and POST /me/avatar routes under /api/v1/users
- Register user router in main FastAPI application
- Add end-to-end integration tests verifying profile workflows and avatar upload constraints
- Verification command passed: pytest test_user_profile_api.py and ruff check
```
