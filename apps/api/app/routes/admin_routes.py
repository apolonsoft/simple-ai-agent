# app/routes/admin_routes.py
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.admin_controller import AdminController
from app.core.dependencies import require_admin_role, require_super_admin_role
from app.db.session import get_db
from app.models.user import UserModel
from app.schemas.admin import (
    AdminActionResponse,
    AdminBanUserRequest,
    AdminUpdateRoleRequest,
    AdminUserDetailResponse,
    AdminUserListResponse,
)
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin/users", tags=["Admin"])


def get_admin_controller(db: AsyncSession = Depends(get_db)) -> AdminController:
    return AdminController(AdminService(db))


@router.get("", response_model=AdminUserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(
        default=20, ge=1, le=100, description="Items per page (max 100)"
    ),
    search: str | None = Query(
        default=None, description="Search term for email or full name"
    ),
    role: str | None = Query(
        default=None, description="Filter by role ('user', 'admin', 'super_admin')"
    ),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter by status ('active', 'banned', 'inactive')",
    ),
    current_admin: UserModel = Depends(require_admin_role),
    controller: AdminController = Depends(get_admin_controller),
) -> AdminUserListResponse:
    """Lists registered users with pagination, keyword search, and role/status filtering."""
    return await controller.list_users(
        page=page,
        limit=limit,
        search=search,
        role=role,
        status_filter=status_filter,
    )


@router.get("/{user_id}", response_model=AdminUserDetailResponse)
async def get_user_detail(
    user_id: uuid.UUID,
    current_admin: UserModel = Depends(require_admin_role),
    controller: AdminController = Depends(get_admin_controller),
) -> AdminUserDetailResponse:
    """Retrieves full details and usage metrics for a specific user."""
    return await controller.get_user_detail(user_id)


@router.post(
    "/{user_id}/ban",
    response_model=AdminActionResponse,
    status_code=status.HTTP_200_OK,
)
async def ban_user(
    user_id: uuid.UUID,
    request_in: AdminBanUserRequest,
    current_admin: UserModel = Depends(require_admin_role),
    controller: AdminController = Depends(get_admin_controller),
) -> AdminActionResponse:
    """Bans user account, records ban reason/timestamp, and invalidates active JWT sessions in Redis."""
    return await controller.ban_user(
        admin_user=current_admin,
        target_user_id=user_id,
        request_in=request_in,
    )


@router.post(
    "/{user_id}/unban",
    response_model=AdminActionResponse,
    status_code=status.HTTP_200_OK,
)
async def unban_user(
    user_id: uuid.UUID,
    current_admin: UserModel = Depends(require_admin_role),
    controller: AdminController = Depends(get_admin_controller),
) -> AdminActionResponse:
    """Unbans user account and restores access."""
    return await controller.unban_user(
        admin_user=current_admin,
        target_user_id=user_id,
    )


@router.patch(
    "/{user_id}/role",
    response_model=AdminActionResponse,
    status_code=status.HTTP_200_OK,
)
async def update_user_role(
    user_id: uuid.UUID,
    request_in: AdminUpdateRoleRequest,
    current_super_admin: UserModel = Depends(require_super_admin_role),
    controller: AdminController = Depends(get_admin_controller),
) -> AdminActionResponse:
    """Promotes or demotes user role. Strictly requires super_admin privileges."""
    return await controller.update_role(
        super_admin_user=current_super_admin,
        target_user_id=user_id,
        request_in=request_in,
    )
