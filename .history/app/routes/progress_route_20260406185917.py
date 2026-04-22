from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid

from app.db.session import get_db
from app.repositories.pronunciation_repo import get_profile


router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/dashboard/{user_id}")
def get_dashboard(user_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = get_profile(db, user_id)

    if not profile:
        return {"pronunciation": None}

    return {
        "pronunciation": {
            "total_levels": 5,
            "current_level": profile.current_level,
            "completion_pct": round(profile.exercises_completed / 50 * 100, 2),
            "avg_score": float(profile.overall_score_avg),
            "weak_phonemes": profile.weak_phonemes,
            "time_spent_mins": profile.time_spent_total_secs // 60,
        }
    }