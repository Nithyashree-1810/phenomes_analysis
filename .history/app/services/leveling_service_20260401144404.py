# app/services/levelling_service.py

LEVEL_ORDER = ["basic", "intermediate", "advanced"]

LEVEL_REQUIREMENTS = {
    "basic": 20,
    "intermediate": 25,
    "advanced": 30
}


def update_level_progress(profile):
    """
    Update the level_progress dictionary inside the profile safely.
    Ensures consistent structure and no missing fields.
    """

    current_level = profile.current_level
    exercises_done = profile.exercises_completed

    required = LEVEL_REQUIREMENTS.get(current_level, 20)

    progress = profile.level_progress or {}

    # Guarantee consistent structure
    profile.level_progress = {
        "current": current_level,
        "exercises_at_level": progress.get("exercises_at_level", 0) + 1,
        "required_for_next": required,
        "avg_score_at_level": float(profile.overall_score_avg)
    }

    # Check if level can advance
    if profile.level_progress["exercises_at_level"] >= required:
        _promote_level(profile)


def _promote_level(profile):
    """
    Promote user to the next level if possible.
    """

    current = profile.current_level
    if current not in LEVEL_ORDER:
        return

    idx = LEVEL_ORDER.index(current)

    if idx < len(LEVEL_ORDER) - 1:
        next_lvl = LEVEL_ORDER[idx + 1]
        profile.current_level = next_lvl

        # Reset progress for new level
        profile.level_progress = {
            "current": next_lvl,
            "exercises_at_level": 0,
            "required_for_next": LEVEL_REQUIREMENTS[next_lvl],
            "avg_score_at_level": 0
        }