# Standard library imports
from typing import Optional
from datetime import datetime

# Third-party imports
from sqlalchemy import (
    Integer, Boolean, DateTime, String, func, ForeignKey, CheckConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Local imports
from src.core import Base
from src.models.questions import Category
from src.models.authentication import User


class DailyChallenge(Base):
    __tablename__ = 'daily_challenges'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('categories.id'), index=True)
    challenge_type: Mapped[str] = mapped_column(String(500), nullable=False)
    target_value: Mapped[int] = mapped_column(Integer, default=0)
    description:  Mapped[str] = mapped_column(String(500), nullable=False)
    xp_reward: Mapped[int] = mapped_column(
        Integer, default=0)
    coins_reward: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    # Relationship
    category: Mapped['Category'] = relationship(
        'Category', back_populates='daily_challenges')

    __table_args__ = (
        CheckConstraint(
            'target_value >= 0', name='check_target_value_non_negative'),
        CheckConstraint('xp_reward >= 0', name='check_xp_reward_non_negative'),
        CheckConstraint(
            'coins_reward >= 0', name='check_coins_reward_non_negative')
    )

    def __repr__(self) -> str:
        return (
            f"<DailyChallenge(id={self.id}, "
            f"category_id={self.category_id}, "
            f"challenge_type='{self.challenge_type}', "
            f"is_active={self.is_active})>"
        )

    def __str__(self) -> str:
        return f"Daily Challenge: {self.challenge_type} (ID: {self.id})"


class DailyChallengeCompletion(Base):
    __tablename__ = 'daily_challenge_completions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    daily_challenge_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('daily_challenges.id'), index=True)
    progress_value: Mapped[int] = mapped_column(
        Integer, default=0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    reward_claimed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)

    # Relationship
    user: Mapped['User'] = relationship(
        'User', back_populates='daily_challenge_completions',
        lazy='select')
    daily_challenge: Mapped['DailyChallenge'] = relationship(
        'DailyChallenge', back_populates='daily_challenge_completions',
        lazy='select')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'progress_value >= 0', name='check_progress_value_non_negative'),
        CheckConstraint(
            'NOT reward_claimed OR is_completed',
            name='check_reward_claimed_only_if_completed'),
        CheckConstraint(
            'NOT is_completed OR completed_at IS NOT NULL',
            name='check_completed_at_when_completed'),
    )

    def __repr__(self) -> str:
        return (
            f"<DailyChallengeCompletion(id={self.id}, "
            f"user_id={self.user_id}, "
            f"daily_challenge_id={self.daily_challenge_id}, "
            f"progress_value={self.progress_value}, "
            f"is_completed={self.is_completed}, "
            f"reward_claimed={self.reward_claimed})>"
        )

    def __str__(self) -> str:
        status = "Completed" if self.is_completed else f"Progress: {self.progress_value}"
        return f"Challenge Completion (ID: {self.id}) - {status}"
