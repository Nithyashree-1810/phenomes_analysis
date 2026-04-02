# app/services/levelling_service.py

LEVEL_ORDER = ["basic", "intermediate", "advanced"]

LEVEL_REQUIREMENTS = {
    "basic": 20,
    "intermediate": 20,
    "advanced": 30
}


def update_level_progress(profile):
    """
    Safely update the level_progress stored inside the profile.
    - Updates exercises_at_level
    - Updates avg_score_at_level
    - Checks and promotes user if required
    """

    current_level = profile.current_level
    required = LEVEL_REQUIREMENTS.get(current_level, 20)

    progress = profile.level_progress or {}

    # Increment exercises at current level if not already promoted this session
    exercises_done = progress.get("exercises_at_level", 0) + 1

    profile.level_progress = {
        "current": current_level,
        "exercises_at_level": exercises_done,
        "required_for_next": required,
        "avg_score_at_level": float(profile.overall_score_avg)
    }

    # Promote if eligible
    if exercises_done >= required:
        _promote_user(profile)


def _promote_user(profile):
    """
    Promote the user to the next level if possible and reset level_progress.
    """

    current = profile.current_level
    if current not in LEVEL_ORDER:
        return

    idx = LEVEL_ORDER.index(current)

    if idx < len(LEVEL_ORDER) - 1:
        next_level = LEVEL_ORDER[idx + 1]
        profile.current_level = next_level

        # Reset progress for new level
        profile.level_progress = {
            "current": next_level,
            "exercises_at_level": 0,
            "required_for_next": LEVEL_REQUIREMENTS[next_level],
            "avg_score_at_level": 0
        }