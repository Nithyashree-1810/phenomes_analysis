
from fastapi import APIRouter, Query
from app.services.pronun_questions_service import PronunciationQuestionsService
from app.schema.pronun_schema import QuestionOut

router = APIRouter(prefix="/question", tags=["Questions"])
_service = PronunciationQuestionsService()


@router.get(
    "/next",
    user_id:uuid.UU
    response_model=QuestionOut,
    summary="Get the next pronunciation practice question",
)
def get_next_question(
    score: float = Query(..., ge=0, le=100, description="User's current pronunciation score"),
):
    questions = _service.generate_questions(score, num_questions=1)
    q = questions[0] if questions else {"difficulty": "easy", "question": "Practice reading aloud."}
    return {"difficulty": q.get("difficulty", "easy"), "question_text": q.get("question", "")}
