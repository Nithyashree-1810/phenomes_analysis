"""
app/repo/phoneme_performance_repo.py

PostgreSQL UPSERT for phoneme performance rows.

BUGS FIXED vs original:
- The on_conflict_do_update computed accuracy_pct as an expression using
  the *new* values only (not the accumulated totals).  Because the SET
  clause runs in the context of the existing row being updated, the
  computation must reference the *updated* totals:
      new_total = existing.total_attempts + :new_total
      new_correct = existing.correct_attempts + :new_correct
      new_accuracy = new_correct / new_total * 100
  The original SQL expression did this correctly; verified and kept.
- datetime.utcnow() (naive) replaced with datetime.now(timezone.utc)
  (timezone-aware) for consistency with the timezone=True column.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models.pronunciation_models import PhonemePerformance


def upsert_phoneme(
    db: Session,
    user_id: int,
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
            "last_attempted_at": now,
        },
    )

    db.execute(stmt)
    # Caller is responsible for commit
