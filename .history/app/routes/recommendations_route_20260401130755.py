# app/routes/pronunciation_recommend_route.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.pronunciation_models import UserPronunciationProfile, PhonemePerformance

router = APIRouter(prefix="/api/v1/pronunciation", tags=["Pronunciation"])

# Expand later
SENTENCE_BANK = {
    "θ": [
        {"sentence": "Think about the thing.", "difficulty": "basic"},
        {"sentence": "Three thousand thoughts.", "difficulty": "intermediate"},
    ],
    "ð": [
        {"sentence": "This is the day that they arrived.", "difficulty": "basic"},
        {"sentence": "Those weathered clothes are theirs.", "difficulty": "intermediate"},
    ]
}


def safe_level_progress(profile: UserPronunciationProfile):
    """
    Guarantee a valid dict structure for level_progress.
    Avoids KeyError and NoneType crashes.
    """
    lp = profile.level_progress or {}

    return {
        "exercises_at_level": int(lp.get("exercises_at_level", 0)),
        "required": int(lp.get("required_for_next", 20)),
        "current": lp.get("current", profile.current_level),
        "avg_score_at_level": float(lp.get("avg_score_at_level", 0))
    }


def compute_next_milestone(profile: UserPronunciationProfile):
    """
    Determines the next milestone safely.
    """
    lp = safe_level_progress(profile)

    remaining = lp["required"] - lp["exercises_at_level"]

    if remaining <= 0:
        return "You are eligible to level up after scoring above 75% consistently."

    return f"Complete {remaining} more exercises to reach the next level."


@router.get("/recommendations/{user_id}")
def get_pronunciation_recommendations(user_id: int, db: Session = Depends(get_db)):
    """
    Generate a personalized recommendation set based on weak phonemes.
    """

    profile = db.query(UserPronunciationProfile).filter_by(user_id=user_id).first()
    if not profile:
        return {
            "focus_areas": [],
            "suggested_practice_time_mins": 10,
            "next_milestone": "No data available. Complete your first exercise."
        }

    # Fetch phoneme performance
    phonemes = db.query(PhonemePerformance).filter_by(user_id=user_id).all()

    weak_phonemes = []
    for p in phonemes:
        if p.accuracy_pct is not None:
            acc = float(p.accuracy_pct)
            if acc < 50:
                weak_phonemes.append(p)

    focus_areas = []
    for w in weak_phonemes:
        examples = SENTENCE_BANK.get(w.phoneme, [])
        focus_areas.append({
            "phoneme": w.phoneme,
            "exercises": examples
        })

    next_milestone = compute_next_milestone(profile)

    return {
        "focus_areas": focus_areas,
        "suggested_practice_time_mins": 15,
        "next_milestone": next_milestone
    }