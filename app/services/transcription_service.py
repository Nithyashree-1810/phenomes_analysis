import logging
from pathlib import Path

from app.services.llm_client import openai_client

logger = logging.getLogger(__name__)


def transcribe_audio(file_path: str | Path) -> str:
    """
<<<<<<< HEAD
    Transcribe audio using OpenAI Whisper (whisper-1).
    Returns the transcript as a clean string, or "" on failure.
=======
    Transcribe audio using OpenAI's gpt-4o-transcribe model.
    Returns the transcript as a clean string.
>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f
    """
    try:
        with open(file_path, "rb") as f:
            response = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en",        # force English — faster + more accurate
                response_format="text" # returns plain string directly
            )

<<<<<<< HEAD
        text = response.strip().replace("\n", " ").replace("  ", " ")
        logger.info("Transcription complete: %s", text[:80])
        return text

    except Exception as exc:
        logger.error(
            "transcribe_audio failed — type=%s reason=%s path=%s",
            type(exc).__name__, exc, file_path
        )
=======
        # Safely extract text
        text = (
            getattr(response, "text", None)
            or response.get("text")
            or response.get("transcript")
            or ""
        )

        # Normalize
        if text:
            text = text.strip().replace("\n", " ").replace("  ", " ")

        return text

    except Exception as e:
>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f
        return ""