# app/services/user_service.py
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import UserModel
from app.schemas.user import UserProfileUpdate
from app.services.storage_service import StorageService

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


class UserService:
    def __init__(
        self, db: AsyncSession, storage_service: StorageService | None = None
    ) -> None:
        self.db = db
        self.storage_service = storage_service or StorageService()

    async def get_profile(self, user: UserModel) -> UserModel:
        """Returns the authenticated user's current profile."""
        return user

    async def update_profile(
        self, user: UserModel, profile_in: UserProfileUpdate
    ) -> UserModel:
        """Updates user profile attributes (full_name, bio)."""
        if profile_in.full_name is not None:
            user.full_name = profile_in.full_name
        if profile_in.bio is not None:
            user.bio = profile_in.bio

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def upload_avatar(self, user: UserModel, file: UploadFile) -> UserModel:
        """Validates and uploads an avatar file to S3 storage, updating user.avatar_url."""
        if not file.content_type or file.content_type.lower() not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format. Allowed formats: image/jpeg, image/png, image/webp",
            )

        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded image file is empty",
            )

        if len(file_bytes) > settings.MAX_AVATAR_SIZE_BYTES:
            max_mb = settings.MAX_AVATAR_SIZE_BYTES // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image exceeds maximum allowed size of {max_mb}MB",
            )

        filename = file.filename or f"avatar_{user.id}.png"
        avatar_url = await self.storage_service.upload_file(
            file_bytes=file_bytes,
            original_filename=filename,
            content_type=file.content_type,
        )

        user.avatar_url = avatar_url
        await self.db.commit()
        await self.db.refresh(user)
        return user
