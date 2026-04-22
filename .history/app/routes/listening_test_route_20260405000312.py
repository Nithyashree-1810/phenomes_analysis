
import json
import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage

from app.db.session import get_db
from app.models.listening_model import ListeningSession
from app.services.llm_client import get_chat_llm

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/listening", tags=["Listening"])


def get_whisper_model(request: Request):
    """Dependency: retrieves the Whisper model loaded at startup."""
    model = getattr(request.app.state, "whisper_model", None)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Whisper model not loaded.",
        )
    return model


def _evaluate_semantic_score(expected: str, transcript: str) -> dict:
    """
    Use GPT-4o-mini to evaluate how well the user's answer matches the
    expected passage.  Returns {relevance, correctness, feedback}.
    """
    prompt = (
        "You are evaluating a student's listening comprehension.\n\n"
        f'EXPECTED ANSWER:\n"""{expected}"""\n\n'
        f'STUDENT TRANSCRIPT:\n"""{transcript}"""\n\n'
        "Evaluate comprehension accuracy ONLY (not pronunciation).\n"
        "Return STRICT JSON with no extra text:\n"
        '{"relevance": <0-100>, "correctness": <0-100>, "feedback": "<short explanation>"}'
    )
    llm = get_chat_llm(temperature=0.0)
    response = llm.invoke(
        [HumanMessage(content=prompt)],
        config={"run_name": "listening_semantic_evaluation"},
    )
    raw = response.content.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("_evaluate_semantic_score: invalid JSON from LLM: %s", raw)
        raise ValueError(f"LLM returned invalid JSON: {exc}") from exc


@router.post(
    "/submit-audio",
    summary="Evaluate user's spoken answer to a listening question",
)
async def evaluate_listening_audio(
    question_text: str = Form(...),
    file: UploadFile = None,
    whisper=Depends(get_whisper_model),
    db: Session = Depends(get_db),
):
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file uploaded.",
        )

    session_id = str(uuid.uuid4())
    temp_path = Path(f"temp_{session_id}{Path(file.filename or 'audio.bin').suffix}")

    try:
        # ── Save upload ──────────────────────────────────────────────────────
        temp_path.write_bytes(await file.read())

        # ── Whisper transcription ────────────────────────────────────────────
        result = whisper.transcribe(str(temp_path))
        user_transcript = result.get("text", "").strip()

        if not user_transcript:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Transcription returned empty result.",
            )

        # ── LLM semantic evaluation ──────────────────────────────────────────
        expected_text = question_text.strip()
        semantic = _evaluate_semantic_score(expected_text, user_transcript)

        # ── Persist attempt ──────────────────────────────────────────────────
        attempt = ListeningSession(
            session_id=session_id,
            passage=expected_text,
            questions=[{"question": expected_text}],
            user_transcript=user_transcript,
            similarity_score=float(semantic.get("correctness", 0)),
            audio_filename=file.filename,
        )
        db.add(attempt)
        db.commit()

        return {
            "session_id": session_id,
            "expected_answer": expected_text,
            "user_transcript": user_transcript,
            "relevance": semantic.get("relevance", 0),
            "correctness": semantic.get("correctness", 0),
            "feedback": semantic.get("feedback", ""),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("[%s] evaluate_listening_audio failed: %s", session_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {exc}",
        ) from exc
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
