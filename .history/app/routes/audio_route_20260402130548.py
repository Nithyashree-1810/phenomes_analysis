from fastapi import APIRouter, UploadFile, Request, Depends, Query
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
            correct_flag = correct_attempts > 0

            phoneme_results.append({
                "phoneme": phoneme,
                "correct": corr
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
        return {"error": str(e)}