# Standard library imports
from enum import Enum
from typing import List
from datetime import datetime

# Third-party imports
from sqlalchemy import (
    Integer, Boolean, DateTime, String, func, Float, ForeignKey,
    Enum as SQLEnum)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Local imports
from src.core import Base
from src.models.levels import QuizConfiguration
from src.models.analytics import ActiveQuizSession, QuestionHistory


class DifficultyLevel(Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'
    EXPERT = 'expert'


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    difficulty_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(), onupdate=func.now())

    questions: Mapped[List['Question']] = relationship(
        'Question', back_populates='categories')
    quiz_configurations: Mapped[list['QuizConfiguration']] = relationship(
        'QuizConfiguration', back_populates='categories')
    active_quiz_sessions: Mapped[List['ActiveQuizSession']] = relationship(
        'ActiveQuizSession', back_populates='categories')

    def __repr__(self) -> str:
        return f'<Category(id={self.id}, name={self.name}, ' \
                f'difficulty={self.difficulty_multiplier})>'


class Question(Base):
    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('categories.id', ondelete='CASCADE'), index=True)
    question_text: Mapped[str] = mapped_column(String(500), nullable=False)
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        SQLEnum(DifficultyLevel), nullable=False, index=True,
        default=DifficultyLevel.EASY)
    correct_answer: Mapped[str] = mapped_column(String(50), nullable=False)
    option_a: Mapped[str] = mapped_column(String(50), nullable=False)
    option_b: Mapped[str] = mapped_column(String(50), nullable=False)
    option_c: Mapped[str] = mapped_column(String(50), nullable=False)
    option_d: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(), onupdate=func.now())

    category: Mapped['Category'] = relationship(
        'Category', back_populates='questions')
    question_histories: Mapped[List['QuestionHistory']] = relationship(
        'QuestionHistory', back_populates='questions')

    def __repr__(self) -> str:
        return f'<Question(id={self.id}, ' \
                f'category_id={self.category_id}, ' \
                f'difficulty={self.difficulty_level})>'
# /
