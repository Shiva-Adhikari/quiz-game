from fastapi import Request, Depends, HTTPException
from src.utils.db import get_db
from sqlalchemy.orm import Session
from src.models.authentication import UserSession, User
from datetime import datetime, timezone


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    session_id = request.cookies.get('session_id')
    if not session_id:
        raise HTTPException(status_code=404, detail='Invalid session')

    session = db.query(UserSession).filter(UserSession.session_token == session_id).first()
    if not session or (session.expires_at < datetime.now(timezone.utc)):
        raise HTTPException(status_code=401, detail='Invalid session')

    return session.user
