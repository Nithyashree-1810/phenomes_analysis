import json
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.listening_model import ListeningSession
from app.services.listening_service import evaluate_answers_batch
from app.services.transcription_service import transcribe_audio
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/listening", tags=["Listening"])


@router.post(
    "/evaluate",
    summary="Evaluate all 3 spoken answers for a listening session",
)
async def evaluate_listening_answers(
    # Session context
    session_id: str = Form(...),
    

    # Audio answers (one file per question)
    audio_1: UploadFile = File(...),
    audio_2: UploadFile = File(...),
    audio_3: UploadFile = File(...),

    db: Session = Depends(get_db),
):
    """
    Upload 3 audio files (one answer per question).
    Transcribes all 3, then evaluates in a single LLM call.
    """
    temp_dir = Path(settings.TEMP_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_files = []
    try:
        # ── 1. Save + transcribe all 3 audio files ────────────────────────────
        questions = [
            (1, question_1, audio_1),
            (2, question_2, audio_2),
            (3, question_3, audio_3),
        ]

        answers = []
        for q_id, q_text, audio_file in questions:
            suffix = Path(audio_file.filename or "audio.bin").suffix or ".bin"
            temp_path = temp_dir / f"{session_id}_q{q_id}{suffix}"
            temp_files.append(temp_path)

            contents = await audio_file.read()
            temp_path.write_bytes(contents)

            transcript = transcribe_audio(temp_path)
            if not transcript:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Transcription failed for question {q_id}. Check audio quality.",
                )

            logger.info("Q%d transcript: %s", q_id, transcript[:80])
            answers.append({
                "question_id": q_id,
                "question": q_text,
                "answer": transcript,   # whisper transcript as the answer
            })

        # ── 2. Evaluate all answers in one LLM call ───────────────────────────
        results = evaluate_answers_batch(passage=passage, answers=answers)

        total_score = round(
            sum(r.get("score", 0) for r in results) / len(results), 2
        )

        # ── 3. Persist session ────────────────────────────────────────────────
        session = ListeningSession(
            session_id=session_id,
            passage=passage,
            questions=answers,
            similarity_score=total_score,
        )
        db.add(session)
        db.commit()

        return {
            "session_id": session_id,
            "total_score": total_score,
            "results": [
                {
                    "question_id": r.get("question_id"),
                    "question": answers[i]["question"],
                    "transcript": answers[i]["answer"],
                    "correct": r.get("correct", False),
                    "score": r.get("score", 0),
                    "feedback": r.get("feedback", ""),
                }
                for i, r in enumerate(results)
            ],
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("evaluate_listening_answers failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {exc}",
        )
    finally:
        for path in temp_files:
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass