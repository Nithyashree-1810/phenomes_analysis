# services/transcription_service.py
from app.services.client import client

def transcribe_audio(file_path: str) -> str:
    """
    Transcribe audio using OpenAI's gpt-4o-transcribe model.
    Returns the transcript as a string.
    """
    try:
        with open(file_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=f
            )
        return response.text or ""
    except Exception as e:
       
        return ""