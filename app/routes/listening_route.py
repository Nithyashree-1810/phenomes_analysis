"""
app/routes/listening_route.py
GET /listening/module — Generate a listening passage, audio, and questions.
"""
import logging
from unittest import result
from app.db import session
from app.db.session import get_db
from app.models.listening_model import ListeningSession
from app.models.listening_model import ListeningSession
from fastapi import APIRouter, Depends, Query
from app.services.listening_question_service import generate_listening_module
from app.schema.pronun_schema import ListeningModuleOut
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/listening", tags=["Listening"])


@router.get(
    "/module",
    response_model=ListeningModuleOut,
    summary="Generate listening module",
)
async def get_listening_module(
    difficulty: str = Query(default="medium", pattern="^(easy|medium|hard)$"),
    num_questions: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
):
   result = generate_listening_module(difficulty=difficulty, num_questions=num_questions)

    # Save to DB so evaluate can fetch it later
   session = ListeningSession(
        session_id=result["session_id"],
        passage=result["passage"],
        questions=result["listening_questions"],
        user_transcript="",       # filled after evaluation
        similarity_score=0.0,     # filled after evaluation
        audio_filename="",
    )
   db.add(session)
   db.commit()

   return result
"""
app/routes/listening_route.py
GET  /listening/module   — Generate a listening passage, audio, and questions.
POST /listening/evaluate — Evaluate MCQ answers using CEFRGradingService.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db.session import get_db
from app.models.listening_model import ListeningSession
from app.schema.listening_schema import ListeningEvaluateIn, ListeningEvaluateOut
from app.schema.pronun_schema import ListeningModuleOut
from app.services.listening_question_service import (
    evaluate_answers_batch,
    generate_listening_module
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/listening", tags=["Listening"])


@router.get(
    "/module",
    response_model=ListeningModuleOut,
    summary="Generate listening module",
)
async def get_listening_module(
    difficulty: str = Query(default="medium", pattern="^(easy|medium|hard)$"),
    num_questions: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
):
    result = generate_listening_module(difficulty=difficulty, num_questions=num_questions)

    db_session = ListeningSession(
        session_id=result["session_id"],
        passage=result["passage"],
        questions=result["listening_questions"],  # stored as JSON
        audio_filename=result.get("audio_url", ""),
        user_transcript="",
        similarity_score=0.0,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    logger.info("Listening session created: %s", result["session_id"])
    return result


@router.post(
    "/evaluate",
    response_model=ListeningEvaluateOut,
    summary="Evaluate MCQ answers for a listening session",
)
async def evaluate_listening_answers(
    payload: ListeningEvaluateIn,
    db: Session = Depends(get_db),
):
    # Fetch the session
    db_session = (
        db.query(ListeningSession)
        .filter(ListeningSession.session_id == payload.session_id)
        .first()
    )
    if not db_session:
        raise HTTPException(status_code=404, detail="Listening session not found.")

    # Build answer dicts enriched with correct_option + cefr_level from stored questions
    stored_questions: list[dict] = db_session.questions  # already parsed JSON
    question_map = {str(q["id"]): q for q in stored_questions}

    enriched_answers = []
    for ans in payload.answers:
        q = question_map.get(str(ans.question_id))
        if not q:
            raise HTTPException(
                status_code=422,
                detail=f"question_id {ans.question_id} not found in session.",
            )
        
        difficulty_to_cefr = {
        "easy":   "A2",
        "medium": "B1",
        "hard":   "B2",
    }
        cefr_level = q.get("cefr_level") or difficulty_to_cefr.get(
        q.get("difficulty", "medium"), "B1"
    )
        enriched_answers.append({
            "question_id":      ans.question_id,
            "question":         q["question"],
            "selected_option":  ans.selected_option,
            "correct_option":   q["correct_option"],
            "cefr_level":       cefr_level,          # comes from stored question
            "difficulty_score": q.get("difficulty_score"),
        })

    evaluation = evaluate_answers_batch(db_session.passage, enriched_answers)

    # Persist grading result back to the session row
    db_session.results           = evaluation["results"]
    db_session.cefr_level        = evaluation["grading"]["cefr_level"]
    db_session.ability_score     = evaluation["grading"]["ability_score"]
    db_session.accuracy_by_level = evaluation["grading"]["accuracy_by_level"]
    db_session.evaluated_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(
        "Session %s evaluated → CEFR: %s | ability: %.4f",
        payload.session_id,
        evaluation["grading"]["cefr_level"],
        evaluation["grading"]["ability_score"],
    )
    return evaluation