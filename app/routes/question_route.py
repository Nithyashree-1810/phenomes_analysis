from fastapi import APIRouter
from app.services.question_service import next_question_level
from app.agents.qb_agent import generate_question

router = APIRouter(prefix="/question", tags=["question"])


@router.get("/next")
def get_next_question(score: int):
    """
    Return the next practice question based ONLY on score.
    No weak phoneme logic is used.
    """
    # Decide level based on score thresholds
    level = next_question_level(score)

    # Generate sentence for the chosen level
    question = generate_question(level, weak_phonemes=None)

    return {
        "difficulty": level,
        "practice_sentence": question
    }