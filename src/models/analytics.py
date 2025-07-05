# Standard library imports
from typing import Optional
from datetime import datetime

# Third-party imports
from sqlalchemy import (
    Integer, Boolean, DateTime, String, func, ForeignKey, Float,
    CheckConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Local imports
from src.core import Base
from src.models.authentication import User
from src.models.questions import Category, Question


class ActiveQuizSession(Base):
    __tablename__ = 'active_quiz_sessions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('categories.id'))
    session_type: Mapped[str] = mapped_column(String, nullable=False)
    current_question_index: Mapped[int] = mapped_column(
        Integer, default=0)
    questions_answered: Mapped[int] = mapped_column(
        Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    start_time_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    timer_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped['User'] = relationship(
        'User', back_populates='active_quiz_session')
    category: Mapped['Category'] = relationship(
        'Category', back_populates='active_quiz_session')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'current_question_index >= 0',
            name='check_current_question_index_non_negative'),
        CheckConstraint(
            'questions_answered >= 0',
            name='check_questions_answered_non_negative')
    )

    def __repr__(self) -> str:
        return f'<ActiveQuizSession(id={self.id}, ' \
            f'user_id={self.user_id}, ' \
            f'active={self.is_active}, ' \
            f'questions_answered={self.questions_answered})>'


class UserStatistics(Base):
    __tablename__ = 'user_statistics'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    questions_answered: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    accuracy_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    average_time_per_question: Mapped[float] = mapped_column(
        Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(), onupdate=func.now())

    # Relationship
    user: Mapped['User'] = relationship(
        'User', back_populates='user_statistics')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'questions_answered >= 0',
            name='check_questions_answered_non_negative'),
        CheckConstraint(
            'correct_answers >= 0',
            name='check_correct_answered_non_negative'),
        CheckConstraint(
            'accuracy_percentage >= 0 AND accuracy_percentage <= 100',
            name='check_accuracy_percentage_range'),
        CheckConstraint(
            'current_streak >= 0',
            name='check_current_streak_non_negative'),
        CheckConstraint(
            'best_streak >= 0',
            name='check_best_streak_non_negative'),
        CheckConstraint(
            'best_streak >= current_streak',
            name='check_best_streak_not_less_than_current'),
        CheckConstraint(
            'correct_answers <= questions_answered',
            name='check_correct_not_exceed_answered'),
        CheckConstraint(
            'average_time_per_question >= 0.0',
            name='check_average_time_non_negative'),
    )

    def __repr__(self) -> str:
        return f'<UserStatistics(id={self.id}, user_id={self.user_id}, ' \
            f'percentage={self.accuracy_percentage:.1f}%, ' \
            f'streak={self.current_streak})>'


class QuestionHistory(Base):
    __tablename__ = 'question_histories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('questions.id'))
    times_seen: Mapped[int] = mapped_column(Integer, default=0)
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    last_seen_at:  Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    cooldown_until_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(), onupdate=func.now())

    # Relationship
    user: Mapped['User'] = relationship(
        'User', back_populates='question_histories')
    question: Mapped['Question'] = relationship(
        'Question', back_populates='question_histories')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'times_seen >= 0', name='check_times_seen_not_negative'),
        CheckConstraint(
            'last_seen_at >= first_seen_at',
            name='check_last_seen_after_first_seen')
    )

    def __repr__(self) -> str:
        return f'<QuestionHistory(id={self.id}, user_id={self.user_id}, ' \
            f' question_id={self.question_id}, times_seen={self.times_seen})>'
# /
