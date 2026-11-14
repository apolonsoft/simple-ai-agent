### Task 01: Mailpit Docker Setup & Core Configuration

- [x] Completed

#### Full Description
Configure Mailpit as a local email testing server inside `docker-compose.yml` and declare the necessary SMTP and password-reset configuration variables in `apps/api/app/core/config.py`, `.env.example`, and `.env`.

#### Technical Instructions
1. Add `mailpit` container service (`axllent/mailpit:latest`) to `docker-compose.yml` exposing ports `1025` (SMTP) and `8025` (Web UI).
2. Update `.env.example` and `.env` with SMTP configuration variables:
   - `SMTP_HOST=localhost`
   - `SMTP_PORT=1025`
   - `SMTP_USERNAME=`
   - `SMTP_PASSWORD=`
   - `SMTP_FROM_EMAIL=noreply@example.com`
   - `SMTP_USE_TLS=false`
   - `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=15`
   - `FRONTEND_RESET_URL=http://localhost:4200/reset-password`
3. Update `apps/api/app/core/config.py` `Settings` class with these fields and default values.

#### Files Touched
- `docker-compose.yml` (Modified)
- `.env.example` (Modified)
- `.env` (Modified)
- `apps/api/app/core/config.py` (Modified)

#### Verification Strategy
```bash
apps/api/.venv/bin/python -c "from app.core.config import settings; assert settings.SMTP_PORT == 1025; assert settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES == 15; print('Config verified successfully')"
```

#### Prepared Git Commit
```text
feat(config): add mailpit container and smtp configuration

- Add mailpit service (axllent/mailpit:latest) to docker-compose.yml
- Add SMTP and password reset settings to app/core/config.py
- Update .env and .env.example with mailpit default values
- Verification command passed: settings configuration load test
```
