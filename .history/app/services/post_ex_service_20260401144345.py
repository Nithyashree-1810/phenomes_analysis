# app/services/post_exercise_hook.py

from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.models.pronunciation_models import (
    UserPronunciationProfile,
    PhonemePerformance
)
from app.services.levelling_service import update_level_progress


def update_phoneme_stats(db: Session, user_id: int, phoneme_results: list):
    """
    phoneme_results = [
        {"phoneme": "θ", "correct": True},
        {"phoneme": "ð", "correct": False}
    ]
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

        # accuracy_pct = correct_attempts / total_attempts * 100
        if record.total_attempts > 0:
            accuracy = (record.correct_attempts / record.total_attempts) * 100
            record.accuracy_pct = Decimal(f"{accuracy:.2f}")

        record.last_attempted_at = datetime.utcnow()

    db.commit()


def update_profile_summary(db: Session, user_id: int):
    """
    Recalculate weak/strong phoneme lists and update user profile.
    """

    profile = db.query(UserPronunciationProfile).filter_by(user_id=user_id).first()
    if not profile:
        return

    stats = (
        db.query(PhonemePerformance)
        .filter_by(user_id=user_id)
        .all()
    )

    weak = []
    strong = []
    total_scores = []
    total_attempts = 0

    for p in stats:
        if p.accuracy_pct is None:
            continue

        acc = float(p.accuracy_pct)
        total_scores.append(acc)
        total_attempts += p.total_attempts

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

    # Overall score = mean accuracy
    profile.overall_score_avg = (
        sum(total_scores) / len(total_scores)
        if total_scores else 0
    )

    # Time is added externally; here just mark practice timestamp
    profile.last_practice_at = datetime.utcnow()

    # Level progress update
    update_level_progress(profile)

    db.commit()


def post_exercise_hook(db: Session, user_id: int, phoneme_results: list, time_spent_secs: int):
    """
    Main function to call after an exercise is finished.
    Updates:
    - phoneme stats
    - user profile summary
    - time spent
    """

    profile = db.query(UserPronunciationProfile).filter_by(user_id=user_id).first()
    if not profile:
        return

    # 1. Update phoneme analytics
    update_phoneme_stats(db, user_id, phoneme_results)

    # 2. Update aggregates
    update_profile_summary(db, user_id)

    # 3. Update time & exercise counter
    profile.exercises_completed += 1
    profile.time_spent_total_secs += time_spent_secs

    db.commit()

    return {"status": "success", "message": "Exercise processed successfully"}