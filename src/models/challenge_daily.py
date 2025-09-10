from sqlalchemy import String, Boolean, DateTime, Date, Float, Text, ForeignKey, Enum, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from typing import List, Optional
from src.core.database import Base
from src.utils.enums import ChallengeStatus, DifficultyLevel


# 1. DAILY_CHALLENGES - Which challenge is active for each date
class DailyChallenge(Base):
    __tablename__ = 'daily_challenges'

    id: Mapped[int] = mapped_column(primary_key=True)
    challenge_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    challenge_type: Mapped[str] = mapped_column(String(50))  # survival_mode, perfect_score, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Override by admin
    # is_override: Mapped[bool] = mapped_column(Boolean, default=False)
    # created_by_admin: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # override_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationship to attempts
    attempts: Mapped[List["UserChallengeAttempt"]] = relationship(back_populates="daily_challenge")


# 2. USER_CHALLENGE_ATTEMPTS - Track user attempts and progress
class UserChallengeAttempt(Base):
    __tablename__ = 'user_challenge_attempts'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)  # Foreign key to your users table
    daily_challenge_id: Mapped[int] = mapped_column(ForeignKey('daily_challenges.id'))

    # Challenge progress tracking
    status: Mapped[ChallengeStatus] = mapped_column(Enum(ChallengeStatus), default=ChallengeStatus.NOT_STARTED)
    questions_answered: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    wrong_answers: Mapped[int] = mapped_column(Integer, default=0)

    # Challenge-specific data
    current_streak: Mapped[int] = mapped_column(Integer, default=0)  # For streak challenges
    max_streak: Mapped[int] = mapped_column(Integer, default=0)
    time_taken: Mapped[float] = mapped_column(Float, default=0.0)  # In seconds

    # Results
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_successful: Mapped[bool] = mapped_column(Boolean, default=False)
    final_score: Mapped[int] = mapped_column(Integer, default=0)
    accuracy_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    daily_challenge: Mapped["DailyChallenge"] = relationship(back_populates="attempts")


# 3. USER_CHALLENGE_STATS - Overall user statistics
class UserChallengeStat(Base):
    __tablename__ = 'user_challenge_stats'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    # Overall stats
    total_challenges_attempted: Mapped[int] = mapped_column(Integer, default=0)
    total_challenges_completed: Mapped[int] = mapped_column(Integer, default=0)
    total_challenges_successful: Mapped[int] = mapped_column(Integer, default=0)

    # Streak tracking
    current_daily_streak: Mapped[int] = mapped_column(Integer, default=0)  # Consecutive days played
    longest_daily_streak: Mapped[int] = mapped_column(Integer, default=0)

    # Performance metrics
    total_questions_answered: Mapped[int] = mapped_column(Integer, default=0)
    total_correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    overall_accuracy: Mapped[float] = mapped_column(Float, default=0.0)

    # Challenge-specific counters
    survival_mode_completed: Mapped[int] = mapped_column(Integer, default=0)
    perfect_score_completed: Mapped[int] = mapped_column(Integer, default=0)
    speed_challenge_completed: Mapped[int] = mapped_column(Integer, default=0)
    lightning_round_completed: Mapped[int] = mapped_column(Integer, default=0)
    streak_target_completed: Mapped[int] = mapped_column(Integer, default=0)
    marathon_mode_completed: Mapped[int] = mapped_column(Integer, default=0)

    # Scoring
    total_points_earned: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    last_played_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# 4. QUESTIONS - Your existing questions table (example structure)
# class Question(Base):
#     __tablename__ = 'questions'

#     id: Mapped[int] = mapped_column(primary_key=True)
#     question_text: Mapped[str] = mapped_column(Text)
#     option_a: Mapped[str] = mapped_column(String(255))
#     option_b: Mapped[str] = mapped_column(String(255))
#     option_c: Mapped[str] = mapped_column(String(255))
#     option_d: Mapped[str] = mapped_column(String(255))
#     correct_answer: Mapped[str] = mapped_column(String(1))  # A, B, C, or D

#     # Additional fields for challenge system
#     category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
#     difficulty: Mapped[DifficultyLevel] = mapped_column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM)
#     points: Mapped[int] = mapped_column(Integer, default=10)

#     is_active: Mapped[bool] = mapped_column(Boolean, default=True)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# 5. CHALLENGE_TYPES - Master table of challenge configurations
class ChallengeType(Base):
    __tablename__ = 'challenge_types'

    id: Mapped[int] = mapped_column(primary_key=True)
    challenge_key: Mapped[str] = mapped_column(String(50), unique=True)  # survival_mode, perfect_score
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)

    # Challenge settings
    difficulty: Mapped[DifficultyLevel] = mapped_column(Enum(DifficultyLevel))
    estimated_time_minutes: Mapped[int] = mapped_column(Integer, default=5)
    max_questions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = unlimited
    time_limit_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = no time limit

    # Scoring settings
    base_points: Mapped[int] = mapped_column(Integer, default=100)
    bonus_multiplier: Mapped[float] = mapped_column(Float, default=1.0)

    # Challenge-specific settings (JSON-like text field)
    settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Store JSON for challenge-specific config

    # Selection weight for daily picker
    selection_weight: Mapped[int] = mapped_column(Integer, default=10)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# 6. CHALLENGE_LEADERBOARDS - Daily/weekly rankings (Optional)
