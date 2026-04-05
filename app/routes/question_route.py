import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repo.pronunciation_repo import get_or_create_profile
from app.schema.pronun_schema import QuestionOut
from app.services.pronun_questions_service import PronunciationQuestionsService

router = APIRouter(prefix="/question", tags=["Questions"])
_service = PronunciationQuestionsService()

_FALLBACK = {"difficulty": "easy", "question": "Practice reading aloud."}


@router.get(
    "/next",
    response_model=QuestionOut,
    summary="Get the next pronunciation practice question",
)
def get_next_question(
    user_id: uuid.UUID = Query(..., description="User's UUID"),
    db: Session = Depends(get_db),
):
    profile = get_or_create_profile(db, user_id)
    score = float(profile.overall_score_avg or 0)

    questions = _service.generate_questions(score, num_questions=1)
    q = questions[0] if questions else _FALLBACK

    # Save as reference text for /test/analyze
    profile.current_question = q.get("question", _FALLBACK["question"])
    db.commit()

    return {
        "difficulty": q.get("difficulty", "easy"),
        "question_text": q.get("question", ""),
    }