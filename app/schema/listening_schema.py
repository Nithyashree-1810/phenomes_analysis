# app/schema/listening_schema.py
from pydantic import BaseModel, Field


class MCQOption(BaseModel):
    A: str
    B: str
    C: str
    D: str


class ListeningQuestionOut(BaseModel):
    """Returned to client — correct_option intentionally excluded."""
    id: int
    cefr_level: str
    question: str
    options: MCQOption


class ListeningQuestionStored(BaseModel):
    """Internal schema — stored in DB with correct_option."""
    id: int
    cefr_level: str
    question: str
    options: MCQOption
    correct_option: str

class ListeningModuleOut(BaseModel):
    session_id: str
    passage: str
    audio_url: str
    listening_questions: list[ListeningQuestionOut]


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