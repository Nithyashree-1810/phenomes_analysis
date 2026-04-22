from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid

from app.db.session import get_db
from app.services.progress_service import (
    update_user_progress,
)
from app.repositories.pronunciation_progress_repository import get_progress


router = APIRouter(prefix="/progress", tags=["pronunciation-progress"])


@router.post("/update/{user_id}")
def update_progress(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Recompute and store progress (call after exercise completion)
    """
    progress = update_user_progress(db, user_id)

    return {"message": "Progress updated", "data": progress}


@router.get("/dashboard/{user_id}")
def get_dashboard(user_id: uuid.UUID, db: Session = Depends(get_db)):
    progress = get_progress(db, user_id)

    if not progress:
        return {"pronunciation": None}

    return {
        "pronunciation": {
            "total_levels": progress.total_levels,
            "current_level": progress.current_level,
            "completion_pct": float(progress.completion_pct),
            "avg_score": float(progress.avg_score),
            "weak_phonemes": progress.weak_phonemes,
            "time_spent_mins": progress.time_spent_mins,
        }
    }