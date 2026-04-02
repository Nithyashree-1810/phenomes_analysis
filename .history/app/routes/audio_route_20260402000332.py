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
	
Response body
Download
{
  "error": "(psycopg2.errors.ForeignKeyViolation) insert or update on table \"phoneme_performance\" violates foreign key constraint \"phoneme_performance_user_id_fkey\"\nDETAIL:  Key (user_id)=(8) is not present in table \"user_pronunciation_profile\".\n\n[SQL: INSERT INTO phoneme_performance (user_id, phoneme, total_attempts, correct_attempts, accuracy_pct, last_attempted_at) VALUES (%(user_id)s, %(phoneme)s, %(total_attempts)s, %(correct_attempts)s, %(accuracy_pct)s, %(last_attempted_at)s) ON CONFLICT (user_id, phoneme) DO UPDATE SET total_attempts = (phoneme_performance.total_attempts + %(total_attempts_1)s), correct_attempts = (phoneme_performance.correct_attempts + %(correct_attempts_1)s), accuracy_pct = (((phoneme_performance.correct_attempts + %(correct_attempts_2)s) / CAST((phoneme_performance.total_attempts + %(total_attempts_2)s) AS NUMERIC)) * %(param_1)s), last_attempted_at = %(param_2)s RETURNING phoneme_performance.id]\n[parameters: {'user_id': 8, 'phoneme': 'l', 'total_attempts': 1, 'correct_attempts': 1, 'accuracy_pct': 100.0, 'last_attempted_at': datetime.datetime(2026, 4, 1, 18, 28, 12, 180682), 'total_attempts_1': 1, 'correct_attempts_1': 1, 'correct_attempts_2': 1, 'total_attempts_2': 1, 'param_1': 100, 'param_2': datetime.datetime(2026, 4, 1, 18, 28, 12, 180682)}]\n(Background on this error at: https://sqlalche.me/e/20/gkpj)"
}
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

            # update_phoneme_stats expects {"phoneme": X, "correct": bool}
            correct_flag = correct_attempts > 0

            phoneme_results.append({
                "phoneme": phoneme,
                "correct": correct_flag
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