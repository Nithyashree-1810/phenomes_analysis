from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from app.models.pronunciation_models import PhonemePerformance


def upsert_phoneme(db:Sess, user_id: int, phoneme: str, correct: bool):
    total_attempts = 1
    correct_attempts = 1 if correct else 0
    accuracy = (correct_attempts / total_attempts) * 100

    stmt = insert(PhonemePerformance).values(
        user_id=user_id,
        phoneme=phoneme,
        total_attempts=total_attempts,
        correct_attempts=correct_attempts,
        accuracy_pct=accuracy,
        last_attempted_at=datetime.utcnow(),
    )

    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "phoneme"],
        set_={
            "total_attempts": PhonemePerformance.total_attempts + 1,
            "correct_attempts": PhonemePerformance.correct_attempts
            + (1 if correct else 0),
            "accuracy_pct": (
                (
                    PhonemePerformance.correct_attempts
                    + (1 if correct else 0)
                )
                / (PhonemePerformance.total_attempts + 1)
                * 100
            ),
            "last_attempted_at": datetime.utcnow(),
        },
    )

    db.execute(stmt)