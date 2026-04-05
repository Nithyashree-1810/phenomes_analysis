import uuid
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.pronunciation_models import UserPronunciationProfile, PhonemePerformance
from app.repo.pronunciation_repo import get_or_create_profile
from app.services.post_ex_service import post_exercise_hook


# ── SQLite-compatible engine ──────────────────────────────────────────────────
@pytest.fixture(scope="function")
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Make SQLite handle UUID as string
    from sqlalchemy import event
    from sqlalchemy.dialects.postgresql import UUID, JSONB
    from sqlalchemy import String, Text
    import sqlalchemy.types as types

    # Override UUID → String for SQLite
    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        dbapi_connection.execute("PRAGMA journal_mode=WAL")

    # Patch UUID and JSONB to work with SQLite
    from sqlalchemy.dialects import sqlite
    from unittest.mock import patch

    with patch.dict("sqlalchemy.dialects.postgresql.__dict__", {
        "UUID": String,
        "JSONB": Text,
    }):
        Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)