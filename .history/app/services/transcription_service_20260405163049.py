import logging
from app.services.llm_client import openai_client

logger = logging.getLogger(__name__)

def transcribe_audio(file_path: str) -> str:
    try:
        with open(file_path, "rb") as f:
            response = openai_client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=f
            )

        text = getattr(response, "text", None) or ""
        if text:
            text = text.strip().replace("\n", " ").replace("  ", " ")

        return text

    except Exception as exc:
        logger.error("transcribe_audio failed — type=%s reason=%s path=%s", type(exc).__name__, exc, file_path)
        return ""