
import logging
from pathlib import Path

from gtts import gTTS

from app.core.config import settings

logger = logging.getLogger(__name__)

AUDIO_DIR = Path(settings.STATIC_AUDIO_DIR)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def text_to_speech(text: str, filename: str) -> str:
    """
    Convert text to speech and save as mp3.

    Args:
        text: Text to synthesize.
        filename: Target filename (e.g. "passage_abc123.mp3").

    Returns:
        URL path for the frontend (e.g. "/static/audio/passage_abc123.mp3"),
        or "" on failure.
    """
    try:
        filepath = AUDIO_DIR / filename
        tts = gTTS(text=text, lang="en")
        tts.save(str(filepath))
        logger.debug("TTS saved: %s", filepath)
        return f"/static/audio/{filename}"
    except Exception as exc:
        logger.error("TTS failed for filename=%s: %s", filename, exc)
        return ""
