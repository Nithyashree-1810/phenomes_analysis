# app/models/pronunciation_models.py
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Numeric, JSON, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

# ---------------------------------------
# User Pronunciation Profile
# ---------------------------------------
class UserPronunciationProfile(Base):
    __tablename__ = "user_pronunciation_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # IMPORTANT: Now a proper Integer user ID, a unique user record
    user_id = Column(Integer, unique=True, nullable=False)

    current_level = Column(String(20), default="basic")
    overall_score_avg = Column(Numeric(5, 2), default=0)
    exercises_completed = Column(Integer, default=0)
    time_spent_total_secs = Column(Integer, default=0)

    weak_phonemes = Column(JSONB, default=list)
    strong_phonemes = Column(JSONB, default=list)
    level_history = Column(JSONB, default=list)
    level_progress=

    last_practice_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # PhonemePerformance.user_id → UserPronunciationProfile.user_id
    phoneme_stats = relationship(
        "PhonemePerformance",
        back_populates="profile",
        cascade="all, delete-orphan",
        primaryjoin="UserPronunciationProfile.user_id==PhonemePerformance.user_id"
    )


# ---------------------------------------
# Phoneme Performance
# ---------------------------------------
class PhonemePerformance(Base):
    __tablename__ = "phoneme_performance"
    __table_args__ = (
        UniqueConstraint("user_id", "phoneme", name="uq_user_phoneme"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # FK → references the INTEGER column user_pronunciation_profile.user_id
    user_id = Column(
        Integer,
        ForeignKey("user_pronunciation_profile.user_id", ondelete="CASCADE"),
        nullable=False
    )

    phoneme = Column(String(50), nullable=False)
    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    accuracy_pct = Column(Numeric(5, 2), default=0)
    last_attempted_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    profile = relationship(
        "UserPronunciationProfile",
        back_populates="phoneme_stats",
        primaryjoin="PhonemePerformance.user_id==UserPronunciationProfile.user_id"
    )