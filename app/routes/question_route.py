# app/routes/question_route.py

from fastapi import APIRouter
from app.services.question_service import get_next_question

router = APIRouter(prefix="/question", tags=["question"])

@router.get("/next")
def get_next_question_route(score: float):
    """
    Get the next pronunciation practice question based on score.
    Expected score range: 0.0 to 1.0
    """
    result = get_next_question(score)

    return {
        "difficulty": result["difficulty"],
        "question_text": result["question"]["text"],
        "question_id": result["question"]["id"]
    }