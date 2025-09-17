from pydantic import BaseModel, Field, field_validator


class AnswerSubmissionRequest(BaseModel):
    attempt_id: int
    question_id: int
    selected_answer: str = Field(min_length=1, max_length=1, description='Correct Answer')

    @field_validator('selected_answer', mode='before')
    @classmethod
    def convert_to_lowercase(cls, v):
        v = str(v).lower()
        if v not in ['a', 'b', 'c', 'd']:
            raise ValueError('Correct answer must be a, b, c, or d')
        return v
