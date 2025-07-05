# Standard library imports
from datetime import datetime

# Third-party imports
from sqlalchemy import (
    Integer, DateTime, String, func, ForeignKey, CheckConstraint,
    Enum as SQLEnum)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Local imports
from src.core import Base
from src.models.questions import Category
from src.models.user_data import DifficultyLevel


class LevelSystem(Base):
    __tablename__ = 'level_system'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[int] = mapped_column(Integer, default=0, index=True)
    min_xp_required: Mapped[int] = mapped_column(Integer, default=0)
    max_xp_required: Mapped[int] = mapped_column(Integer, default=0)
    level_name: Mapped[str] = mapped_column(String, nullable=False)
    rewards_coins: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint('level >= 0', name='check_level_not_negative'),
        CheckConstraint(
            'min_xp_required >= 0', name='check_min_xp_required_non_negative'),
        CheckConstraint(
            'max_xp_required >= 0', name='check_max_xp_required_non_negative'),
        CheckConstraint(
            'max_xp_required >= min_xp_required',
            name='check_max_xp_greater_than_min_xp'),
        CheckConstraint(
            'rewards_coins >= 0', name='check_rewards_coins_non_negative')
    )

    def __repr__(self) -> str:
        return f'<LevelSystem(id={self.id}, level={self.level}, ' \
            f'name={self.level_name}, ' \
            f'xp_range={self.min_xp_required}-{self.max_xp_required})>'


class QuizConfiguration(Base):
    __tablename__ = 'quiz_configurations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('categories.id'), index=True)
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        SQLEnum(DifficultyLevel), nullable=False,
        default=DifficultyLevel.EASY, index=True)
    time_limit_seconds: Mapped[int] = mapped_column(Integer, default=0)
    questions_per_quiz: Mapped[int] = mapped_column(Integer, default=0)
    xp_reward_base: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(), onupdate=func.now())

    # Relationship
    category: Mapped['Category'] = relationship(
        'Category', back_populates='quiz_configurations')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'time_limit_seconds >= 0',
            name='check_time_limit_seconds_non_negative'),
        CheckConstraint(
            'questions_per_quiz >= 0',
            name='check_questions_per_quiz_non_negative'),
        CheckConstraint(
            'xp_reward_base >= 0', name='check_xp_reward_base_non_negative')
    )

    def __repr__(self) -> str:
        return f'<QuizConfiguration(id={self.id}, ' \
            f'category_id={self.category_id}, ' \
            f'difficulty={self.difficulty_level}, ' \
            f'questions={self.questions_per_quiz})>'
# /
