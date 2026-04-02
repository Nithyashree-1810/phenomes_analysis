# app/models/pronunciation_models.py
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Numeric, DateTime, JSON
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class UserPronunciationProfile(Base):
    __tablename__ = "user_pronunciation_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False)

    current_level = Column(String(20), default="basic")
    overall_score_avg = Column(Numeric(5, 2), default=0)
    exercises_completed = Column(Integer, default=0)
    time_spent_total_secs = Column(Integer, default=0)

    weak_phonemes = Column(JSONB, default=list)
    strong_phonemes = Column(JSONB, default=list)

    # ← THIS IS THE ONLY LEVEL TRACKING FIELD
    level_progress = Column(JSONB, default=dict)

    last_practice_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    phoneme_stats = relationship(
        "PhonemePerformance",
        back_populates="profile",
        cascade="all, delete-orphan",
        primaryjoin="UserPronunciationProfile.user_id==PhonemePerformance.user_id"
    )