### Task 03: Profile Schemas & StorageService Integration

- [ ] Pending

#### Full Description
Define Pydantic schemas for user profile responses and partial updates in `apps/api/app/schemas/user.py`, and implement `StorageService` in `apps/api/app/services/storage_service.py` to handle S3 bucket verification and file uploads using `boto3`.

#### Technical Instructions
1. In `apps/api/app/schemas/user.py`:
   - Define `UserProfileResponse`:
     - `id: uuid.UUID`
     - `email: EmailStr`
     - `role: str`
     - `is_active: bool`
     - `full_name: str | None = None`
     - `avatar_url: str | None = None`
     - `bio: str | None = None`
     - `created_at: datetime | None = None`
     - `updated_at: datetime | None = None`
     - `model_config = ConfigDict(from_attributes=True)`
   - Define `UserProfileUpdate`:
     - `full_name: str | None = Field(None, max_length=100)`
     - `bio: str | None = Field(None, max_length=500)`
2. In `apps/api/app/services/storage_service.py`:
   - Initialize `boto3` client with endpoint URL, credentials, and region from `settings`.
   - Implement `upload_file(file_bytes: bytes, filename: str, content_type: str) -> str`:
     - Auto-check / create bucket if not existing.
     - Upload byte stream with `ContentType`.
     - Return public URL prefix + key.
     - Execute sync boto3 operations non-blockingly via `asyncio.to_thread`.

#### Files Touched
- `apps/api/app/schemas/user.py` (Modified)
- `apps/api/app/services/storage_service.py` (Created)

#### Verification Strategy
```bash
apps/api/.venv/bin/python -c "from app.schemas.user import UserProfileResponse, UserProfileUpdate; from app.services.storage_service import StorageService; print('Schemas and StorageService imported successfully')"
```

#### Prepared Git Commit
```text
feat(storage): create profile schemas and s3 storage service

- Add UserProfileResponse and UserProfileUpdate Pydantic models
- Implement StorageService wrapping boto3 S3 file upload logic
- Provide asynchronous non-blocking file streaming via asyncio.to_thread
- Verification command passed: schema and storage service import checks
```
