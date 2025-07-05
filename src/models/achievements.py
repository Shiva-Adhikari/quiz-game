# Standard library imports
from typing import Optional
from datetime import datetime

# Third-party imports
from sqlalchemy import (
    Integer, Boolean, DateTime, String, func, ForeignKey, CheckConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Local imports
from src.core import Base
from src.models.authentication import User


class Badge(Base):
    __tablename__ = 'badges'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    criteria_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    criteria_value: Mapped[int] = mapped_column(Integer, default=0)
    icon_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    xp_reward: Mapped[int] = mapped_column(Integer, default=0)
    coins_reward: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'criteria_value >= 0', name='check_criteria_value_non_negative'),
        CheckConstraint(
            'xp_reward >= 0', name='check_xp_reward_non_negative'),
        CheckConstraint(
            'coins_reward >= 0', name='check_coins_reward_non_negative'),
    )

    def __repr__(self) -> str:
        return f'<Badge(id={self.id}, name={self.name!r}, ' \
            f'criteria_value={self.criteria_value})>'


class UserBadge(Base):
    __tablename__ = 'user_badges'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    badge_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('badges.id'), index=True)
    progress_value: Mapped[int] = mapped_column(Integer, default=0)
    earned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    is_claimed: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)

    # Relationship
    user: Mapped['User'] = relationship(
        'User', back_populates='user_badges')
    badge: Mapped['Badge'] = relationship(
        'Badge', back_populates='user_badges')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'badge_id >= 0', name='check_progress_value_non_negative')
    )

    def __repr__(self) -> str:
        return f'<UserBadge(user_id={self.user_id}, ' \
            f'badge_id={self.badge_id}, ' \
            f'earned_at={self.earned_at})>'
# /
