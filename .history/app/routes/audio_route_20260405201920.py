import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
import time

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repo.pronunciation_repo import get_or_create_profile
from app.services.audio_service import convert_to_wav
from app.services.post_ex_service import post_exercise_hook
from app.services.scoring_service import compute_pronunciation_scores
from app.services.transcription_service import transcribe_audio
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["Pronunciation"])


@router.post("/analyze", summary="Analyse pronunciation audio")
async def analyze_audio(
    file: UploadFile,
    user_id: uuid.UUID = Query(..., description="Caller-supplied UUID user ID"),
    db: Session = Depends(get_db),
    # reference_text is now optional — uses stored question if not passed
    reference_text: str | None = Query(None, description="The sentence the user should have spoken (optional if /next was called)"),
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
    start_time = time.time()
    temp_dir = Path(settings.TEMP_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)

    original_suffix = Path(file.filename or "audio.bin").suffix or ".bin"
    temp_path = temp_dir / f"{request_id}{original_suffix}"
    wav_path: Path | None = None

    try:
        # ── 1. Ensure profile exists ──────────────────────────────────────────
        profile = get_or_create_profile(db, user_id)

        # ── 2. Resolve reference text ─────────────────────────────────────────
        ref_text = reference_text or profile.current_question
        if not ref_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No reference text provided and no question stored. Call GET /question/next first.",
            )

        # ── 3. Save upload ────────────────────────────────────────────────────
        contents = await file.read()
        temp_path.write_bytes(contents)
        logger.debug("[%s] Saved upload to %s (%d bytes)", request_id, temp_path, len(contents))

        # ── 4. Convert to WAV ─────────────────────────────────────────────────
        audio_format = temp_path.suffix.lstrip(".").lower()
        wav_path = convert_to_wav(temp_path, audio_format)

        # ── 5. Transcribe ─────────────────────────────────────────────────────
        transcript = transcribe_audio(wav_path)
        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Audio transcription returned empty result. Check audio quality.",
            )

        # ── 6. Score ──────────────────────────────────────────────────────────
        result = compute_pronunciation_scores(ref_text, transcript)

        phoneme_score: float = result["phoneme_score"]
        fluency_score: float = result["fluency_score"]
        overall_score: float = result["overall_score"]
        phoneme_details: list = result["phoneme_details"]
        weak_phonemes: list = result["weak_phonemes"]
        strong_phonemes: list = result["strong_phonemes"]
        mistakes: list = result["mistakes"]
        tips: list = result["tips"]

        # ── 7. Build phoneme results for DB ───────────────────────────────────
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

        # ── 8. Run post-exercise pipeline ─────────────────────────────────────
        elapsed_secs = int(time.time() - start_time)
        post_exercise_hook(
            db=db,
            user_id=user_id,
            phoneme_results=phoneme_results,
            time_spent_secs=elapsed_secs,
            current_score=overall_score,
        )

        # ── 9. Clear stored question after use ────────────────────────────────
        profile.current_question = None
        db.commit()

        logger.info(
            "[%s] Analysis complete for user_id=%s: phoneme_score=%.1f overall=%.1f",
            request_id, user_id, phoneme_score, overall_score,
        )

        return {
            "request_id": request_id,
            "user_id": user_id,
            "reference_text": ref_text,
            "transcript": transcript,
            "ref_ipa": result["ref_ipa"],
            "user_ipa": result["user_ipa"],
            "phoneme_score": phoneme_score,
            "fluency_score": fluency_score,
<<<<<<< HEAD
            "overall_score": overall_score,
=======
>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f
            "weak_phonemes": weak_phonemes,
            "strong_phonemes": strong_phonemes,
            "mistakes": mistakes,
            "tips": tips,
        }

<<<<<<< HEAD
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
        for path in (temp_path, wav_path):
            if path and path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass
=======
    except Exception as e:
        db.rollback()
        return {"error": str(e)}




