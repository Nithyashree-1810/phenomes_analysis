"""
app/core/config.py
Centralised application settings loaded from environment / .env file.
All other modules import from here — never call os.getenv() directly.
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── Database ────────────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── OpenAI ──────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str

    # ── LangSmith ───────────────────────────────────────────────────────────
   
    # ── App ─────────────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # ── Audio ───────────────────────────────────────────────────────────────
    STATIC_AUDIO_DIR: str = "app/static/audio"
    TEMP_DIR: str = "temp"

    # ── Whisper ─────────────────────────────────────────────────────────────
    WHISPER_MODEL: str = "medium.en"

    class Config:
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
