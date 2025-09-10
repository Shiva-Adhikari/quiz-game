# Standard library imports
from typing import Optional, TYPE_CHECKING
from datetime import datetime

# Third-party imports
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    ForeignKey, Integer, Boolean,
    DateTime, Enum as SQLEnum, UniqueConstraint, String, func
)

# Local imports
from src.core.database import Base
from src.utils.enums import SessionStatus, SessionType, DifficultyLevel
if TYPE_CHECKING:
    from src.models.questions import Question


# from src.models.authentication import User


# TABLE 1: MAIN QUIZ SESSION (Merged ActiveQuizSession + QuizSession)
class QuizSession(Base):
    __tablename__ = 'quiz_sessions'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True)
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True)

    '''
    # Quiz Configuration
    # session_type: Mapped[SessionType] = mapped_column(SQLEnum(SessionType), nullable=False)
    # difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        # SQLEnum(DifficultyLevel), nullable=False, default=DifficultyLevel.EASY)
    '''

    # Quiz Configuration
    session_type: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty_level: Mapped[str] = mapped_column(String(20), nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    # Progress Tracking
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    questions_answered: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)

    # Status & State
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus), nullable=False, default=SessionStatus.STARTED)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now())
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    timer_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    total_time_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # Gamification
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    coins_earned: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    questions: Mapped[list['Question']] = relationship(
        'Question', secondary='quiz_session_questions',  # ← ADDED secondary table
        back_populates='quiz_sessions'  # ← CHANGED from 'quiz_session' to 'quiz_sessions'
    )
    quiz_session_question: Mapped[list['QuizSessionQuestion']] = relationship("QuizSessionQuestion", back_populates="question")
    quiz_session_question: Mapped[list['QuizSessionQuestion']] = relationship("QuizSessionQuestion", back_populates="quiz_session")   # , cascade="all, delete-orphan"

    '''
    # from src.models.questions import Question
    # questions: Mapped['Question'] = relationship(
        # "Question", back_populates="quiz_session")
    # user: Mapped['User'] = relationship("User", back_populates="quiz_sessions")
    # answers: Mapped[list["UserAnswer"]] = relationship("UserAnswer", back_populates="quiz_session")    # cascade="all, delete-orphan"
    '''

    @property
    def score_percentage(self) -> float:
        """Calculate score percentage"""
        if self.questions_answered == 0:
            return 0.0
        return (self.correct_answers / self.questions_answered) * 100

    @property
    def is_completed(self) -> bool:
        """Check if quiz is completed"""
        return self.status == SessionStatus.COMPLETED

    @property
    def is_in_progress(self) -> bool:
        """Check if quiz is in progress"""
        return self.status == SessionStatus.IN_PROGRESS

    @property
    def remaining_questions(self) -> int:
        """Get remaining questions count"""
        return self.total_questions - self.questions_answered

    def mark_as_completed(self):
        """Mark session as completed"""
        self.status = SessionStatus.COMPLETED
        self.completed_at = func.now()
        self.is_active = False

    def mark_as_abandoned(self):
        """Mark session as abandoned"""
        self.status = SessionStatus.ABANDONED
        self.is_active = False


# TABLE 2: LINK QUESTIONS TO SESSIONS (NEW - This was missing!)
class QuizSessionQuestion(Base):
    __tablename__ = 'quiz_session_questions'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    quiz_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('quiz_sessions.id', ondelete='CASCADE'), index=True)
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('questions.id', ondelete='CASCADE'), index=True)

    # Question Order in Session
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3... 10

    # Status
    is_answered: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    quiz_session: Mapped['QuizSession'] = relationship("QuizSession")
    question: Mapped['Question'] = relationship("Question")

    # Unique constraint: One question can appear only once per session
    __table_args__ = (
        UniqueConstraint(
            'quiz_session_id', 'question_id', name='unique_session_question'),
        UniqueConstraint(
            'quiz_session_id', 'question_order', name='unique_session_order'),
    )


# TABLE 3: USER ANSWERS (Your existing table - improved)
class UserAnswer(Base):
    __tablename__ = 'user_answers'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    quiz_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('quiz_sessions.id', ondelete='CASCADE'), index=True)
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('questions.id', ondelete='CASCADE'), index=True)

    # Answer Data
    user_answer: Mapped[str] = mapped_column(String(1), nullable=False)  # 'A', 'B', 'C', 'D'
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timing
    time_taken_seconds: Mapped[int] = mapped_column(Integer, default=0)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    '''
    # Relationships
    # quiz_session = relationship("QuizSession", back_populates="answers")
    # question = relationship("Question", back_populates="user_answers")
    '''

    # Unique constraint: One answer per question per session
    __table_args__ = (
        UniqueConstraint('quiz_session_id', 'question_id', name='unique_session_answer'),
    )
