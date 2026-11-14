# app/models/user.py
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Uuid
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
    )  # "user" | "admin"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # User Profile Information
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationship to user's chat sessions
    chat_sessions: Mapped[list["ChatSessionModel"]] = relationship(
        "ChatSessionModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Relationship to password reset requests
    password_resets: Mapped[list["PasswordResetModel"]] = relationship(
        "PasswordResetModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
