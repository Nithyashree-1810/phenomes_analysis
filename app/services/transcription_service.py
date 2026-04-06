import logging
from pathlib import Path

from app.services.llm_client import openai_client

logger = logging.getLogger(__name__)


def transcribe_audio(file_path: str | Path) -> str:
    """
    Transcribe audio using OpenAI Whisper (whisper-1).
    Returns the transcript as a clean string, or "" on failure.
    """
    try:
        with open(file_path, "rb") as f:
            response = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en",        # force English — faster + more accurate
                response_format="text" # returns plain string directly
            )

        text = response.strip().replace("\n", " ").replace("  ", " ")
        logger.info("Transcription complete: %s", text[:80])
        return text

    except Exception as exc:
        logger.error(
            "transcribe_audio failed — type=%s reason=%s path=%s",
            type(exc).__name__, exc, file_path
        )
        return ""