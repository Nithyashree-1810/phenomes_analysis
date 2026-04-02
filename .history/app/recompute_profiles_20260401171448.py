from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.pronunciation_models import UserPronunciationProfile, PhonemePerformance
from app.services.levelling_service import update_level_progress
from decimal import Decimal
from datetime import datetime

def recompute_profiles(db: Session):
    users = db.query(UserPronunciationProfile).all()
    
    for profile in users:
        phonemes = db.query(PhonemePerformance).filter_by(user_id=profile.user_id).all()
        weak, strong, scores = [], [], []

        for p in phonemes:
            acc = float(p.accuracy_pct or 0)
            scores.append(acc)
            
            if acc < 50:
                weak.append({"phoneme": p.phoneme, "error_rate": float(f"{100 - acc:.2f}")})
            elif acc >= 70:
                strong.append({"phoneme": p.phoneme, "accuracy": float(f"{acc:.2f}")})

        profile.weak_phonemes = weak
        profile.strong_phonemes = strong
        profile.overall_score_avg = (sum(scores) / len(scores)) if scores else 0
        profile.last_practice_at = datetime.utcnow()

        # Recompute level progress
        update_level_progress(profile)

    db.commit()
    print("Recomputed weak/strong phonemes, overall score, and level_progress for all users.")


if __name__ == "__main__":
    db = next(get_db())
    recompute_profiles(db)