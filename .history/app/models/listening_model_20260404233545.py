
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.db.base import Base


class ListeningAttempt(Base):
    __tablename__ = "listening_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, index=True)   # UUID string
    passage = Column(Text, nullable=False)
    questions = Column(JSONB)
    user_transcript = Column(Text, nullable=False)
    similarity_score = Column(Float, nullable=False)
    audio_filename = Column(String)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
