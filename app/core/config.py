"""
app/core/config.py
Centralised application settings loaded from environment / .env file.
All other modules import from here — never call os.getenv() directly.
"""
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ────────────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── OpenAI (keep for other modules) ─────────────────────────────────────
    #OPENAI_API_KEY: str = ""

    # ── Azure OpenAI (for listening module) ─────────────────────────────────
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str          # e.g. https://<resource>.openai.azure.com/
    AZURE_OPENAI_API_VERSION: str =  "2025-01-01-preview"
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "o4-mini-2025-04-16"

    # ── Azure Speech (for TTS / pronunciation) ───────────────────────────────
    #AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = "eastus2"

    # ── LangSmith ───────────────────────────────────────────────────────────
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "phenome_analysis_agent"

    # ── App ─────────────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # ── Audio ───────────────────────────────────────────────────────────────
    STATIC_AUDIO_DIR: str = "app/static/audio"
    TEMP_DIR: str = "temp"

    # ── Whisper ─────────────────────────────────────────────────────────────
    WHISPER_MODEL: str = "small"
    WHISPER_DEVICE: str = "cpu"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()