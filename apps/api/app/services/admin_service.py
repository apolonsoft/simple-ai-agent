# app/services/admin_service.py
import math
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session_revocation import clear_user_revocation, revoke_user_sessions
from app.models.chat import ChatSessionModel
from app.models.user import UserModel
from app.schemas.admin import (
    AdminActionResponse,
    AdminUserDetailResponse,
    AdminUserListItem,
    AdminUserListResponse,
)


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(
        self,
        page: int = 1,
        limit: int = 20,
        search: str | None = None,
        role: str | None = None,
        status_filter: str | None = None,
    ) -> AdminUserListResponse:
        page = max(1, page)
        limit = max(1, min(limit, 100))
        offset = (page - 1) * limit

        query = select(UserModel)
        count_query = select(func.count(UserModel.id))

        filters = []
        if search and search.strip():
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    UserModel.email.ilike(term),
                    UserModel.full_name.ilike(term),
                )
            )
        if role and role.strip():
            filters.append(UserModel.role == role.strip())

        if status_filter:
            sf = status_filter.strip().lower()
            if sf == "banned":
                filters.append(UserModel.is_banned.is_(True))
            elif sf == "active":
                filters.extend(
                    [
                        UserModel.is_banned.is_(False),
                        UserModel.is_active.is_(True),
                    ]
                )
            elif sf == "inactive":
                filters.append(UserModel.is_active.is_(False))

        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)

        total_res = await self.db.execute(count_query)
        total = total_res.scalar_one() or 0

        query = query.order_by(UserModel.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()

        total_pages = math.ceil(total / limit) if total > 0 else 1

        items = [AdminUserListItem.model_validate(u) for u in users]
        return AdminUserListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    async def get_user_detail(self, user_id: uuid.UUID) -> AdminUserDetailResponse:
        user = await self.db.get(UserModel, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' was not found.",
            )

        # Count user's chat sessions
        count_query = select(func.count(ChatSessionModel.id)).where(
            ChatSessionModel.user_id == user_id
        )
        count_res = await self.db.execute(count_query)
        sessions_count = count_res.scalar_one() or 0

        return AdminUserDetailResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_banned=user.is_banned,
            banned_at=user.banned_at,
            ban_reason=user.ban_reason,
            avatar_url=user.avatar_url,
            bio=user.bio,
            chat_sessions_count=sessions_count,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def ban_user(
        self,
        admin_user: UserModel,
        target_user_id: uuid.UUID,
        reason: str | None = None,
    ) -> AdminActionResponse:
        target = await self.db.get(UserModel, target_user_id)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{target_user_id}' was not found.",
            )

        # Self-ban guardrail
        if admin_user.id == target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot ban their own account.",
            )

        # Administrative hierarchy guardrails
        if admin_user.role != "super_admin" and target.role in ("admin", "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to ban administrative accounts.",
            )

        if admin_user.role == "super_admin" and target.role == "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super administrator accounts cannot be banned.",
            )

        target.is_banned = True
        target.banned_at = datetime.now(timezone.utc)
        target.ban_reason = reason.strip() if reason else None

        # Write session revocation timestamp to Redis
        await revoke_user_sessions(target_user_id, 86400 * 30)

        await self.db.commit()
        await self.db.refresh(target)

        return AdminActionResponse(
            success=True,
            message=f"User '{target.email}' has been banned successfully.",
            user=AdminUserListItem.model_validate(target),
        )

    async def unban_user(
        self,
        admin_user: UserModel,
        target_user_id: uuid.UUID,
    ) -> AdminActionResponse:
        target = await self.db.get(UserModel, target_user_id)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{target_user_id}' was not found.",
            )

        target.is_banned = False
        target.banned_at = None
        target.ban_reason = None

        # Clean up Redis revocation key
        await clear_user_revocation(target_user_id)

        await self.db.commit()
        await self.db.refresh(target)

        return AdminActionResponse(
            success=True,
            message=f"User '{target.email}' has been unbanned successfully.",
            user=AdminUserListItem.model_validate(target),
        )

    async def update_role(
        self,
        super_admin_user: UserModel,
        target_user_id: uuid.UUID,
        new_role: Literal["user", "admin", "super_admin"],
    ) -> AdminActionResponse:
        target = await self.db.get(UserModel, target_user_id)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{target_user_id}' was not found.",
            )

        # Self-demotion guardrail
        if super_admin_user.id == target_user_id and new_role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Super administrators cannot modify or demote their own role.",
            )

        target.role = new_role
        await self.db.commit()
        await self.db.refresh(target)

        return AdminActionResponse(
            success=True,
            message=f"User '{target.email}' role updated to '{new_role}'.",
            user=AdminUserListItem.model_validate(target),
        )
