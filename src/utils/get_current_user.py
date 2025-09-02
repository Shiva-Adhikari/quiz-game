from fastapi import Depends, HTTPException, Response, Cookie
from src.utils.db import get_db
from sqlalchemy.orm import Session
from src.models.authentication import UserSession, User
from datetime import datetime, timezone
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional


security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session_id: Optional[str] = Cookie(None, alias="session_id"),  # Use Cookie dependency
    db: Session = Depends(get_db)
) -> User:

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
    session = db.query(UserSession).filter(
        UserSession.session_token == session_token,
        UserSession.is_active,
        UserSession.expires_at > datetime.now(timezone.utc)
    ).first()

    if not session:
        raise HTTPException(status_code=401, detail='Invalid or expired session')

    # Get user
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail='User not found')

    return user
