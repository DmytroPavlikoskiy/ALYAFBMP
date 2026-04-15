"""
FastAPI auth dependencies.

Dependency hierarchy (FastAPI caches each node once per request):

    get_current_user          ← single DB query; returns User object
         │
         ├── get_current_user_id           ← derives uuid from cached User
         │
         └── verify_user_not_banned        ← partial-ban guard (zero extra DB calls)
                  │
                  └── applied only to write product endpoints

Public / browse endpoints use get_current_user_id_optional which makes its
own DB call only when a token is present and does NOT enforce the partial ban.
WebSocket auth uses get_user_id_from_ws_token (raw token string path).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_db
from common.models import User
from config import settings

security = HTTPBearer(auto_error=False)

JWT_SECRET = settings.JWT_SECRET
ALGORITHM = settings.ALGORITHM


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _decode_token(token: str) -> uuid.UUID:
    """Decode a raw JWT string and return the user UUID from the `sub` claim."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub")
        return uuid.UUID(user_id)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


async def _load_user(user_uuid: uuid.UUID, db: AsyncSession) -> User:
    """
    Load a user from the database.

    Only checks that the account *exists* — intentionally does NOT enforce
    the partial ban so that banned users can still authenticate, browse, and
    use non-restricted endpoints.  Ban enforcement is delegated to the
    verify_user_not_banned dependency which is applied selectively.
    """
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# Public dependencies
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Authenticate the request and return the full User ORM object.

    This is the single DB query for all auth in a request.  FastAPI caches
    the result for the lifetime of the request, so any other dependency that
    also declares Depends(get_current_user) receives the same object for free.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_uuid = _decode_token(credentials.credentials)
    return await _load_user(user_uuid, db)


async def get_current_user_id(
    user: User = Depends(get_current_user),
) -> uuid.UUID:
    """
    Return the authenticated user's UUID.

    Thin wrapper around get_current_user — no extra DB call; FastAPI reuses
    the cached User object from the same request.
    """
    return user.id


async def get_current_user_id_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> uuid.UUID | None:
    """
    Like get_current_user_id but returns None for unauthenticated requests.

    Used for public endpoints (e.g. the product feed) where personalisation
    is applied when a token is present but access is not gated on auth.
    Partial bans are NOT enforced here — a banned user can still browse.
    """
    if credentials is None:
        return None
    user_uuid = _decode_token(credentials.credentials)
    user = await _load_user(user_uuid, db)
    return user.id


async def verify_user_not_banned(
    user: User = Depends(get_current_user),
) -> None:
    """
    Partial-ban guard for content creation and modification endpoints.

    Raises HTTP 403 if the user has an active ban (banned_until > now).
    Apply this dependency *only* to write endpoints (POST/PATCH/PUT/DELETE
    for products). Do NOT apply it to GET routes or to login/register.

    Zero extra DB queries: FastAPI returns the already-cached User object
    that get_current_user fetched earlier in the same request cycle.
    """
    if user.banned_until and user.banned_until > datetime.now(timezone.utc):
        until = user.banned_until.strftime("%d %b %Y at %H:%M UTC")
        raise HTTPException(
            status_code=403,
            detail=f"Your account is restricted from posting products until {until}.",
        )


async def get_user_id_from_ws_token(token: str, db: AsyncSession) -> uuid.UUID:
    """Decode a JWT passed as a query-string token (WebSocket connections)."""
    user_uuid = _decode_token(token)
    user = await _load_user(user_uuid, db)
    return user.id
