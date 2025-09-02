# Standard library imports
from typing import Optional
from pydantic import BaseModel, Field

# Local imports
from src.models.questions import DifficultyLevel


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description='Category name')
    description: str = Field(..., min_length=1, max_length=500, description='Category description')
    difficulty_multiplier: float = Field(
        default=1.0, ge=0.1, le=10.0, description='Set number according to difficult level')
    is_active: bool = Field(default=True, description='Whether the category is active')


class QuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=1, max_length=500, description='Question')
    difficulty_level: DifficultyLevel = Field(..., description='Question difficulty level')
    correct_answer: str = Field(..., min_length=1, max_length=50, description='Correct Answer')
    option_a: str = Field(..., min_length=1, max_length=50, description='Option A')
    option_b: str = Field(..., min_length=1, max_length=50, description='Option B')
    option_c: str = Field(..., min_length=1, max_length=50, description='Option C')
    option_d: str = Field(..., min_length=1, max_length=50, description='Option D')
    is_active: bool = Field(default=True, description='Whether the question is active')


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description='Category name')
    description: Optional[str] = Field(None, min_length=1, max_length=500, description='Category description')
    difficulty_multiplier: Optional[float] = Field(
        None, ge=0.1, le=10.0, description='Set number according to difficult level')
    is_active: Optional[bool] = Field(None, description='Whether the category is active')



class QuestionUpdate(BaseModel):
    question_text: Optional[str] = Field(None, min_length=1, max_length=500, description='Question')
    difficulty_level: Optional[DifficultyLevel] = Field(None, description='Question difficulty level')
    correct_answer: Optional[str] = Field(None, min_length=1, max_length=50, description='Correct Answer')
    option_a: Optional[str] = Field(None, min_length=1, max_length=50, description='Option A')
    option_b: Optional[str] = Field(None, min_length=1, max_length=50, description='Option B')
    option_c: Optional[str] = Field(None, min_length=1, max_length=50, description='Option C')
    option_d: Optional[str] = Field(None, min_length=1, max_length=50, description='Option D')
    is_active: Optional[bool] = Field(None, description='Whether the question is active')


# Response schemas for better API documentation
class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str
    difficulty_multiplier: float
    is_active: bool
    created_at: str
    questions_count: Optional[int] = None

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    id: int
    category_id: int
    question_text: str
    difficulty_level: str
    correct_answer: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class PaginationResponse(BaseModel):
    current_page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool
