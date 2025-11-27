# === Standard library imports ===
from datetime import datetime, timezone

# === Third-party imports ===
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Response, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# === Local imports ===
from src.utils.db import get_db
from src.models.authentication import UserSession, User


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session_id: str | None = Cookie(None, alias="session_id"),  # Use Cookie dependency
    db: Session = Depends(get_db)) -> User:
    """Verify user"""

    session_token = None

    # Try to get token from Authorization header (mobile)
    if credentials:
        session_token = credentials.credentials

    # If no token in header, try cookie (web)
    if not session_token and session_id:
        session_token = session_id

    if not session_token:
        raise HTTPException(status_code=401, detail='Authentication required')

    # Find active session
    query = select(UserSession).where(
        UserSession.session_token == session_token,
        UserSession.is_active,
        UserSession.expires_at > datetime.now(timezone.utc))
    session = await db.scalar(query)

    if not session:
        raise HTTPException(status_code=401, detail='Invalid or expired session')

    query = select(User).where(User.id == session.user_id)
    user = await db.scalar(query)

    if not user:
        raise HTTPException(status_code=401, detail='User not found')

    return user
