# Standard library imports
from typing import Optional
from datetime import datetime

# Third-party imports
from sqlalchemy import (
    Integer, Boolean, DateTime, String, func, ForeignKey,
    CheckConstraint)
from sqlalchemy.orm import Mapped, mapped_column

# Local imports
from src.core.database import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True)
    username: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)


class EmailVerification(Base):
    __tablename__ = 'email_verification'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), index=True)
    token: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), insert_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            'token IS NULL OR (token >= 100000 AND token <= 999999)'),
    )


# class UserSession(Base):
#     __tablename__ = 'user_sessions'

#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
#     session_token: Mapped[str] = mapped_column(String)
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True), server_default=func.now())
#     expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
#     is_active: Mapped[bool] = mapped_column(Boolean, default=True)
