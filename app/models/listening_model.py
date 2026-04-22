from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.db.base import Base


class ListeningSession(Base):
    __tablename__ = "listening_sessions"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    session_id     = Column(String(36), nullable=False, unique=True, index=True)
    passage        = Column(Text, nullable=False)
    audio_filename = Column(String(512), nullable=True)

    # Full questions stored with correct_option (never exposed to client)
    # Shape: [{"id": 1, "cefr_level": "B1", "question": "...",
    #           "options": {"A": "..", "B": "..", "C": "..", "D": ".."},
    #           "correct_option": "B"}]
    questions      = Column(JSONB, nullable=False)

    # Per-question evaluation results (populated after /evaluate)
    # Shape: [{"question_id": 1, "correct": true, "feedback": "..."}]
    results        = Column(JSONB, nullable=True)

    # CEFR grading (populated after /evaluate)
    cefr_level        = Column(String(8), nullable=True)   # e.g. "B1" or "B1+"
    ability_score     = Column(Float, nullable=True)       # 0.0 – 1.0
    accuracy_by_level = Column(JSONB, nullable=True)       # {"A1": 0.0, "B1": 1.0, ...}

    # Timestamps
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    evaluated_at = Column(DateTime(timezone=True), nullable=True)
