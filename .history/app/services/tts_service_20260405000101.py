
import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Whisper model is expensive to load (~1-2s), so cache it after first load ─
_whisper_model = None
_whisper_lock = threading.Lock()  # thread-safe lazy init

WHISPER_MODEL_SIZE = "base"  # tiny | base | small | medium | large-v3
                              # base  = good accuracy, fast, ~140MB
                              # small = better accuracy,  ~460MB
                              # large-v3 = best accuracy, ~2.9GB


def _get_whisper_model():
    """
    Lazy-load and cache the Whisper model.
    Thread-safe — safe to call from concurrent requests.
    """
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    with _whisper_lock:
        # Double-checked locking — another thread may have loaded it
        if _whisper_model is not None:
            return _whisper_model
        try:
            import whisper  # lazy import — optional dependency
            logger.info("Loading Whisper model '%s' ...", WHISPER_MODEL_SIZE)
            _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
            logger.info("Whisper model loaded successfully.")
            return _whisper_model
        except ImportError:
            logger.warning(
                "openai-whisper not installed. "
                "Run: pip install openai-whisper"
            )
            return None
        except Exception as exc:
            logger.error("Failed to load Whisper model: %s", exc)
            return None


# ── Local Whisper transcription ───────────────────────────────────────────────

def _transcribe_local(file_path: Path) -> str:
    """
    Transcribe using local Whisper model.
    Returns transcript string or "" on failure.
    """
    model = _get_whisper_model()
    if model is None:
        return ""

    try:
        # fp16=False ensures CPU compatibility (no silent NaN issues on CPU)
        result = model.transcribe(str(file_path), fp16=False, language="en")
        text: str = result.get("text", "") or ""
        text = _clean_transcript(text)
        logger.debug("Local Whisper transcribed %d chars", len(text))
        return text
    except Exception as exc:
        logger.error("Local Whisper transcription failed: %s", exc)
        return ""


# ── API fallback (gpt-4o-transcribe) ─────────────────────────────────────────

"""def _transcribe_api(file_path: Path) -> str:
    """
    Fallback: transcribe via OpenAI gpt-4o-transcribe API.
    Only called if local Whisper is unavailable.
    """
    try:
        from app.services.llm_client import openai_client
        with open(file_path, "rb") as f:
            response = openai_client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=f,
            )
        text: str = getattr(response, "text", "") or ""
        text = _clean_transcript(text)
        logger.debug("API transcription transcribed %d chars", len(text))
        return text
    except Exception as exc:
        logger.error("API transcription fallback failed: %s", exc)
        return ""


# ── Shared text cleanup ───────────────────────────────────────────────────────

def _clean_transcript(text: str) -> str:
    #Normalize whitespace in transcript.
    text = text.strip().replace("\n", " ")
    while "  " in text:
        text = text.replace("  ", " ")
    return text"""


# ── Public entry point ────────────────────────────────────────────────────────

def transcribe_audio(file_path: str | Path) -> str:
    """
    Transcribe an audio file.

    Strategy:
        1. Try local Whisper (free, private, no internet needed)
        2. Fall back to gpt-4o-transcribe API if Whisper unavailable

    Returns the transcript string, or "" on failure (caller must handle).
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error("transcribe_audio: file not found — %s", file_path)
        return ""

    # Try local first
    text = _transcribe_local(file_path)
    if text:
        return text

    # API fallback
    logger.warning(
        "Local Whisper unavailable — falling back to gpt-4o-transcribe API."
    )
    return _transcribe_api(file_path)