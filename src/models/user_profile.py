from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from datetime import datetime
from src.core.database import Base
from src.models.authentication import User
from src.models.level_system import LevelSystem


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(30), index=True)
    total_xp: Mapped[int] = mapped_column(Integer, default=0, index=True)
    current_level: Mapped[int] = mapped_column(Integer, default=1)
    coins: Mapped[int] = mapped_column(Integer, default=0)
    total_games_played: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")
    level_info: Mapped["LevelSystem"] = relationship(
        "LevelSystem", foreign_keys=[current_level],
        primaryjoin="UserProfile.current_level == LevelSystem.level")
