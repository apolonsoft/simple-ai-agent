# app/core/dependencies.py
import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis_client
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import UserModel

# Enables the "Authorize" button in Swagger UI (/docs)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception

    try:
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, TypeError):
        raise credentials_exception from None

    # Check for distributed session revocation in Redis
    try:
        redis = await get_redis_client()
        revoked_at = await redis.get(f"revoked_user:{user_id}")
        if revoked_at is not None:
            token_iat = payload.get("iat")
            if token_iat is None or int(token_iat) < int(revoked_at):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session revoked. Please log in again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
    except HTTPException:
        raise
    except Exception:
        # Graceful degradation if Redis is temporarily unreachable
        pass

    user = await db.get(UserModel, user_id)
    if not user or not user.is_active:
        raise credentials_exception

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
