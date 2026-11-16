# app/controllers/admin_controller.py
import uuid

from app.models.user import UserModel
from app.schemas.admin import (
    AdminActionResponse,
    AdminBanUserRequest,
    AdminUpdateRoleRequest,
    AdminUserDetailResponse,
    AdminUserListResponse,
)
from app.services.admin_service import AdminService


class AdminController:
    def __init__(self, service: AdminService):
        self.service = service

    async def list_users(
        self,
        page: int = 1,
        limit: int = 20,
        search: str | None = None,
        role: str | None = None,
        status_filter: str | None = None,
    ) -> AdminUserListResponse:
        return await self.service.list_users(
            page=page,
            limit=limit,
            search=search,
            role=role,
            status_filter=status_filter,
        )

    async def get_user_detail(self, user_id: uuid.UUID) -> AdminUserDetailResponse:
        return await self.service.get_user_detail(user_id)

    async def ban_user(
        self,
        admin_user: UserModel,
        target_user_id: uuid.UUID,
        request_in: AdminBanUserRequest,
    ) -> AdminActionResponse:
        return await self.service.ban_user(
            admin_user=admin_user,
            target_user_id=target_user_id,
            reason=request_in.reason,
        )

    async def unban_user(
        self,
        admin_user: UserModel,
        target_user_id: uuid.UUID,
    ) -> AdminActionResponse:
        return await self.service.unban_user(
            admin_user=admin_user,
            target_user_id=target_user_id,
        )

    async def update_role(
        self,
        super_admin_user: UserModel,
        target_user_id: uuid.UUID,
        request_in: AdminUpdateRoleRequest,
    ) -> AdminActionResponse:
        return await self.service.update_role(
            super_admin_user=super_admin_user,
            target_user_id=target_user_id,
            new_role=request_in.role,
        )
