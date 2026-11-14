# app/controllers/user_controller.py
from fastapi import UploadFile

from app.models.user import UserModel
from app.schemas.user import UserProfileResponse, UserProfileUpdate
from app.services.user_service import UserService


class UserController:
    def __init__(self, service: UserService) -> None:
        self.service = service

    async def get_profile(self, user: UserModel) -> UserProfileResponse:
        profile = await self.service.get_profile(user)
        return UserProfileResponse.model_validate(profile)

    async def update_profile(
        self, user: UserModel, profile_in: UserProfileUpdate
    ) -> UserProfileResponse:
        updated = await self.service.update_profile(user, profile_in)
        return UserProfileResponse.model_validate(updated)

    async def upload_avatar(
        self, user: UserModel, file: UploadFile
    ) -> UserProfileResponse:
        updated = await self.service.upload_avatar(user, file)
        return UserProfileResponse.model_validate(updated)
