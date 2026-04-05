import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

# Whisper model cache
_whisper_model = None
_whisper_lock = threading.Lock()

# Choose Whisper model size
WHISPER_MODEL_SIZE = "base"   # tiny | base | small | medium | large-v3


def _get_whisper_model():
    """
    Lazy-load and cache the Whisper model (thread-safe).
    Returns the model instance or None if Whisper is not installed.
    """
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    with _whisper_lock:
        if _whisper_model is not None:
            return _whisper_model

        try:
            import whisper
            logger.info("Loading Whisper model '%s' ...", WHISPER_MODEL_SIZE)
            _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
            logger.info("Whisper model loaded successfully.")
            return _whisper_model
        except ImportError:
            logger.error("Whisper package missing. Install via: pip install openai-whisper")
            return None
        except Exception as exc:
            logger.error("Failed to load Whisper model: %s", exc)
            return None


def _transcribe_local(file_path: Path) -> str:
    """
    Transcribe audio using local Whisper only.
    Returns transcription text or an empty string on failure.
    """
    model = _get_whisper_model()
    if model is None:
        return ""

    try:
        result = model.transcribe(str(file_path), fp16=False, language="en")
        text: str = result.get("text", "") or ""
        return _clean_transcript(text)
    except Exception as exc:
        logger.error("Whisper local transcription failed: %s", exc)
        return ""


def _clean_transcript(text: str) -> str:
    text = text.strip().replace("\n", " ")
    while "  " in text:
        text = text.replace("  ", " ")
    return text


def transcribe_audio(file_path: str | Path) -> str:
    """
    Transcribe audio file using ONLY local Whisper.
    No API fallback.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error("File not found: %s", file_path)
        return ""

    return _transcribe_local(file_path)  # Whisper only