from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class RoomCreate(BaseModel):
    room_name: str
    max_players: int = 4
    category_id: Optional[int] = None
    difficulty_level: str = "medium"
    total_questions: int = 10
    time_per_question: int = 30
    is_public: bool = True
    room_password: Optional[str] = None
    
    @field_validator('max_players')
    @classmethod
    def validate_max_players(cls, v):
        if v < 2 or v > 6:
            raise ValueError('Max players must be between 2 and 6')
        return v
    
    @field_validator('difficulty_level')
    @classmethod
    def validate_difficulty(cls, v):
        if v not in ['easy', 'medium', 'hard']:
            raise ValueError('Difficulty must be easy, medium, or hard')
        return v
    
    @field_validator('total_questions')
    @classmethod
    def validate_questions(cls, v):
        if v < 5 or v > 50:
            raise ValueError('Total questions must be between 5 and 50')
        return v


class RoomResponse(BaseModel):
    id: int
    room_code: str
    room_name: str
    current_players: int
    max_players: int
    status: str
    difficulty_level: str
    host_user_id: int
    is_public: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ParticipantResponse(BaseModel):
    id: int
    user_id: int
    is_ready: bool
    is_host: bool
    total_score: int
    correct_answers: int
    wrong_answers: int
    
    model_config = {"from_attributes": True}


class RoomDetailResponse(BaseModel):
    room: RoomResponse
    participants: List[ParticipantResponse]


class JoinRoomRequest(BaseModel):
    room_code: str
    password: Optional[str] = None


class PlayerReadyRequest(BaseModel):
    is_ready: bool


class SubmitAnswerRequest(BaseModel):
    question_id: int
    selected_answer: str
    time_taken: float
    
    @field_validator('selected_answer')
    @classmethod
    def validate_answer(cls, v):
        if v not in ['A', 'B', 'C', 'D']:
            raise ValueError('Answer must be A, B, C, or D')
        return v
    
    @field_validator('time_taken')
    @classmethod
    def validate_time(cls, v):
        if v < 0:
            raise ValueError('Time taken cannot be negative')
        return v


class QuestionResponse(BaseModel):
    id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    time_limit: int
    question_index: int


class GameResultResponse(BaseModel):
    question_id: int
    correct_answer: str
    player_scores: List[dict]
    leaderboard: List[dict]
