# app/routes/user_routes.py
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.user_controller import UserController
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import UserModel
from app.schemas.user import UserProfileResponse, UserProfileUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_controller(db: AsyncSession = Depends(get_db)) -> UserController:
    return UserController(UserService(db))


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: UserModel = Depends(get_current_user),
    controller: UserController = Depends(get_user_controller),
) -> UserProfileResponse:
    """Protected endpoint: Returns full profile details of current authenticated user."""
    return await controller.get_profile(current_user)


@router.patch("/me", response_model=UserProfileResponse)
async def update_my_profile(
    profile_in: UserProfileUpdate,
    current_user: UserModel = Depends(get_current_user),
    controller: UserController = Depends(get_user_controller),
) -> UserProfileResponse:
    """Protected endpoint: Updates profile fields (full_name, bio) for current user."""
    return await controller.update_profile(current_user, profile_in)


@router.post("/me/avatar", response_model=UserProfileResponse)
async def upload_my_avatar(
    file: UploadFile = File(..., description="Avatar image (JPEG, PNG, or WebP <= 5MB)"),
    current_user: UserModel = Depends(get_current_user),
    controller: UserController = Depends(get_user_controller),
) -> UserProfileResponse:
    """Protected endpoint: Uploads user avatar to SeaweedFS/S3 storage."""
    return await controller.upload_avatar(current_user, file)
