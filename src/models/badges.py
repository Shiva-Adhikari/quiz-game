from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from src.core.database import Base  # Your existing base
from typing import Optional, List


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    criteria_type: Mapped[str] = mapped_column(String(50), nullable=False)  # quiz_count, perfect_score, speed_average, category_accuracy, streak_count
    criteria_value: Mapped[int] = mapped_column(Integer, nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For category-specific badges
    icon_url: Mapped[Optional[str]] = mapped_column(String(255))
    xp_reward: Mapped[int] = mapped_column(Integer, default=0)
    coins_reward: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user_badges: Mapped[List["UserBadge"]] = relationship("UserBadge", back_populates="badge")


class UserBadge(Base):
    __tablename__ = "user_badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    badge_id: Mapped[int] = mapped_column(Integer, ForeignKey("badges.id"), nullable=False)
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    progress_value: Mapped[int] = mapped_column(Integer, default=0)
    is_claimed: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    badge: Mapped["Badge"] = relationship("Badge", back_populates="user_badges")
