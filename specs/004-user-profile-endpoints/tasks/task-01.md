### Task 01: SeaweedFS Docker Setup & Storage Settings

- [x] Completed

#### Full Description
Configure SeaweedFS as a lightweight, Apache 2.0-licensed S3-compatible storage service in `docker-compose.yml`, add `boto3` dependency to `apps/api/pyproject.toml`, and expose S3 settings in `app/core/config.py`, `.env.example`, and `.env`.

#### Technical Instructions
1. Add `seaweedfs` container service (`chrislusf/seaweedfs:latest`) with command `server -s3 -dir=/data` to `docker-compose.yml`. Expose port `8333` (S3 API). Mount volume `seaweedfs_data:/data`.
2. Add `seaweedfs_data:` under `volumes:` in `docker-compose.yml`.
3. Add `boto3>=1.35.0` to dependencies in `apps/api/pyproject.toml`.
4. Update `apps/api/app/core/config.py` with S3 configuration settings:
   - `S3_ENDPOINT_URL: str = "http://localhost:8333"`
   - `S3_ACCESS_KEY: str = "any"`
   - `S3_SECRET_KEY: str = "any"`
   - `S3_BUCKET_NAME: str = "avatars"`
   - `S3_PUBLIC_URL_PREFIX: str = "http://localhost:8333/avatars"`
   - `MAX_AVATAR_SIZE_BYTES: int = 5 * 1024 * 1024`
5. Update `.env.example` and `.env` with S3 defaults.

#### Files Touched
- `docker-compose.yml` (Modified)
- `apps/api/pyproject.toml` (Modified)
- `apps/api/app/core/config.py` (Modified)
- `.env.example` (Modified)
- `.env` (Modified)

#### Verification Strategy
```bash
apps/api/.venv/bin/python -c "from app.core.config import settings; assert settings.S3_ENDPOINT_URL == 'http://localhost:8333'; assert settings.S3_BUCKET_NAME == 'avatars'; print('S3 settings verified successfully')"
```

#### Prepared Git Commit
```text
feat(storage): configure seaweedfs s3 container and storage settings

- Add seaweedfs service with S3 API enabled to docker-compose.yml
- Add boto3 dependency in apps/api/pyproject.toml
- Define S3 storage configuration options in app/core/config.py
- Update .env and .env.example with S3 default endpoints
- Verification command passed: settings configuration load test
```
