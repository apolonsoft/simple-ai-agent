### Task 03: Asynchronous Email Service (SMTP / Mailpit)

- [ ] Pending

#### Full Description
Implement an asynchronous email dispatch service (`EmailService`) that connects via SMTP to Mailpit (or configured production SMTP server) to send password reset emails with HTML and plain-text multipart templates.

#### Technical Instructions
1. Create `apps/api/app/services/email_service.py`:
   - Initialize with `settings` (or custom parameters).
   - Method `send_password_reset_email(recipient_email: str, reset_token: str) -> bool`:
     - Builds multipart email (`email.message.EmailMessage`) with both plain-text and HTML formatting containing the reset link (`f"{settings.FRONTEND_RESET_URL}?token={reset_token}"`).
     - Executes synchronous `smtplib.SMTP` in a background worker thread via `asyncio.to_thread` to prevent blocking FastAPI's event loop.
     - Supports optional STARTTLS (`settings.SMTP_USE_TLS`) and optional authentication (`settings.SMTP_USERNAME`/`PASSWORD`).
     - Includes robust error handling and logging without crashing calling processes if the mail server is temporarily unavailable.
2. Export `EmailService` from `apps/api/app/services/__init__.py`.

#### Files Touched
- `apps/api/app/services/email_service.py` (Created)
- `apps/api/app/services/__init__.py` (Modified)

#### Verification Strategy
```bash
apps/api/.venv/bin/python -c "from app.services.email_service import EmailService; s = EmailService(); print('EmailService loaded successfully')"
```

#### Prepared Git Commit
```text
feat(email): implement asynchronous SMTP email service

- Create EmailService with multipart HTML/plain-text templates for password reset
- Use asyncio.to_thread with smtplib to keep event loop unblocked
- Add graceful error handling and configuration support for Mailpit and TLS
- Verification command passed: service import and initialization check
```
