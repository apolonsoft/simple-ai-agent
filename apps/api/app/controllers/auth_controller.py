# app/controllers/auth_controller.py
from fastapi import HTTPException, status

from app.schemas.user import (
    MessageResponse,
    Token,
    UserCreate,
    UserResponse,
    VerifyResetTokenResponse,
)
from app.services.auth_service import AuthService
from app.services.email_service import EmailService


class AuthController:
    def __init__(self, service: AuthService, email_service: EmailService | None = None):
        self.service = service
        self.email_service = email_service or EmailService()

    async def register(self, user_in: UserCreate) -> UserResponse:
        existing = await self.service.get_by_email(user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered.",
            )
        user = await self.service.register_user(user_in)
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> Token:
        user = await self.service.authenticate(email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = self.service.generate_token(user)
        return Token(access_token=token)

    async def forgot_password(self, email: str) -> MessageResponse:
        raw_token = await self.service.create_password_reset(email)
        if raw_token:
            await self.email_service.send_password_reset_email(email, raw_token)

        return MessageResponse(
            message="If an account with that email exists, a password reset link has been sent."
        )

    async def verify_reset_token(self, token: str) -> VerifyResetTokenResponse:
        record = await self.service.verify_reset_token(token)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token.",
            )
        return VerifyResetTokenResponse(valid=True, email=record.user.email)

    async def reset_password(self, token: str, new_password: str) -> MessageResponse:
        success = await self.service.reset_password(token, new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token.",
            )
        return MessageResponse(message="Password has been successfully reset.")
