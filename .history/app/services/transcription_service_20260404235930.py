# services/transcription_service.py
from app.services.llm_client import openai_client

def transcribe_audio(file_path: str) -> str:
    """
    Transcribe audio using OpenAI's gpt-4o-transcribe model.
    Returns the transcript as a clean string.
    """
    try:
        with open(file_path, "rb") as f:
            response = opeclient.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=f
            )

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
        return ""