"""from fastapi import APIRouter, UploadFile, Request, Depends, Query
from sqlalchemy.orm import Session
from pathlib import Path
import os
from datetime import datetime

from app.services.audio_service import convert_to_wav
from app.services.transcription_service import transcribe_audio
from app.services.scoring_service import compute_pronunciation_scores
from app.services.pronun_questions_service import PronunciationQuestionsService
from app.services.post_ex_service import update_phoneme_stats
from app.db.session import get_db
from app.models.pronunciation_models import UserPronunciationProfile


router = APIRouter(prefix="/test", tags=["pronunciation"])
service = PronunciationQuestionsService()

@router.post("/analyze")
async def analyze_audio(
    request: Request,
    file: UploadFile,
    reference_text: str = Query(...),
    user_id: int = Query(...),
    db: Session = Depends(get_db)
):
    try:
        # ---------------------------------------------------------
        # Save temporary file
        # ---------------------------------------------------------
        os.makedirs("temp", exist_ok=True)
        temp_path = Path("temp") / file.filename
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # ---------------------------------------------------------
        # Convert to WAV
        # ---------------------------------------------------------
        audio_format = temp_path.suffix.lower().replace(".", "")
        wav_path = convert_to_wav(temp_path, audio_format)

        # ---------------------------------------------------------
        # Transcribe
        # ---------------------------------------------------------
        transcript = transcribe_audio(wav_path)

        # ---------------------------------------------------------
        # Scoring (IPA + accuracy + mistakes + tips)
        # ---------------------------------------------------------
        result = compute_pronunciation_scores(reference_text, transcript)

        phoneme_score = result.get("phoneme_score", 0)
        fluency_score = result.get("fluency_score", 0)

        phoneme_details = result.get("phoneme_details", [])
        weak_phonemes = result.get("weak_phonemes", [])
        strong_phonemes = result.get("strong_phonemes", [])
        mistakes = result.get("mistakes", [])
        tips = result.get("tips", [])

        # ---------------------------------------------------------
        # Convert phoneme details → format required by update_phoneme_stats()
        # ---------------------------------------------------------
        phoneme_results = []

        for detail in phoneme_details:
            phoneme = detail.get("phoneme")
            if not phoneme:
                continue

            total_attempts = detail.get("total_attempts", 1)
            correct_attempts = detail.get("correct_attempts", 0)
            accuracy = detail.get("accuracy", 0) 
            # update_phoneme_stats expects {"phoneme": X, "correct": bool}
           

            phoneme_results.append({
                "phoneme": phoneme,
                "correct": correct_attempts > 0,
                "accuracy": accuracy,
                "total_attempts": total_attempts,
                "correct_attempts": correct_attempts
            })

        # ---------------------------------------------------------
        # SAFE UPSERT (no duplicates, no unique constraint errors)
        # ---------------------------------------------------------
        update_phoneme_stats(db, user_id, phoneme_results)

        # ---------------------------------------------------------
        # Update / Create pronunciation profile
        # ---------------------------------------------------------
        profile = (
            db.query(UserPronunciationProfile)
            .filter(UserPronunciationProfile.user_id == user_id)
            .first()
        )

        weak_list = [w.get("phoneme") for w in weak_phonemes]
        strong_list = [s.get("phoneme") for s in strong_phonemes]

        if not profile:
            profile = UserPronunciationProfile(
                user_id=user_id,
                current_level=None,
                overall_score_avg=phoneme_score,
                exercises_completed=1,
                time_spent_total_secs=0,
                weak_phonemes=weak_list,
                strong_phonemes=strong_list,
                level_progress={},
                last_practice_at=datetime.utcnow(),
            )
            db.add(profile)
        else:
            profile.overall_score_avg = phoneme_score
            profile.exercises_completed = (profile.exercises_completed or 0) + 1
            profile.weak_phonemes = weak_list
            profile.strong_phonemes = strong_list
            profile.last_practice_at = datetime.utcnow()

        db.commit()

        return {
            "user_id": user_id,
            "reference_text": reference_text,
            "transcript": transcript,
            "phoneme_score": phoneme_score,
            "fluency_score": fluency_score,
            "weak_phonemes": weak_phonemes,
            "strong_phonemes": strong_phonemes,
            "mistakes": mistakes,
            "tips": tips,
        }

    except Exception as e:
        db.rollback()
        return {"error": str(e)}"""
>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f
