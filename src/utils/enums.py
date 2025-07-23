from enum import Enum


class DifficultyLevel(Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'


class SessionStatus(str, Enum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
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


# ##################################################

class AnswerOption(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class RoomStatus(str, Enum):
    STARTING = 'starting'
    ACTIVE = 'active'
    WAITING = 'waiting'
    FINISHED = 'finished'
    CANCELLED = 'cancelled'


class RoomType(str, Enum):
    SYSTEM_CREATED = 'system_created'
    USER_CREATED = 'user_created'
    TOURNAMENT = 'tournament'
    PRIVATE = 'private'
