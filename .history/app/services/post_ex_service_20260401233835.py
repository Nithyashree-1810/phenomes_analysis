# app/services/post_exercise_hook.py

from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.models.pronunciation_models import (
    UserPronunciationProfile,
    PhonemePerformance
)
from app.services.leveling_service import update_level_progress
from app.repo.phoneme_performance_repo import upsert_phoneme


# ---------------------------------------------------
# Update phoneme stats using REAL UPSERT (no skipping)
# ---------------------------------------------------
def update_phoneme_stats(db: Session, user_id: int, phoneme_results: list):
    """
    Updates phoneme stats using UPSERT.
    Every appearance of a phoneme is counted correctly.
    """
    for result in phoneme_results:
        phoneme = result["phoneme"]
        correct = result["correct"]

        # always update — UPSERT handles duplicates safely
        upsert_phoneme(db, user_id, phoneme, correct)

    db.commit()


# ---------------------------------------------------
# Recompute weak/strong lists + score
# ---------------------------------------------------
def recompute_weak_strong_and_score(db: Session, profile: UserPronunciationProfile):
    phonemes = db.query(PhonemePerformance).filter_by(user_id=profile.user_id).all()

    weak, strong, scores = [], [], []

    for p in phonemes:
        acc = float(p.accuracy_pct or 0)
        scores.append(acc)

        if acc < 50:
            weak.append({
                "phoneme": p.phoneme,
                "error_rate": float(f"{100 - acc:.2f}")
            })
        elif acc >= 70:
            strong.append({
                "phoneme": p.phoneme,
                "accuracy": float(f"{acc:.2f}")
            })

    profile.weak_phonemes = weak
    profile.strong_phonemes = strong
    profile.overall_score_avg = (sum(scores) / len(scores)) if scores else 0
    profile.last_practice_at = datetime.utcnow()


# ---------------------------------------------------
# Main Hook
# ---------------------------------------------------
def post_exercise_hook(db: Session, user_id: int, phoneme_results: list, time_spent_secs: int):
    profile = db.query(UserPronunciationProfile).filter_by(user_id=user_id).first()
    if not profile:
        return {"status": "error", "message": "Profile not found"}

    # Update phoneme stats with UPSERT
    update_phoneme_stats(db, user_id, phoneme_results)

    # Update counters
    profile.exercises_completed += 1
    profile.time_spent_total_secs += time_spent_secs

    # Recompute stats
    recompute_weak_strong_and_score(db, profile)

    # Update level
    update_level_progress(profile)

    db.commit()

    return {"status": "success"}