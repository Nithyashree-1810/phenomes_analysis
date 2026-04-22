# app/routes/pronunciation_profile_route.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.pronunciation_models import (
    UserPronunciationProfile,
    PhonemePerformance
)
from app.schema.pronun_schema import UserPronunciationProfileOut

router = APIRouter(prefix="/api/v1/pronunciation", tags=["Pronunciation"])


@router.get("/profile/{user_id}", response_model=UserPronunciationProfileOut)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """
    Fetch the pronunciation profile AND compute strong/weak phonemes dynamically
    from phoneme_performance table.
    """

    # -----------------------------
    # Load base profile
    # -----------------------------
    profile = (
        db.query(UserPronunciationProfile)
        .filter(UserPronunciationProfile.user_id == user_id)
        .first()
    )

    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    # -----------------------------
    # Load phoneme performance stats
    # -----------------------------
    phoneme_stats = (
        db.query(PhonemePerformance)
        .filter(PhonemePerformance.user_id == user_id)
        .all()
    )

    weak_phonemes = []
    strong_phonemes = []

    for stat in phoneme_stats:
        if stat.accuracy_pct is None:
            continue

        accuracy = float(stat.accuracy_pct)

        # Weak phonemes → accuracy < 50%
        if accuracy < 50:
            weak_phonemes.append({
                "phoneme": stat.phoneme,
                "error_rate": round((100 - accuracy) / 100, 3),
                "example_word": _example_word(stat.phoneme)
            })

        # Strong phonemes → accuracy >= 70%
        if accuracy >= 70:
            strong_phonemes.append({
                "phoneme": stat.phoneme,
                "accuracy": round(accuracy / 100, 3)
            })

    # -----------------------------
    # Convert seconds → minutes
    # -----------------------------
    time_minutes = round((profile.time_spent_total_secs or 0) / 60, 2)

    # -----------------------------
    # Validate and patch level_progress
    # -----------------------------
    level = profile.level_progress or {}

    level_progress = {
        "current": level.get("current", profile.current_level or "basic"),
        "exercises_at_level": level.get("exercises_at_level", profile.exercises_completed or 0),
        "required_for_next": level.get("required_for_next", 20),
        "avg_score_at_level": level.get("avg_score_at_level", float(profile.overall_score_avg or 0))
    }

    # -----------------------------
    # Final return
    # -----------------------------
    return {
        "user_id": profile.user_id,
        "current_level": profile.current_level or "basic",
        "overall_score_avg": float(profile.overall_score_avg or 0),
        "exercises_completed": profile.exercises_completed or 0,
        "time_spent_total_mins": time_minutes,
        "weak_phonemes": weak_phonemes,
        "strong_phonemes": strong_phonemes,
        "level_progress": level_progress,
        "last_practice": profile.last_practice_at,
    }


# -----------------------------
# Example-word lookup table
# -----------------------------
EXAMPLE_WORDS = {
    "θ": "think",
    "ð": "this",
    "ʃ": "shoe",
    "tʃ": "chair",
    "ŋ": "sing",
    "r": "red",
    "l": "light",
}

def _example_word(phoneme: str):
    return EXAMPLE_WORDS.get(phoneme, None)