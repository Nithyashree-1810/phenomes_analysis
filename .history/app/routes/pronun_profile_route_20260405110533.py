"""
app/routes/pronun_profile_route.py

GET /api/v1/pronunciation/profile/{user_id}
Returns a user's full pronunciation profile with live phoneme stats.
"""
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.pronunciation_models import UserPronunciationProfile, PhonemePerformance
from app.schema.pronun_schema import UserPronunciationProfileOut
from app.core.phoneme_example_words import PHONEME_EXAMPLE_WORDS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/pronunciation", tags=["Pronunciation"])




@router.get(
    "/profile/{user_id}",
    response_model=UserPronunciationProfileOut,
    summary="Get user pronunciation profile",
)
def get_user_profile(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Fetch a user's pronunciation profile.
    Weak/strong phoneme lists are computed live from PhonemePerformance rows.
    """
    profile = (
        db.query(UserPronunciationProfile)
        .filter(UserPronunciationProfile.user_id == user_id)
        .first()
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pronunciation profile not found for user_id={user_id}",
        )

    # ── Compute weak/strong from live phoneme stats ───────────────────────
    phoneme_stats = (
        db.query(PhonemePerformance)
        .filter(PhonemePerformance.user_id == user_id)
        .all()
    )

    weak_phonemes, strong_phonemes = [], []
    for stat in phoneme_stats:
        if stat.accuracy_pct is None:
            continue
        accuracy = float(stat.accuracy_pct)
        if accuracy < 50:
            weak_phonemes.append({
                "phoneme": stat.phoneme,
                "error_rate": round((100 - accuracy) / 100, 3),
                "example_word": EXAMPLE_WORDS.get(stat.phoneme),
            })
        elif accuracy >= 70:
            strong_phonemes.append({
                "phoneme": stat.phoneme,
                "accuracy": round(accuracy / 100, 3),
            })

    # ── Level progress ────────────────────────────────────────────────────
    lp = profile.level_progress or {}
    level_progress = {
        "current": lp.get("current", profile.current_level or "basic"),
        "exercises_at_level": lp.get("exercises_at_level", profile.exercises_completed or 0),
        "required_for_next": lp.get("required_for_next", 20),
        "avg_score_at_level": lp.get("avg_score_at_level", float(profile.overall_score_avg or 0)),
    }

    return {
        "user_id": profile.user_id,
        "current_level": profile.current_level or "basic",
        "overall_score_avg": float(profile.overall_score_avg or 0),
        "exercises_completed": profile.exercises_completed or 0,
        "time_spent_total_mins": round((profile.time_spent_total_secs or 0) / 60, 2),
        "weak_phonemes": weak_phonemes,
        "strong_phonemes": strong_phonemes,
        "level_progress": level_progress,
        "last_practice": profile.last_practice_at,
    }
