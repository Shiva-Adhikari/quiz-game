# Standard library imports
from typing import Optional, List
from pydantic import (
    BaseModel,
    # Field
)
from datetime import datetime

# Local imports
from src.utils.enums import (
    SessionType, DifficultyLevel,
    # SessionStatus
)


# class StartQuizRequest(BaseModel):
#     category_id: Optional[int] = None
#     session_type: str = SessionType.RANDOM.value  # quick_quiz, practice, challenge, random
#     difficulty_level: str = DifficultyLevel.EASY.value   # easy, medium, hard
#     total_questions: int = 10
#     time_limit_minutes: Optional[int] = None


class StartQuizRequest(BaseModel):
    category_id: Optional[int]
    session_type: str
    difficulty_level: str
    total_questions: int
    time_limit_minutes: Optional[int]


class QuestionResponse(BaseModel):
    question_id: int
    question_order: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    # Note: We DON'T send correct_answer to prevent cheating


class StartQuizResponse(BaseModel):
    quiz_session_id: int
    session_status: str
    total_questions: int
    current_question: int
    questions: List[QuestionResponse]
    timer_expires_at: Optional[datetime] = None
    message: str


class SubmitAnswerRequest(BaseModel):
    quiz_session_id: int
    question_id: int
    user_answer: str  # 'A', 'B', 'C', or 'D'


class SubmitAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None
    current_score: int
    questions_answered: int
    total_questions: int
    score_percentage: float
    session_completed: bool
    next_question_order: Optional[int] = None
    message: str


class QuizProgressResponse(BaseModel):
    quiz_session_id: int
    status: str
    current_question: int
    questions_answered: int
    total_questions: int
    correct_answers: int
    score_percentage: float
    time_remaining_seconds: Optional[int] = None
    is_completed: bool
