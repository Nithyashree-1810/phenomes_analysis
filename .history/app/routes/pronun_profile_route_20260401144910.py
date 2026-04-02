# app/routes/pronunciation_profile_route.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.pronunciation_models import (
    UserPronunciationProfile,
    PhonemePerformance
)
from app.schemas.pronun_schema import UserPronunciationProfileOut

router = APIRouter(prefix="/api/v1/pronunciation", tags=["Pronunciation"])


@router.get("/profile/{user_id}", response_model=UserPronunciationProfileOut)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """
    Returns the complete pronunciation profile for a user.
    """

    profile = (
        db.query(UserPronunciationProfile)
        .filter(UserPronunciationProfile.user_id == user_id)
        .first()
    )

    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Load phoneme performance table
    phoneme_stats = (
        db.query(PhonemePerformance)
        .filter(PhonemePerformance.user_id == user_id)
        .all()
    )

    # Build weak_phonemes and strong_phonemes with examples if needed
    weak_phonemes = []
    strong_phonemes = []

    for stat in phoneme_stats:
        if stat.accuracy_pct is None:
            continue

        accuracy = float(stat.accuracy_pct)
        error_rate = float(f"{100 - accuracy:.2f}")

        # Weak < 50% accuracy
        if accuracy < 50:
            weak_phonemes.append({
                "phoneme": stat.phoneme,
                "error_rate": error_rate / 100,      # convert 65 -> 0.65
                "example_word": _example_word(stat.phoneme)
            })

        # Strong >= 70%
        if accuracy >= 70:
            strong_phonemes.append({
                "phoneme": stat.phoneme,
                "accuracy": accuracy / 100          # convert 95 -> 0.95
            })

    # Convert sec → mins
    time_minutes = round(profile.time_spent_total_secs / 60, 2)

    # Ensure level_progress structure is safe
    level = profile.level_history or {}
    level_progress = {
        "current": level.get("current", profile.current_level),
        "exercises_at_level": level.get("exercises_at_level", 0),
        "required_for_next": level.get("required_for_next", 20),
        "avg_score_at_level": level.get("avg_score_at_level", 0),
    }

    return {
        "user_id": profile.user_id,
        "current_level": profile.current_level,
        "overall_score_avg": float(profile.overall_score_avg or 0),
        "exercises_completed": profile.exercises_completed,
        "time_spent_total_mins": time_minutes,
        "weak_phonemes": weak_phonemes,
        "strong_phonemes": strong_phonemes,
        "level_progress": level_progress,
        "last_practice": profile.last_practice_at,
    }


# Example-word generator (simple, extendable)
EXAMPLE_WORDS = {
    "θ": "think",
    "ð": "the",
    "ʃ": "shoe",
    "tʃ": "chair",
    "ŋ": "sing",
}

def _example_word(phoneme: str):
    return EXAMPLE_WORDS.get(phoneme)