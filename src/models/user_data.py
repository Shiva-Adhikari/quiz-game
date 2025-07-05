# Standard library imports
from enum import Enum
from typing import Optional, List
from datetime import datetime

# Third-party imports
from sqlalchemy import (
    Integer, Boolean, DateTime, String, func, ForeignKey, CheckConstraint,
    Enum as SQLEnum)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Local imports
from src.core import Base
from src.models.authentication import User
from src.models.questions import Category, Question


class UserProfile(Base):
    __tablename__ = 'user_profiles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True)
    display_name: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True)
    total_xp: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0)
    current_level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1)
    coins: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0)
    total_games_played: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now())

    user: Mapped['User'] = relationship(
        'User', back_populates='user_profiles')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'total_xp >= 0', name='check_total_xp_non_negative'),
        CheckConstraint(
            'current_level >= 1', name='check_current_level_positive'),
        CheckConstraint(
            'coins >= 0', name='check_coins_non_negative'),
        CheckConstraint(
            'total_games_played >= 0', name='check_games_non_negative'),
    )

    def __repr__(self):
        return f'<UserProfile(id={self.id}, user_id={self.user_id}, '
        f'display_name="{self.display_name}", level={self.current_level})>'


class SessionStatus(Enum):
    STARTED = 'started'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    ABANDONED = 'abandoned'
    TIMEOUT = 'timeout'


class SessionType(Enum):
    PRACTICE = 'practice'
    TIMED = 'timed'
    CHALLENGE = 'challenge'
    TOURNAMENT = 'tournament'


class DifficultyLevel(Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'


class QuizSession(Base):
    __tablename__ = 'quiz_sessions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('categories.id', ondelete='CASCADE'), index=True)
    session_type: Mapped[SessionType] = mapped_column(
        SQLEnum(SessionType), nullable=False)
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        SQLEnum(DifficultyLevel), nullable=False)
    total_questions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0)
    correct_answers: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0)
    total_time_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0)
    xp_earned: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0)
    coins_earned: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0)
    status: Mapped[SessionStatus] = mapped_column(SQLEnum(
        SessionStatus), nullable=False, default=SessionStatus.STARTED)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped[Optional['User']] = relationship(
        'User', back_populates='quiz_sessions')
    category: Mapped[Optional['Category']] = relationship(
        'Category', back_populates='quiz_sessions')
    user_answers: Mapped[List['UserAnswer']] = relationship(
        'UserAnswer', back_populates='quiz_sessions')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'total_questions >= 0',
            name='check_total_questions_non_negative'),
        CheckConstraint(
            'correct_answers >= 0',
            name='check_correct_answers_non_negative'),
        CheckConstraint(
            'correct_answers <= total_questions',
            name='check_correct_answers_not_exceed_total'),
        CheckConstraint(
            'total_time_seconds >= 0', name='check_time_non_negative'),
        CheckConstraint(
            'xp_earned >= 0', name='check_xp_non_negative'),
        CheckConstraint(
            'coins_earned >= 0', name='check_coins_non_negative'),
        CheckConstraint(
            'completed_at >= started_at',
            name='check_completed_after_started')
    )

    def __repr__(self) -> str:
        return f'<QuizSession(id={self.id}, user_id={self.user_id}, ' \
                f'status={self.status.value}, ' \
                f'score={self.correct_answers}/{self.total_questions})>'


class UserAnswer(Base):
    __tablename__ = 'user_answers'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('quiz_sessions.id'), index=True)
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('questions.id'), index=True)
    user_answer: Mapped[str] = mapped_column(String, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    time_taken_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0)
    answered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)

    # Relationship
    quiz_session: Mapped['QuizSession'] = relationship(
        'QuizSession', back_populates='user_answers')
    question: Mapped['Question'] = relationship(
        'Question', back_populates='user_answers')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'time_taken_seconds >= 0', name='check_time_taken_non_negative')
    )

    def __repr__(self) -> str:
        return f'<UserAnswer(id={self.id}, ' \
            f'session_id={self.quiz_session_id}, ' \
            f'question_id={self.question_id}, correct={self.is_correct})>'
# /
