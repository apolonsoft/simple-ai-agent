# app/schemas/admin.py
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminBanUserRequest(BaseModel):
    reason: str | None = Field(
        default=None, max_length=500, description="Reason for administrative ban"
    )


class AdminUpdateRoleRequest(BaseModel):
    role: Literal["user", "admin", "super_admin"] = Field(
        description="Target user role ('user', 'admin', or 'super_admin')"
    )


class AdminUserListItem(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    role: str
    is_active: bool
    is_banned: bool
    banned_at: datetime | None = None
    ban_reason: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    total: int
    page: int
    limit: int
    total_pages: int


class AdminUserDetailResponse(AdminUserListItem):
    avatar_url: str | None = None
    bio: str | None = None
    chat_sessions_count: int = 0
    updated_at: datetime | None = None


class AdminActionResponse(BaseModel):
    success: bool
    message: str
    user: AdminUserListItem
