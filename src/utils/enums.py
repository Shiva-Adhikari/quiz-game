from enum import Enum


class DifficultyLevel(str, Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'


class SessionStatus(str, Enum):
    NOT_STARTED = "not_started"
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"
    ABANDONED = 'abandoned'


class SessionType(str, Enum):
    RANDOM = "random"
    CATEGORY = "category"
    DAILY_CHALLENGE = "daily_challenge"


class ChallengeType(str, Enum):
    SCORE_TARGET = "score_target"
    QUESTIONS_ANSWERED = "questions_answered"
    ACCURACY_TARGET = "accuracy_target"
    STREAK_TARGET = "streak_target"
    PERFECT_QUIZ = "perfect_quiz"


class UserSessionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class ChallengeStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
