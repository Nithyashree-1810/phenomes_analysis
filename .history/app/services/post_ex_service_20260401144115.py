# app/services/post_exercise_hook.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.pronunciation_result import PronunciationResult
from app.models.pronunciation_profile import UserPronunciationProfile

from app.services.leveling_service import should_level_up, get_next_level

# Initialize clients



async def update_user_pronunciation_profile_db(
    db: AsyncSession, user_id: str, current_level: str, score: float, mispronounced_phonemes: list
):
    """
    Update or create UserPronunciationProfile in DB.
    """
    profile = await db.get(UserPronunciationProfile, user_id)
    if not profile:
        profile = UserPronunciationProfile(
            user_id=user_id,
            current_level=current_level,
            overall_score_avg=score,
            exercises_completed=1,
            weak_phonemes=mispronounced_phonemes,
        )
        db.add(profile)
    else:
        # Update existing profile
        profile.current_level = current_level
        profile.exercises_completed += 1
        profile.overall_score_avg = float(
            (profile.overall_score_avg * (profile.exercises_completed - 1) + score)
            / profile.exercises_completed
        )
        profile.weak_phonemes = mispronounced_phonemes
    await db.commit()
    await db.refresh(profile)
    return profile


async def post_exercise_hook(user_id: str, result: PronunciationResult, db: AsyncSession):
    """
    Called after pronunciation exercise completion.
    """
    # 1️⃣ Update user profile in DB
    profile = await update_user_pronunciation_profile_db(
        db=db,
        user_id=user_id,
        current_level=result.difficulty_level,
        score=result.overall_score,
        mispronounced_phonemes=[m["expected"] for m in result.mistakes],
    )

    # 2️⃣ Store the exercise result
    result_entry = PronunciationResult(
        user_id=user_id,
        reference_text=result.reference_text,
        transcript=result.transcript,
        pronunciation_score=result.overall_score,
        total_mistakes=len(result.mistakes),
        mistakes=result.mistakes,
        improvement_tips=result.tips,
        audio_path=getattr(result, "audio_path", None)
    )
    db.add(result_entry)
    await db.commit()
    await db.refresh(result_entry)

    # 3️⃣ Report to Progress Tracking Service
    await progress_tracking_client.record(
        user_id=user_id,
        module="pronunciation",
        topic=result.difficulty_level,
        subtopic=getattr(result, "sentence_category", "default"),
        score=result.overall_score,
        time_spent_secs=getattr(result, "duration_secs", 0),
    )

    # 4️⃣ Check if level-up is needed
    if should_level_up(profile.user_id, result):
        await learning_path_client.update_module_level(
            user_id=profile.user_id,
            module="pronunciation",
            new_level=get_next_level(result.difficulty_level),
        )