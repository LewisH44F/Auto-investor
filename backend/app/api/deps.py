"""FastAPI dependency injection helpers."""

from __future__ import annotations

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import get_redis
from app.core.security import decode_access_token

security = HTTPBearer(auto_error=False)


async def get_session(session: AsyncSession = Depends(get_db)) -> AsyncSession:
    """Re-export the DB session dependency."""
    return session


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """Return the user subject from JWT if present, else None (demo mode)."""
    if credentials is None:
        return None
    subject = decode_access_token(credentials.credentials)
    return subject


async def get_current_user(
    subject: Optional[str] = Depends(get_current_user_optional),
) -> str:
    """Require a valid JWT. Raise 401 if missing/invalid."""
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return subject
