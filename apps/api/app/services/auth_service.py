# app/services/auth_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import UserModel
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password, create_access_token


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.db.scalars(stmt)
        return result.first()

    async def register_user(self, user_in: UserCreate) -> UserModel:
        hashed_pw = get_password_hash(user_in.password)
        user = UserModel(
            email=user_in.email,
            hashed_password=hashed_pw,
            role=user_in.role
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> UserModel | None:
        user = await self.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    def generate_token(self, user: UserModel) -> str:
        payload = {"sub": str(user.id), "email": user.email, "role": user.role}
        return create_access_token(data=payload)
