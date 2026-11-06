# app/controllers/auth_controller.py
from fastapi import HTTPException, status
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserResponse, Token

class AuthController:
    def __init__(self, service: AuthService):
        self.service = service

    def register(self, user_in: UserCreate) -> UserResponse:
        existing = self.service.get_by_email(user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered."
            )
        user = self.service.register_user(user_in)
        return UserResponse.model_validate(user)

    def login(self, email: str, password: str) -> Token:
        user = self.service.authenticate(email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = self.service.generate_token(user)
        return Token(access_token=token)