from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, DateTime, Numeric, UniqueConstraint, ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class UserPronunciationProgress(Base):
    __tablename__ = "user_pronunciation_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
    )

    total_levels = Column(Integer, default=5, nullable=False)
    current_level = Column(String(20), default="beginner", nullable=False)
    completion_pct = Column(Numeric(5, 2), default=0)
    avg_score = Column(Numeric(5, 2), default=0)
    weak_phonemes = Column(JSONB, default=list)
    time_spent_mins = Column(Integer, default=0, nullable=False)

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
    )