class ChallengeLeaderboard(Base):
    __tablename__ = 'challenge_leaderboards'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    daily_challenge_id: Mapped[int] = mapped_column(ForeignKey('daily_challenges.id'))

    # Ranking data
    score: Mapped[int] = mapped_column(Integer)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # For speed-based ranking

    # Period tracking
    leaderboard_date: Mapped[date] = mapped_column(Date, index=True)
    week_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For weekly leaderboards
    month_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For monthly leaderboards

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# 7. USER_ACHIEVEMENTS - Badges and milestones (Optional)
class UserAchievement(Base):
    __tablename__ = 'user_achievements'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    achievement_key: Mapped[str] = mapped_column(String(50))  # first_perfect_score, streak_10_days
    achievement_name: Mapped[str] = mapped_column(String(100))
    achievement_description: Mapped[str] = mapped_column(Text)

    # Achievement metadata
    points_awarded: Mapped[int] = mapped_column(Integer, default=0)
    badge_icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Icon filename or URL
    rarity: Mapped[str] = mapped_column(String(20), default='common')  # common, rare, epic, legendary

    # Earning details
    earned_date: Mapped[date] = mapped_column(Date)
    challenge_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Which challenge earned this

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# 8. CHALLENGE_SESSIONS - Detailed session data for analytics (Optional)
class ChallengeSession(Base):
    __tablename__ = 'challenge_sessions'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_challenge_attempt_id: Mapped[int] = mapped_column(ForeignKey('user_challenge_attempts.id'))

    # Session tracking
    session_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    session_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    questions_in_session: Mapped[int] = mapped_column(Integer, default=0)

    # Analytics data
    average_response_time: Mapped[float] = mapped_column(Float, default=0.0)
    device_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # mobile, desktop, tablet
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# Example of how to create all tables
# def create_tables(engine):
    # """Create all tables in the database"""
    # Base.metadata.create_all(engine)

'''
# Example of initial data population
def populate_challenge_types(session):
    """Populate the challenge_types table with initial data"""

    challenge_types_data = [
        {
            'challenge_key': 'survival_mode',
            'name': 'Survival Mode',
            'description': 'Keep playing until you get 3 questions wrong',
            'difficulty': DifficultyLevel.MEDIUM,
            'estimated_time_minutes': 7,
            'base_points': 150,
            'selection_weight': 15,
            'settings': '{"max_wrong_answers": 3}'
        },
        {
            'challenge_key': 'perfect_score',
            'name': 'Perfect Score',
            'description': 'Get 100% accuracy on today\'s quiz',
            'difficulty': DifficultyLevel.HARD,
            'estimated_time_minutes': 5,
            'max_questions': 10,
            'base_points': 200,
            'selection_weight': 10,
            'settings': '{"required_accuracy": 100}'
        },
        {
            'challenge_key': 'speed_challenge',
            'name': 'Speed Challenge',
            'description': 'Answer 10 questions in under 2 minutes',
            'difficulty': DifficultyLevel.MEDIUM,
            'estimated_time_minutes': 2,
            'max_questions': 10,
            'time_limit_seconds': 120,
            'base_points': 175,
            'selection_weight': 20
        },
        {
            'challenge_key': 'lightning_round',
            'name': 'Lightning Round',
            'description': 'Answer as many questions as possible in 60 seconds',
            'difficulty': DifficultyLevel.EASY,
            'estimated_time_minutes': 1,
            'time_limit_seconds': 60,
            'base_points': 100,
            'selection_weight': 25
        },
        {
            'challenge_key': 'streak_target',
            'name': 'Streak Target',
            'description': 'Maintain a 5-question streak',
            'difficulty': DifficultyLevel.EASY,
            'estimated_time_minutes': 3,
            'base_points': 125,
            'selection_weight': 20,
            'settings': '{"target_streak": 5}'
        },
        {
            'challenge_key': 'marathon_mode',
            'name': 'Marathon Mode',
            'description': 'Complete a 25-question endurance quiz',
            'difficulty': DifficultyLevel.HARD,
            'estimated_time_minutes': 12,
            'max_questions': 25,
            'base_points': 250,
            'selection_weight': 10
        }
    ]

    for challenge_data in challenge_types_data:
        challenge_type = ChallengeType(**challenge_data)
        session.add(challenge_type)

    session.commit()
'''
