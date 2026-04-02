from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.models.pronunciation_models import UserPronunciationProfile, PhonemePerformance
from app.services.leveling_service import update_level_progress


def update_phoneme_stats(db: Session, user_id: int, phoneme_results: list):
    """Update or insert phoneme performance records"""
    for result in phoneme_results:
        phoneme = result["phoneme"]
        correct = result["correct"]

        record = db.query(PhonemePerformance).filter_by(user_id=user_id, phoneme=phoneme).first()
        if not record:
            record = PhonemePerformance(
                user_id=user_id, phoneme=phoneme, total_attempts=0, correct_attempts=0
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


def update_profile_summary(db: Session, user_id: int):
    """Recalculate weak/strong phonemes and overall score"""
    profile = db.query(UserPronunciationProfile).filter_by(user_id=user_id).first()
    if not profile:
        return

    stats = db.query(PhonemePerformance).filter_by(user_id=user_id).all()
    weak = []
    strong = []
    scores = []

    for p in stats:
        if p.accuracy_pct is None:
            continue

        acc = float(p.accuracy_pct)
        scores.append(acc)

        if acc < 50:
            weak.append({
                "phoneme": p.phoneme,
                "error_rate": round((100 - acc) / 100, 2),  # scale 0-1
            })
        elif acc >= 70:
            strong.append({
                "phoneme": p.phoneme,
                "accuracy": round(acc / 100, 2),  # scale 0-1
            })

    profile.weak_phonemes = weak
    profile.strong_phonemes = strong

    profile.overall_score_avg = sum(scores) / len(scores) if scores else 0
    profile.last_practice_at = datetime.utcnow()
    db.commit()


def post_exercise_hook(db: Session, user_id: int, phoneme_results: list, time_spent_secs: int):
    """
    Main post-exercise update:
    - Update exercises & time BEFORE calculating level_progress and profile summary
    - Update phoneme stats
    - Update profile summary (weak/strong, overall score)
    - Update level_progress using latest data
    """
    profile = db.query(UserPronunciationProfile).filter_by(user_id=user_id).first()
    if not profile:
        return

    # 1. Increment exercises & time first
    profile.exercises_completed += 1
    profile.time_spent_total_secs += time_spent_secs
    db.commit()

    # 2. Update phoneme stats
    update_phoneme_stats(db, user_id, phoneme_results)

    # 3. Update profile summary (weak/strong phonemes & overall score)
    update_profile_summary(db, user_id)

    # 4. Update level progress
    update_level_progress(profile)

    db.commit()
    return {"status": "success"}