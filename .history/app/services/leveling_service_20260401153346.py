# app/services/levelling_service.py

LEVEL_ORDER = ["basic", "intermediate", "advanced"]

LEVEL_REQUIREMENTS = {
    "basic": 20,
    "intermediate": 20,
    "advanced": 30
}


def update_level_progress(profile):
    """
    Safely update level_progress stored inside the profile.
    Keeps stable structure and ensures promotion when required.
    """

    current = profile.current_level
    required = LEVEL_REQUIREMENTS.get(current, 20)

    progress = profile.level_progress or {}

    # Ensure structure
    exercises_done = progress.get("exercises_at_level", 0) + 1

    profile.level_progress = {
        "current": current,
        "exercises_at_level": exercises_done,
        "required_for_next": required,
        "avg_score_at_level": float(profile.overall_score_avg)
    }

    # Promote if eligible
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

        profile.level_progress = {
            "current": new_level,
            "exercises_at_level": 0,
            "required_for_next": LEVEL_REQUIREMENTS[new_level],
            "avg_score_at_level": 0
        }