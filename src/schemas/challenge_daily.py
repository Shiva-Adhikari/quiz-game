from pydantic import BaseModel


class AnswerSubmissionRequest(BaseModel):
    attempt_id: int
    question_id: int
    selected_answer: str  # 'A', 'B', 'C', or 'D'
