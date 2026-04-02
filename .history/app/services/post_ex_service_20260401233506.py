# app/services/post_exercise_hook.py

from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
from sqlalchemy.dialects.postgresql import insert

from app.models.pronunciation_models import (
    UserPronunciationProfile,
    PhonemePerformance
)
from app.services.leveling_service import update_level_progress
from app.repo

# ---------------------------------------------
# UPSERT for phoneme stats (PREVENTS duplicate key issue)
# ---------------------------------------------
def upsert_phoneme(db: Session, user_id: int, phoneme: str, correct: bool):
    total_attempts = 1
    correct_attempts = 1 if correct else 0

    stmt = insert(PhonemePerformance).values(
        user_id=user_id,
        phoneme=phoneme,
        total_attempts=total_attempts,
        correct_attempts=correct_attempts,
        accuracy_pct=(correct_attempts / total_attempts) * 100,
        last_attempted_at=datetime.utcnow(),
    )

    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "phoneme"],
        set_={
            "total_attempts": PhonemePerformance.total_attempts + 1,
            "correct_attempts": PhonemePerformance.correct_attempts
            + (1 if correct else 0),
            "accuracy_pct": (
                (
                    PhonemePerformance.correct_attempts
                    + (1 if correct else 0)
                )
                / (PhonemePerformance.total_attempts + 1)
                * 100
            ),
            "last_attempted_at": datetime.utcnow(),
        },
    )

    db.execute(stmt)


# ---------------------------------------------
# Update phoneme stats using UPSERT
# ---------------------------------------------
def update_phoneme_stats(db: Session, user_id: int, phoneme_results: list):
    """
    UPSERT-based phoneme update (safe & idempotent).
    Removes duplicates BEFORE insert to avoid UniqueViolation.
    """
    seen = set()

    for result in phoneme_results:
        phoneme = result["phoneme"]
        correct = result["correct"]

        if phoneme in seen:
            continue
        seen.add(phoneme)

        upsert_phoneme(db, user_id, phoneme, correct)

    db.commit()


# ---------------------------------------------
# Recompute weak/strong + score
# ---------------------------------------------
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


# ---------------------------------------------
# Main Hook
# ---------------------------------------------
def post_exercise_hook(db: Session, user_id: int, phoneme_results: list, time_spent_secs: int):
    profile = db.query(UserPronunciationProfile).filter_by(user_id=user_id).first()
    if not profile:
        return {"status": "error", "message": "Profile not found"}

    # UPSERT phoneme stats safely
    update_phoneme_stats(db, user_id, phoneme_results)

    # Update counters
    profile.exercises_completed += 1
    profile.time_spent_total_secs += time_spent_secs

    # Recompute stats
    recompute_weak_strong_and_score(db, profile)

    # Update levels
    update_level_progress(profile)

    db.commit()

    return {"status": "success"}