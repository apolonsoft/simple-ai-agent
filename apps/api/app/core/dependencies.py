# app/core/dependencies.py
import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.core.session_revocation import is_token_revoked
from app.db.session import get_db
from app.models.user import UserModel

# Enables the "Authorize" button in Swagger UI (/docs)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    header_token: str | None = Depends(oauth2_scheme),
    query_token: str | None = Query(None, alias="token"),
    db: AsyncSession = Depends(get_db),
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = header_token or query_token
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception

    try:
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, TypeError):
        raise credentials_exception from None

    user = await db.get(UserModel, user_id)
    if not user or not user.is_active:
        raise credentials_exception

    if is_token_revoked(user, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account has been suspended. Reason: {user.ban_reason or 'No reason specified.'}",
        )

    return user


def require_role(required_role: str) -> Callable:
    """Dependency factory that verifies user has the necessary role."""

    def role_checker(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return current_user

    return role_checker


def require_admin_role(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """Verifies user has administrative privileges ('admin' or 'super_admin')."""
    if current_user.role not in ("admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this administrative resource.",
        )
    return current_user


def require_super_admin_role(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """Verifies user strictly has 'super_admin' privileges."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super administrator privileges required for this action.",
        )
    return current_user
