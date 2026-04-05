
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import uuid

from app.models.pronunciation_models import PhonemePerformance


def upsert_phoneme(
    db: Session,
    user_id: uuid.UUID,
    phoneme: str,
    correct: bool,
    total_attempts: int = 1,
    correct_attempts: int | None = None,
) -> None:
    """
    Insert or update a PhonemePerformance row for (user_id, phoneme).

    On conflict (duplicate user_id + phoneme) the totals are accumulated
    and accuracy_pct is recomputed from the new totals.
    """
    if correct_attempts is None:
        correct_attempts = 1 if correct else 0

    now = datetime.now(timezone.utc)

    stmt = insert(PhonemePerformance).values(
        id=uuid.uuid4(),
        user_id=user_id,
        phoneme=phoneme,
        total_attempts=total_attempts,
        correct_attempts=correct_attempts,
        accuracy_pct=round(correct_attempts / total_attempts * 100, 2) if total_attempts > 0 else 0.0,
        last_attempted_at=now,
    )

    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "phoneme"],
        set_={
            "total_attempts": PhonemePerformance.total_attempts + total_attempts,
            "correct_attempts": PhonemePerformance.correct_attempts + correct_attempts,
            # Recompute accuracy from the new cumulative totals
            "accuracy_pct": (
                (PhonemePerformance.correct_attempts + correct_attempts)
                / (PhonemePerformance.total_attempts + total_attempts)
                * 100
            ),
<<<<<<< HEAD
            "last_attempted_at": now,
=======
            "last_attempted_at": datetime.utcnow(),
>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f
        },
    )

    db.execute(stmt)
<<<<<<< HEAD
    # Caller is responsible for commit
=======



"""from datetime import datetime

from requests import Session
from sqlalchemy.dialects.postgresql import insert
from app.models.pronunciation_models import PhonemePerformance


def upsert_phoneme(db: Session, user_id: int, phoneme: str, correct: bool):
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

    db.execute(stmt)"""
>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f
