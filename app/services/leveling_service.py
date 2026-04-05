<<<<<<< HEAD

import logging
from app.models.pronunciation_models import UserPronunciationProfile

logger = logging.getLogger(__name__)

LEVEL_ORDER = ["basic", "intermediate", "advanced"]

LEVEL_REQUIREMENTS: dict[str, int] = {
    "basic": 20,
    "intermediate": 20,
    "advanced": 30,
}

# Minimum average score required to level up
LEVEL_UP_SCORE_THRESHOLD = 70.0


def update_level_progress(profile: UserPronunciationProfile) -> None:
    """
    Recalculate level_progress for the profile after each exercise.
    Promotes the user when both the exercise count AND score threshold
    are met.
    """
    current = profile.current_level or "basic"
    required = LEVEL_REQUIREMENTS.get(current, 20)
    avg_score = float(profile.overall_score_avg or 0)

    exercises_at_level = profile.exercises_completed or 0


    
    profile.level_progress = {
        "current": current,
        "exercises_at_level": exercises_at_level,
        "required_for_next": required,
        "avg_score_at_level": round(avg_score, 2),
        "next_level": LEVEL_ORDER[LEVEL_ORDER.index(current) + 1]
            if current in LEVEL_ORDER and LEVEL_ORDER.index(current) < len(LEVEL_ORDER) - 1
            else None,
    }

    # Promote only if both conditions satisfied
    if exercises_at_level >= required and avg_score >= LEVEL_UP_SCORE_THRESHOLD:
        _promote_user(profile)


def _promote_user(profile: UserPronunciationProfile) -> None:
    """Advance the user to the next level and reset per-level progress."""
    current = profile.current_level or "basic"

    if current not in LEVEL_ORDER:
        logger.warning("Unknown level '%s' — cannot promote.", current)
        return

    idx = LEVEL_ORDER.index(current)
    if idx >= len(LEVEL_ORDER) - 1:
        logger.info("User %s is already at max level (%s).", profile.user_id, current)
        return

    new_level = LEVEL_ORDER[idx + 1]
    logger.info(
        "Promoting user %s: %s → %s", profile.user_id, current, new_level
    )

    profile.current_level = new_level
    profile.level_progress = {
        "current": new_level,
        "exercises_at_level": 0,
        "required_for_next": LEVEL_REQUIREMENTS[new_level],
        "avg_score_at_level": 0.0,
    }
=======
LEVEL_ORDER = ["basic", "intermediate", "advanced"]

LEVEL_REQUIREMENTS = {
    "basic": 20,
    "intermediate": 20,
    "advanced": 30
}


def update_level_progress(profile):
    """
    Safely update level_progress inside the profile.
    Uses latest exercises_completed and overall_score_avg.
    Promotes the user if required.
    """

    current = profile.current_level
    required = LEVEL_REQUIREMENTS.get(current, 20)

    progress = profile.level_progress or {}

    # Increment exercises_at_level
    exercises_done = progress.get("exercises_at_level", 0) + 1

    # Update level_progress
    profile.level_progress = {
        "current": current,
        "exercises_at_level": exercises_done,
        "required_for_next": required,
        "avg_score_at_level": float(profile.overall_score_avg or 0)
    }

    # Promote user if eligible
    if exercises_done >= required:
        _promote_user(profile)


def _promote_user(profile):
    """Promote user to next level and reset progress."""

    current = profile.current_level
    if current not in LEVEL_ORDER:
        return

    idx = LEVEL_ORDER.index(current)

    if idx < len(LEVEL_ORDER) - 1:
        new_level = LEVEL_ORDER[idx + 1]
        profile.current_level = new_level

        # Reset level_progress for new level
        profile.level_progress = {
            "current": new_level,
            "exercises_at_level": 0,
            "required_for_next": LEVEL_REQUIREMENTS[new_level],
            "avg_score_at_level": 0
        }
>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f
