from fastapi import APIRouter, UploadFile, Request, Depends, Query
from sqlalchemy.orm import Session
from pathlib import Path
import os
from datetime import datetime

from app.services.audio_service import convert_to_wav
from app.services.transcription_service import transcribe_audio
from app.services.scoring_service import compute_pronunciation_scores
from app.services.pronun_questions_service import PronunciationQuestionsService
from app.db.session import get_db
from app.models.pronunciation_models import UserPronunciationProfile,

router = APIRouter(prefix="/test", tags=["pronunciation"])
service = PronunciationQuestionsService()


@router.post("/analyze")
async def analyze_audio(
    request: Request,
    file: UploadFile,
    reference_text: str = Query(...),
    user_id: int = Query(...),   # ← FIXED: user_id now integer
    db: Session = Depends(get_db)
):
    """
    Analyze audio and update:
    - user_pronunciation_profile
    - phoneme_performance
    """

    try:
        # ---------------------------------------------------------
        # Save uploaded file
        # ---------------------------------------------------------
        os.makedirs("temp", exist_ok=True)
        temp_path = Path("temp") / file.filename
        file_bytes = await file.read()

        with open(temp_path, "wb") as f:
            f.write(file_bytes)

        # ---------------------------------------------------------
        # Convert to WAV
        # ---------------------------------------------------------
        audio_format = temp_path.suffix.lower().replace(".", "")
        wav_path = convert_to_wav(temp_path, audio_format)

        # ---------------------------------------------------------
        # Transcription
        # ---------------------------------------------------------
        transcript = transcribe_audio(wav_path)

        # ---------------------------------------------------------
        # Scoring
        # ---------------------------------------------------------
        result = compute_pronunciation_scores(reference_text, transcript)

        phoneme_score = result.get("phoneme_score", 0)
        fluency_score = result.get("fluency_score", 0)

        mistakes = result.get("mistakes", [])
        strong = result.get("strong_phonemes", [])
        phoneme_details = result.get("phoneme_details", [])
        tips = result.get("tips", [])

        # ---------------------------------------------------------
        # Update PhonemePerformance per phoneme
        # ---------------------------------------------------------
        for detail in phoneme_details:
            phoneme = detail.get("phoneme")
            if not phoneme:
                continue

            total_attempts = detail.get("total_attempts", 1)
            correct_attempts = detail.get("correct_attempts", 0)

            existing = (
                db.query(PhonemePerformance)
                .filter(PhonemePerformance.user_id == user_id)
                .filter(PhonemePerformance.phoneme == phoneme)
                .first()
            )

            if existing:
                existing.total_attempts += total_attempts
                existing.correct_attempts += correct_attempts
                existing.accuracy_pct = (
                    existing.correct_attempts / existing.total_attempts * 100
                )
                existing.last_attempted_at = datetime.utcnow()

            else:
                new_stat = PhonemePerformance(
                    user_id=user_id,
                    phoneme=phoneme,
                    total_attempts=total_attempts,
                    correct_attempts=correct_attempts,
                    accuracy_pct=(
                        (correct_attempts / total_attempts * 100)
                        if total_attempts > 0 else 0
                    ),
                    last_attempted_at=datetime.utcnow(),
                )
                db.add(new_stat)

        # ---------------------------------------------------------
        # Update or create UserPronunciationProfile
        # ---------------------------------------------------------
        profile = (
            db.query(UserPronunciationProfile)
            .filter(UserPronunciationProfile.user_id == user_id)
            .first()
        )

        weak_list = [m.get("phoneme", "unknown") for m in mistakes]
        strong_list = [s.get("phoneme", "unknown") for s in strong]

        if not profile:
            profile = UserPronunciationProfile(
                user_id=user_id,
                current_level=None,
                overall_score_avg=phoneme_score,
                exercises_completed=1,
                time_spent_total_secs=0,
                weak_phonemes=weak_list,
                strong_phonemes=strong_list,
                level_history=[],
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

        # ---------------------------------------------------------
        # Generate next question
        # ---------------------------------------------------------
        next_q = service.generate_questions(phoneme_score, num_questions=1)

        # ---------------------------------------------------------
        # Response Payload
        # ---------------------------------------------------------
        return {
            "user_id": user_id,
            "reference_text": reference_text,
            "transcript": transcript,
            "phoneme_score": phoneme_score,
            "fluency_score": fluency_score,
            "mistakes": mistakes,
            "tips": tips,
            "next_question": next_q,
        }

    except Exception as e:
        db.rollback()
        return {"error": str(e)}