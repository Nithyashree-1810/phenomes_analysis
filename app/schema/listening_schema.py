# app/schema/listening_schema.py
from pydantic import BaseModel, Field


class MCQAnswerIn(BaseModel):
    question_id: int
    selected_option: str = Field(..., pattern="^[A-D]$")
    
    model_config = {"extra": "forbid"}

class ListeningEvaluateIn(BaseModel):
    session_id: str
    answers: list[MCQAnswerIn]

    model_config = {"extra": "forbid"}


class QuestionResult(BaseModel):
    question_id: int
    correct: bool
    feedback: str


class GradingOut(BaseModel):
    cefr_level: str
    ability_score: float
    accuracy_by_level: dict[str, float]


class ListeningEvaluateOut(BaseModel):
    results: list[QuestionResult]
    grading: GradingOut