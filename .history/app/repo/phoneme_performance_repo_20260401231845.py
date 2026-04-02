from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from app.models.pronunciation_models import PhonemePerformance


def upsert_phoneme(db, user_id, phoneme, total_attempts, correct_attempts):
    accuracy_pct = (
        (correct_attempts / total_attempts) * 100 if total_attempts > 0 else 0
    )

    stmt = insert(PhonemePerformance).values(
        user_id=user_id,
        phoneme=phoneme,
        total_attempts=total_attempts,
        correct_attempts=correct_attempts,
        accuracy_pct=accuracy_pct,
        last_attempted_at=datetime.utcnow(),
    )

    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "phoneme"],
        set_=dict(
            total_attempts=PhonemePerformance.total_attempts + total_attempts,
            correct_attempts=PhonemePerformance.correct_attempts
            + correct_attempts,
            accuracy_pct=(
                (
                    PhonemePerformance.correct_attempts
                    + correct_attempts
                )
                / (
                    PhonemePerformance.total_attempts
                    + total_attempts
                )
                * 100
            ),
            last_attempted_at=datetime.utcnow(),
        ),
    )

    db.execute(stmt)