# app/controllers/auth_controller.py
from fastapi import HTTPException, status

from app.schemas.user import Token, UserCreate, UserResponse
from app.services.auth_service import AuthService


class AuthController:
    def __init__(self, service: AuthService):
        self.service = service

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
