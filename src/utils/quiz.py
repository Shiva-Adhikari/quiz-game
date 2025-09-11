# from fastapi import Depends
# from src.utils.db import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from src.models.quiz_session import QuizSession
from src.utils.enums import SessionStatus


def check_and_expire_sessions(user_id: int, db: Session):
    """Check and expire old inactive sessions"""
    from datetime import timedelta

    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

    expired_sessions = db.query(QuizSession).filter(
        QuizSession.user_id == user_id,
        QuizSession.is_active,
        QuizSession.last_activity_at < cutoff_time
    ).all()

    for session in expired_sessions:
        session.status = SessionStatus.EXPIRED
        session.is_active = False

    if expired_sessions:
        db.commit()
