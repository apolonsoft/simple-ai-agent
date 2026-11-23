### Task 17: Bound Avatar Uploads

- [x] Completed

**Lessons:** [06 — What actually blocks the event loop](../lessons/lesson-06-event-loop-blocking.md), [01 — Never trust the request body](../lessons/lesson-01-trust-boundaries-and-mass-assignment.md)

#### Full Description
**MEDIUM + LOW.**
- `UserService.upload_avatar` (`app/services/user_service.py:48`) calls `await file.read()`, loading the entire upload into memory before the 5 MB check. A multi-GB upload is fully buffered first.
- The object key extension comes from the client filename (`app/services/storage_service.py:57-62`) while `ContentType` comes from the client header; they can disagree (`avatar.html` with `image/png`).
- Upload errors return `str(e)` from boto3 (`storage_service.py:71`), leaking endpoint/bucket details.

#### Technical Instructions
1. **Failing test first** in `app/tests/test_user_profile_api.py`: patch `MAX_AVATAR_SIZE_BYTES` to 100, upload 10,000 bytes, and assert `UploadFile.read` was called with `size=101` (spy) and response is `400`.
2. `upload_avatar`: `file_bytes = await file.read(settings.MAX_AVATAR_SIZE_BYTES + 1)`; reject when `len(file_bytes) > MAX`.
3. Map extension from the validated content type: `{"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}`; pass it to `upload_file(..., extension=...)` and drop `original_filename` parsing.
4. Optional magic-byte check (cheap, no dependency): JPEG `FF D8 FF`, PNG `89 50 4E 47`, WebP `RIFF....WEBP`; reject mismatches with `400`.
5. `storage_service.upload_file`: log the exception with `logger.exception`, raise `HTTPException(502, "Avatar upload failed.")`.

#### Files Touched
- `apps/api/app/services/user_service.py` (Modified)
- `apps/api/app/services/storage_service.py` (Modified)
- `apps/api/app/tests/test_user_profile_api.py` (Modified)

#### Verification Strategy
- Command: `cd apps/api && .venv/bin/pytest app/tests/test_user_profile_api.py -v && cd ../.. && make lint-api && make typecheck-api`

#### Prepared Git Commit
```text
fix(users): bound avatar reads and derive extension from content type

- Read at most MAX_AVATAR_SIZE_BYTES + 1 bytes from the upload
- Derive the object extension from the validated content type and verify
  image magic bytes
- Return a generic 502 on storage failure and log the details
- Add bounded-read regression test
- Verification: pytest test_user_profile_api.py, make lint-api,
  make typecheck-api passed
```
