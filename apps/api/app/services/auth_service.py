# app/services/auth_service.py
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.session_revocation import revoke_user_sessions
from app.models.password_reset import PasswordResetModel
from app.models.user import UserModel
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: AsyncSession, redis_client=None):
        self.db = db
        self.redis = redis_client

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        """Computes SHA-256 digest of the raw token for secure database storage."""
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    async def get_by_email(self, email: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.db.scalars(stmt)
        return result.first()

    async def register_user(self, user_in: UserCreate) -> UserModel:
        hashed_pw = get_password_hash(user_in.password)
        user = UserModel(
            email=user_in.email, hashed_password=hashed_pw, role=user_in.role
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

    async def create_password_reset(self, email: str) -> str | None:
        """
        Initiates a password reset for the specified email.
        Returns the plaintext raw token if user exists and is active, else returns None.
        """
        user = await self.get_by_email(email)
        if not user or not user.is_active:
            return None

        raw_token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )

        reset_record = PasswordResetModel(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_used=False,
        )
        self.db.add(reset_record)
        await self.db.commit()
        return raw_token

    async def verify_reset_token(self, raw_token: str) -> PasswordResetModel | None:
        """
        Validates the provided raw reset token against the database.
        Returns the reset record if valid, unused, and unexpired; otherwise None.
        """
        if not raw_token:
            return None

        token_hash = self._hash_token(raw_token)
        stmt = (
            select(PasswordResetModel)
            .options(selectinload(PasswordResetModel.user))
            .where(
                PasswordResetModel.token_hash == token_hash,
                PasswordResetModel.is_used.is_(False),
            )
        )
        result = await self.db.scalars(stmt)
        record = result.first()
        if not record:
            return None

        # Check expiration with timezone tolerance
        now = datetime.now(timezone.utc)
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < now:
            return None

        return record

    async def reset_password(self, raw_token: str, new_password: str) -> bool:
        """
        Consumes the reset token and updates the user's password.
        Returns True on success, False if the token is invalid or expired.
        """
        record = await self.verify_reset_token(raw_token)
        if not record:
            return False

        stmt = select(UserModel).where(UserModel.id == record.user_id)
        result = await self.db.scalars(stmt)
        user = result.first()
        if not user or not user.is_active:
            return False

        user.hashed_password = get_password_hash(new_password)
        record.is_used = True
        record.used_at = datetime.now(timezone.utc)
        await self.db.commit()
        return True

    async def change_password(
        self, user: UserModel, current_password: str, new_password: str
    ) -> None:
        """
        Validates the user's current password, checks that the new password is not identical,
        updates the password hash in the database, and registers a revocation timestamp in Redis
        to invalidate active tokens across all sessions.
        """
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password cannot be the same as current password.",
            )

        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        await self.db.refresh(user)

        # Invalidate existing JWT sessions across devices via Redis
        await revoke_user_sessions(
            user.id,
            settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            client=self.redis,
        )
