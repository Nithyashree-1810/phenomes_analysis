import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db.session import get_db
from app.models.listening_model import ListeningSession
from app.schema.listening_schema import (
    ListeningEvaluateIn,
    ListeningEvaluateOut,
    ListeningModuleOut,
)
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
    try:
        result = generate_listening_module(difficulty=difficulty, num_questions=num_questions)
    except Exception as exc:
        logger.error("generate_listening_module failed: %s", exc)
        return JSONResponse(
            status_code=200,
            content={
                "session_id": "",
                "passage": "",
                "audio_url": "",
                "listening_questions": [],
                "error": str(exc),
            },
        )

    db_session = ListeningSession(
        session_id=result["session_id"],
        passage=result["passage"],
        questions=result["listening_questions"],
        audio_filename=result.get("audio_url", ""),
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    safe_questions = [
        {k: v for k, v in q.items() if k != "correct_option"}
        for q in result["listening_questions"]
    ]

    logger.info("Listening session created: %s", result["session_id"])
    return {
        "session_id":          result["session_id"],
        "passage":             result["passage"],
        "audio_url":           result.get("audio_url", ""),
        "listening_questions": safe_questions,
    }


@router.post(
    "/evaluate",
    response_model=ListeningEvaluateOut,
    summary="Evaluate MCQ answers for a listening session",
)
async def evaluate_listening_answers(
    payload: ListeningEvaluateIn,
    db: Session = Depends(get_db),
):
    db_session = (
        db.query(ListeningSession)
        .filter(ListeningSession.session_id == payload.session_id)
        .first()
    )
    if not db_session:
        raise HTTPException(status_code=404, detail="Listening session not found.")

    stored_questions: list[dict] = db_session.questions
    question_map = {str(q["id"]): q for q in stored_questions}

    enriched_answers = []
    for ans in payload.answers:
        q = question_map.get(str(ans.question_id))
        if not q:
            raise HTTPException(
                status_code=422,
                detail=f"question_id {ans.question_id} not found in session.",
            )

        difficulty_to_cefr = {"easy": "A2", "medium": "B1", "hard": "B2"}
        cefr_level = q.get("cefr_level") or difficulty_to_cefr.get(
            q.get("difficulty", "medium"), "B1"
        )
        enriched_answers.append({
            "question_id":      ans.question_id,
            "question":         q["question"],
            "selected_option":  ans.selected_option,
            "correct_option":   q["correct_option"],
            "cefr_level":       cefr_level,
            "difficulty_score": q.get("difficulty_score"),
        })

    evaluation = evaluate_answers_batch(db_session.passage, enriched_answers)

    db_session.results           = evaluation["results"]
    db_session.cefr_level        = evaluation["grading"]["cefr_level"]
    db_session.ability_score     = evaluation["grading"]["ability_score"]
    db_session.accuracy_by_level = evaluation["grading"]["accuracy_by_level"]
    db_session.evaluated_at      = datetime.now(timezone.utc)
    db.commit()

    logger.info(
        "Session %s evaluated → CEFR: %s | ability: %.4f",
        payload.session_id,
        evaluation["grading"]["cefr_level"],
        evaluation["grading"]["ability_score"],
    )
    return evaluation