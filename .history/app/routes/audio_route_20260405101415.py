

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repo.pronunciation_repo import get_or_create_profile
from app.services.audio_service import convert_to_wav
from app.services.post_ex_service import post_exercise_hook, update_phoneme_stats
from app.services.pronun_questions_service import PronunciationQuestionsService
from app.services.scoring_service import compute_pronunciation_scores
from app.services.transcription_service import transcribe_audio
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["Pronunciation"])
_question_svc = PronunciationQuestionsService()


@router.post("/analyze", summary="Analyse pronunciation audio")
async def analyze_audio(
    file: UploadFile,
    reference_text: str = Query(..., description="The sentence the user should have spoken"),
    user_id: uuid. = Query(..., description="Caller-supplied integer user ID"),
    db: Session = Depends(get_db),
):
    """
    Pipeline:
      1. Save uploaded audio to disk.
      2. Convert to WAV.
      3. Transcribe via OpenAI Whisper.
      4. Score pronunciation (IPA comparison, fluency, mistakes, tips).
      5. Persist phoneme stats and profile.
      6. Return full analysis result with a UUID request_id.
    """
    request_id = str(uuid.uuid4())
    temp_dir = Path(settings.TEMP_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Use a unique temp filename to avoid race conditions
    original_suffix = Path(file.filename or "audio.bin").suffix or ".bin"
    temp_path = temp_dir / f"{request_id}{original_suffix}"
    wav_path: Path | None = None

    try:
        # ── 1. Save upload ───────────────────────────────────────────────────
        contents = await file.read()
        temp_path.write_bytes(contents)
        logger.debug("[%s] Saved upload to %s (%d bytes)", request_id, temp_path, len(contents))

        # ── 2. Convert to WAV ────────────────────────────────────────────────
        audio_format = temp_path.suffix.lstrip(".").lower()
        wav_path = convert_to_wav(temp_path, audio_format)

        # ── 3. Transcribe ────────────────────────────────────────────────────
        transcript = transcribe_audio(wav_path)
        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Audio transcription returned empty result. Check audio quality.",
            )

        # ── 4. Score ─────────────────────────────────────────────────────────
        result = compute_pronunciation_scores(reference_text, transcript)

        phoneme_score: float = result["phoneme_score"]
        fluency_score: float = result["fluency_score"]
        overall_score: float = result["overall_score"]
        phoneme_details: list = result["phoneme_details"]
        weak_phonemes: list = result["weak_phonemes"]
        strong_phonemes: list = result["strong_phonemes"]
        mistakes: list = result["mistakes"]
        tips: list = result["tips"]

        # ── 5. Build phoneme results for DB ──────────────────────────────────
        phoneme_results = [
            {
                "phoneme": d["phoneme"],
                "correct": d["correct_attempts"] > 0,
                "accuracy": d["accuracy"],
                "total_attempts": d["total_attempts"],
                "correct_attempts": d["correct_attempts"],
            }
            for d in phoneme_details
            if d.get("phoneme")
        ]

        # ── 6. Ensure profile exists (flush so FK is satisfied) ───────────────
        profile = get_or_create_profile(db, user_id)

        # ── 7. Update phoneme stats (within same transaction) ─────────────────
        update_phoneme_stats(db, user_id, phoneme_results)

        # ── 8. Update profile fields ──────────────────────────────────────────
        n = (profile.exercises_completed or 0) + 1
        old_avg = float(profile.overall_score_avg or 0)
        profile.overall_score_avg = round((old_avg * (n - 1) + phoneme_score) / n, 2)
        profile.exercises_completed = n
        profile.weak_phonemes = [w.get("phoneme") for w in weak_phonemes]
        profile.strong_phonemes = [s.get("phoneme") for s in strong_phonemes]
        profile.last_practice_at = datetime.now(timezone.utc)

        db.commit()
        logger.info(
            "[%s] Analysis complete for user_id=%s: phoneme_score=%.1f overall=%.1f",
            request_id, user_id, phoneme_score, overall_score,
        )

        return {
            "request_id": request_id,
            "user_id": user_id,
            "reference_text": reference_text,
            "transcript": transcript,
            "ref_ipa": result["ref_ipa"],
            "user_ipa": result["user_ipa"],
            "phoneme_score": phoneme_score,
            "fluency_score": fluency_score,
            "overall_score": overall_score,
            "weak_phonemes": weak_phonemes,
            "strong_phonemes": strong_phonemes,
            "mistakes": mistakes,
            "tips": tips,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("[%s] analyze_audio failed: %s", request_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {exc}",
        ) from exc
    finally:
        # Always clean up temp files
        for path in (temp_path, wav_path):
            if path and path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass
