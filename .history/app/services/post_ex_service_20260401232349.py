# app/services/post_exercise_hook.py

from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.models.pronunciation_models import (
    UserPronunciationProfile,
    PhonemePerformance
)
from app.services.leveling_service import update_level_progress


def update_phoneme_stats(db: Session, user_id: int, phoneme_results: list):
    """
    Update individual phoneme performance records.
    """
    for result in phoneme_results:
        phoneme = result["phoneme"]
        correct = result["correct"]

        record = (
            db.query(PhonemePerformance)
            .filter_by(user_id=user_id, phoneme=phoneme)
            .first()
        )

        if not record:
            record = PhonemePerformance(
                user_id=user_id,
                phoneme=phoneme,
                total_attempts=0,
                correct_attempts=0
            )
            db.add(record)

        record.total_attempts += 1
        if correct:
            record.correct_attempts += 1

        if record.total_attempts > 0:
            accuracy = (record.correct_attempts / record.total_attempts) * 100
            record.accuracy_pct = Decimal(f"{accuracy:.2f}")

        record.last_attempted_at = datetime.utcnow()

    db.commit()


def recompute_weak_strong_and_score(db: Session, profile: UserPronunciationProfile):
    """
    Recompute weak/strong phonemes and overall score from PhonemePerformance.
    """
    phonemes = db.query(PhonemePerformance).filter_by(user_id=profile.user_id).all()
    weak, strong, scores = [], [], []

    for p in phonemes:
        acc = float(p.accuracy_pct or 0)
        
        scores.append(acc)

        if acc < 50:
            weak.append({"phoneme": p.phoneme, "error_rate": float(f"{100 - acc:.2f}")})
        elif acc >= 70:
            strong.append({"phoneme": p.phoneme, "accuracy": float(f"{acc:.2f}")})

    profile.weak_phonemes = weak
    profile.strong_phonemes = strong
    profile.overall_score_avg = (sum(scores) / len(scores)) if scores else 0
    profile.last_practice_at = datetime.utcnow()


def post_exercise_hook(db: Session, user_id: int, phoneme_results: list, time_spent_secs: int):
    """
    Main hook to call after a user completes an exercise.
    Updates phoneme stats, recomputes weak/strong lists, updates level progress.
    """
    profile = db.query(UserPronunciationProfile).filter_by(user_id=user_id).first()
    if not profile:
        return {"status": "error", "message": "Profile not found"}

    # Update phoneme attempts and accuracy
    update_phoneme_stats(db, user_id, phoneme_results)

    # Increment exercises/time
    profile.exercises_completed += 1
    profile.time_spent_total_secs += time_spent_secs

    # Recompute weak/strong phonemes and overall score
    recompute_weak_strong_and_score(db, profile)

    # Update level progress based on updated score
    update_level_progress(profile)

    db.commit()

    return {"status": "success"}    