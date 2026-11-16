# app/services/email_service.py
import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Asynchronous SMTP email service designed for transactional emails (e.g., Mailpit/SMTP)."""

    def __init__(
        self,
        smtp_host: str = settings.SMTP_HOST,
        smtp_port: int = settings.SMTP_PORT,
        smtp_username: str = settings.SMTP_USERNAME,
        smtp_password: str = settings.SMTP_PASSWORD,
        smtp_from_email: str = settings.SMTP_FROM_EMAIL,
        smtp_use_tls: bool = settings.SMTP_USE_TLS,
        frontend_reset_url: str = settings.FRONTEND_RESET_URL,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.smtp_from_email = smtp_from_email
        self.smtp_use_tls = smtp_use_tls
        self.frontend_reset_url = frontend_reset_url

    def _send_smtp_sync(self, msg: EmailMessage) -> None:
        """Synchronously connects to SMTP server and transmits the message."""
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
            if self.smtp_use_tls:
                server.starttls()
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)

    async def send_password_reset_email(
        self, recipient_email: str, reset_token: str
    ) -> bool:
        """
        Builds and sends a password reset email asynchronously using asyncio.to_thread
        to avoid blocking the main event loop.
        """
        reset_link = f"{self.frontend_reset_url}?token={reset_token}"
        expires_minutes = settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES

        msg = EmailMessage()
        msg["Subject"] = "Password Reset Request"
        msg["From"] = self.smtp_from_email
        msg["To"] = recipient_email

        # Plain text fallback
        text_content = (
            f"Hello,\n\n"
            f"We received a request to reset your password. You can reset it by clicking the link below:\n\n"
            f"{reset_link}\n\n"
            f"This link is valid for {expires_minutes} minutes. "
            f"If you did not request a password reset, you can safely ignore this email.\n"
        )
        msg.set_content(text_content)

        # HTML formatted alternative
        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f9fafb; margin: 0; padding: 20px; }}
    .container {{ max-width: 560px; margin: 0 auto; background: #ffffff; padding: 32px; border-radius: 8px; border: 1px solid #e5e7eb; }}
    h1 {{ font-size: 20px; color: #111827; margin-top: 0; }}
    p {{ color: #4b5563; line-height: 1.5; font-size: 15px; }}
    .btn {{ display: inline-block; padding: 12px 24px; background-color: #2563eb; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }}
    .footer {{ margin-top: 24px; font-size: 12px; color: #9ca3af; border-top: 1px solid #f3f4f6; padding-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Password Reset Request</h1>
    <p>We received a request to reset your password. Click the button below to choose a new password:</p>
    <p style="text-align: center;">
      <a href="{reset_link}" class="btn" target="_blank">Reset Password</a>
    </p>
    <p>Or copy and paste this link into your browser:</p>
    <p style="word-break: break-all; color: #2563eb;">{reset_link}</p>
    <p>This link is valid for <strong>{expires_minutes} minutes</strong>.</p>
    <div class="footer">
      If you did not request a password reset, please ignore this email. Your password will remain unchanged.
    </div>
  </div>
</body>
</html>"""
        msg.add_alternative(html_content, subtype="html")

        try:
            await asyncio.to_thread(self._send_smtp_sync, msg)
            logger.info("Password reset email sent to %s", recipient_email)
            return True
        except Exception as exc:
            logger.error(
                "Failed to send password reset email to %s: %s", recipient_email, exc
            )
            return False
