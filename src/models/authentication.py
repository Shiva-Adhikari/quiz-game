# Standard library imports
from typing import (
    Optional,
    # List
)
from datetime import datetime

# Third-party imports
from sqlalchemy import (
    Integer, Boolean, DateTime, String, func, ForeignKey,
    # CheckConstraint
)
from sqlalchemy.orm import (
    Mapped, mapped_column,
    relationship
)

# Local imports
from src.core.database import Base
'''
# from src.models.user_data import QuizSession
# from src.models.analytics import (
    # ActiveQuizSession, QuestionHistory, UserStatistics)
# from src.models.questions import Category
'''


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True)
    username: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now())

    user_session: Mapped["UserSession"] = relationship(
        "UserSession", back_populates="user")


'''
    # email_verifications: Mapped[List["EmailVerification"]] = relationship(
        # "EmailVerification", back_populates="user")

    # # These should be plural (one-to-many)
    # quiz_sessions: Mapped[List['QuizSession']] = relationship('QuizSession', back_populates='user')

    # active_quiz_session: Mapped[List['ActiveQuizSession']] = relationship(
    #     'ActiveQuizSession', back_populates='user')
    # question_history: Mapped[List['QuestionHistory']] = relationship(
    #     'QuestionHistory', back_populates='user')

    # # This should be singular (one-to-one)
    # user_statistics: Mapped['UserStatistics'] = relationship(
    #     'UserStatistics', back_populates='user')

    # def __repr__(self):
    #     return f'<User(id={self.id}, email={self.email}, username={self.username})>'
'''


class EmailVerification(Base):
    __tablename__ = 'email_verification'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), index=True)
    token: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)


'''
    # user: Mapped['User'] = relationship(
        # 'User', back_populates='email_verification')

    # __table_args__ = (
    #     CheckConstraint(
    #         'token IS NULL OR (token >= 100000 AND token <= 999999)'),
    # )

    # def __repr__(self):
    #     return f'<EmailVerification(id={self.id}, user_id={self.user_id})>'
'''


class UserSession(Base):
    __tablename__ = 'user_sessions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    session_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String)
    device_id: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped['User'] = relationship(
        'User', back_populates='user_session')

'''
    # category: Mapped['Category'] = relationship(
        # 'Category', back_populates='user_sessions')
'''
# /
