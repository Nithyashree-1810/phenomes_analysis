<<<<<<< HEAD
import uuid
=======
# routes/question_route.py
from fastapi import APIRouter, Query
from app.services.pronun_questions_service import PronunciationQuestionsService

service= PronunciationQuestionsService()
>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

<<<<<<< HEAD
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
=======
@router.get("/next")
def get_next_question_route(score: float = Query(..., ge=0, le=100)):
    """
    Generate next pronunciation question dynamically based on user score.
    """
    questions = service.generate_questions(score, num_questions=1)
    question = questions[0] if questions else {"difficulty": "easy", "question": "Practice reading aloud."}
>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f

    return {
        "difficulty": q.get("difficulty", "easy"),
        "question_text": q.get("question", ""),
    }