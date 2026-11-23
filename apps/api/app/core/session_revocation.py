# apps/api/app/core/session_revocation.py
from datetime import datetime, timezone
from typing import Any

from app.models.user import UserModel


def revoke_user_sessions(user: UserModel) -> None:
    """Invalidate all existing JWTs for a user by advancing tokens_valid_after."""
    user.tokens_valid_after = datetime.now(timezone.utc).replace(microsecond=0)


def is_token_revoked(user: UserModel, payload: dict[str, Any]) -> bool:
    """Return True if the token was issued before the user's revocation timestamp."""
    valid_after = user.tokens_valid_after
    if valid_after is None:
        return False
    if valid_after.tzinfo is None:
        valid_after = valid_after.replace(tzinfo=timezone.utc)
    iat = payload.get("iat")
    return iat is None or int(iat) < int(valid_after.timestamp())
