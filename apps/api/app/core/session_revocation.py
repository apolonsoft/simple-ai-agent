# apps/api/app/core/session_revocation.py
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.redis import get_redis_client

REVOCATION_KEY_PREFIX = "revoked_user:"


async def revoke_user_sessions(
    user_id: uuid.UUID,
    ttl_seconds: int,
    client: Any = None,
) -> None:
    """Invalidate all active sessions for a user by storing a revocation timestamp in Redis."""
    try:
        redis = client or await get_redis_client()
        now_ts = int(datetime.now(timezone.utc).timestamp())
        await redis.set(f"{REVOCATION_KEY_PREFIX}{user_id}", now_ts, ex=ttl_seconds)
    except Exception:
        # Graceful degradation if Redis is temporarily unreachable
        pass


async def clear_user_revocation(
    user_id: uuid.UUID,
    client: Any = None,
) -> None:
    """Remove user session revocation record upon account reactivation/unban."""
    try:
        redis = client or await get_redis_client()
        await redis.delete(f"{REVOCATION_KEY_PREFIX}{user_id}")
    except Exception:
        # Graceful degradation if Redis is temporarily unreachable
        pass


async def is_token_revoked(
    user_id: uuid.UUID,
    payload: dict[str, Any],
    client: Any = None,
) -> bool:
    """Check whether a token was issued prior to the user's recorded session revocation timestamp."""
    try:
        redis = client or await get_redis_client()
        revoked_at = await redis.get(f"{REVOCATION_KEY_PREFIX}{user_id}")
        if revoked_at is not None:
            token_iat = payload.get("iat")
            if token_iat is None or int(token_iat) < int(revoked_at):
                return True
        return False
    except Exception:
        # Fail-open if Redis is temporarily unreachable
        return False
