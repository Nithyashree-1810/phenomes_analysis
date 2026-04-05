import json
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.listening_model import ListeningSession
from app.services.listening_service import (
    generate_listening_module,
    evaluate_answers_batch,
)
from app.schema.pronun_schema import ListeningModuleOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/listening", tags=["Listening"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class AnswerItem(BaseModel):
    question_id: int
    question: str
    answer: str          # user's text answer


class BatchEvaluateRequest(BaseModel):
    session_id: str
    passage: str
    answers: list[AnswerItem]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get(
    "/module",
    response_model=ListeningModuleOut,
    summary="Generate listening module",
)
async def get_listening_module(
    difficulty: str = "medium",
    num_questions: int = 3,
):
    return generate_listening_module(difficulty=difficulty, num_questions=num_questions)


@router.post(
    "/evaluate",
    summary="Evaluate all answers for a listening session in one call",
)
async def evaluate_listening_answers(
    payload: BatchEvaluateRequest,
    db: Session = Depends(get_db),
):
    """
    Submit all answers at once. One LLM call evaluates everything.

    Request:
    {
        "session_id": "ef99b746-...",
        "passage": "As the sun began to set...",
        "answers": [
            {"question_id": 1, "question": "What did Sarah see?", "answer": "The sunset"},
            {"question_id": 2, "question": "What was the family doing?", "answer": "Having a picnic"},
            {"question_id": 3, "question": "How did Sarah feel?", "answer": "Warm and happy"}
        ]
    }
    """
    if not payload.answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No answers provided.",
        )

    try:
        results = evaluate_answers_batch(
            passage=payload.passage,
            answers=[a.model_dump() for a in payload.answers],
        )

        # Compute overall score
        total_score = round(
            sum(r.get("score", 0) for r in results) / len(results), 2
        )

        # Persist session
        session = ListeningSession(
            session_id=payload.session_id,
            passage=payload.passage,
            questions=[a.model_dump() for a in payload.answers],
            similarity_score=total_score,
        )
        db.add(session)
        db.commit()

        return {
            "session_id": payload.session_id,
            "total_score": total_score,
            "results": results,
        }

    except Exception as exc:
        db.rollback()
        logger.exception("evaluate_listening_answers failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {exc}",
        )