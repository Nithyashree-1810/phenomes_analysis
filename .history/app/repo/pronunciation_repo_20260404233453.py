
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.pronunciation_models import UserPronunciationProfile

logger = logging.getLogger(__name__)


def get_profile(db: Session, user_id: int) -> UserPronunciationProfile | None:
    return (
        db.query(UserPronunciationProfile)
        .filter(UserPronunciationProfile.user_id == user_id)
        .first()
    )


def get_or_create_profile(db: Session, user_id: int) -> UserPronunciationProfile:
    """Return existing profile or create a fresh one (flushed, not committed)."""
    profile = get_profile(db, user_id)
    if profile:
        return profile

    profile = UserPronunciationProfile(
        user_id=user_id,
        current_level="basic",
        overall_score_avg=0,
        exercises_completed=0,
        time_spent_total_secs=0,
        weak_phonemes=[],
        strong_phonemes=[],
        level_progress={},
        last_practice_at=datetime.now(timezone.utc),
    )
    db.add(profile)
    db.flush()  # assign PK, satisfy FKs — caller must commit
    logger.debug("Created new pronunciation profile for user_id=%s", user_id)
    return profile


def update_profile(
    db: Session,
    profile: UserPronunciationProfile,
    score: float,
    time_spent_secs: int = 0,
    current_level: str | None = None,
    strong_phonemes: list[str] | None = None,
    weak_phonemes: list[str] | None = None,
) -> UserPronunciationProfile:
    """
    Increment exercise counters and update the running average score.
    """
    n = (profile.exercises_completed or 0) + 1
    old_avg = float(profile.overall_score_avg or 0)

    # Correct running weighted average
    profile.overall_score_avg = round((old_avg * (n - 1) + score) / n, 2)
    profile.exercises_completed = n
    profile.time_spent_total_secs = (profile.time_spent_total_secs or 0) + time_spent_secs
    profile.last_practice_at = datetime.now(timezone.utc)

    if current_level:
        profile.current_level = current_level
    if strong_phonemes is not None:
        profile.strong_phonemes = strong_phonemes
    if weak_phonemes is not None:
        profile.weak_phonemes = weak_phonemes

    db.commit()
    db.refresh(profile)
    return profile
