from sqlalchemy.orm import Session
from app.models.pronunciation_models import UserPronunciationProfile
from datetime import datetime


def get_profile(db: Session, user_id: int):
    return (
        db.query(UserPronunciationProfile)
        .filter(UserPronunciationProfile.user_id == user_id)
        .first()
    )


def create_profile(db: Session, user_id: int):
    profile = UserPronunciationProfile(
        user_id=user_id,
        current_level="basic",
        overall_score_avg=0,
        exercises_completed=0,
        time_spent_total_secs=0,
        weak_phonemes=[],
        strong_phonemes=[],
        level_p=[],
        last_practice_at=datetime.utcnow(),
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_profile(
    db: Session,
    profile: UserPronunciationProfile,
    score: float,
    time_spent_secs: int = 0,
    current_level: str | None = None,
):
    profile.exercises_completed += 1
    profile.time_spent_total_secs += time_spent_secs
    profile.last_practice_at = datetime.utcnow()

    # safe averaging
    if profile.overall_score_avg and float(profile.overall_score_avg) > 0:
        profile.overall_score_avg = (
            float(profile.overall_score_avg) + score
        ) / 2
    else:
        profile.overall_score_avg = score

    if current_level:
        profile.current_level = current_level

    db.commit()
    db.refresh(profile)
    return profile