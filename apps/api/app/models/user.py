# app/models/user.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.chat import ChatSessionModel
    from app.models.password_reset import PasswordResetModel


class UserModel(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), default="user", nullable=False
    )  # "user" | "admin" | "super_admin"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Administrative ban management
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    banned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ban_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # User Profile Information
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationship to user's chat sessions
    chat_sessions: Mapped[list["ChatSessionModel"]] = relationship(
        "ChatSessionModel",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )

    # Relationship to password reset requests
    password_resets: Mapped[list["PasswordResetModel"]] = relationship(
        "PasswordResetModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="raise",
    )
