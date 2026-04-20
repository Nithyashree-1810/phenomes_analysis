# app/services/transcription_service.py
from __future__ import annotations
import logging
import math
from pathlib import Path
import numpy as np

import whisper
import soundfile as sf
from fastapi import Request

from app.core.config import get_settings

logger = logging.getLogger(__name__)
cfg = get_settings()


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class TranscriptionError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)

class SilentAudioError(TranscriptionError):
    def __init__(self):
        super().__init__("SILENT_AUDIO", "No speech detected in the audio.")

class AudioTooShortError(TranscriptionError):
    def __init__(self, duration: float):
        super().__init__(
            "AUDIO_TOO_SHORT",
            f"Audio is too short ({duration:.2f}s); minimum is 1 second.",
        )

class UnsupportedLanguageError(TranscriptionError):
    def __init__(self, detected: str):
        super().__init__(
            "UNSUPPORTED_LANGUAGE",
            f"Detected language '{detected}' is not supported; only English is accepted.",
        )


# ---------------------------------------------------------------------------
# FastAPI dependency — fetches already-loaded model from app.state
# ---------------------------------------------------------------------------

def get_whisper_model(request: Request) -> whisper.Whisper:
    """
    Returns the Whisper model loaded at startup via the lifespan handler.
    Inject with:  model: whisper.Whisper = Depends(get_whisper_model)
    """
    return request.app.state.whisper_model


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MIN_DURATION_S: float = 1.0
_SILENCE_AMPLITUDE_THRESHOLD: float = 1e-3

def check_duration(file_path: str | Path) -> None:
    info = sf.info(str(file_path))
    if info.duration < _MIN_DURATION_S:
        raise AudioTooShortError(info.duration)


def is_silent_audio(audio: np.ndarray, threshold: float = _SILENCE_AMPLITUDE_THRESHOLD) -> bool:
    if audio is None or audio.size == 0:
        return True

    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(np.square(audio, dtype=np.float64))))
    return peak <= threshold and rms <= threshold




# ---------------------------------------------------------------------------
# Confidence extraction
# ---------------------------------------------------------------------------

def get_confidence(result: dict) -> float:
    """
    Derive a [0.0, 1.0] confidence score from a raw Whisper result dict.

    Primary:  mean avg_logprob across segments → exp() → [0, 1]
    Fallback: mean token probability across segments
    Default:  0.0 if neither is available
    """
    try:
        segments = result.get("segments")
        if not segments:
            return 0.0

        total_logprob = 0.0
        count = 0
        for seg in segments:
            avg_lp = seg.get("avg_logprob")
            if isinstance(avg_lp, (int, float)):
                total_logprob += avg_lp
                count += 1

        if count > 0:
            return round(max(0.0, min(1.0, math.exp(total_logprob / count))), 3)

        # Fallback: token-level probabilities
        total_prob = 0.0
        token_count = 0
        for seg in segments:
            for tok in seg.get("tokens", []):
                p = tok.get("probability")
                if isinstance(p, (int, float)):
                    total_prob += p
                    token_count += 1

        return round(total_prob / token_count, 3) if token_count > 0 else 0.0

    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def transcribe_audio(file_path: str | Path, model: whisper.Whisper) -> tuple[str, float]:
    file_path = Path(file_path)
    use_fp16: bool = cfg.WHISPER_DEVICE != "cpu"

    check_duration(file_path)
    

    try:
        # ── Step 1: Detect silence and language first ─────────────────────────
        audio = whisper.load_audio(str(file_path))
        if is_silent_audio(audio):
            raise SilentAudioError()

        audio_pad = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio_pad).to(model.device)

        _, probs = model.detect_language(mel)
        detected_lang = max(probs, key=probs.get)

        logger.info("Detected language: %s (confidence: %.3f)", detected_lang, probs[detected_lang])

        if detected_lang != "en":
            logger.warning("Unsupported language detected: %s", detected_lang)
            raise UnsupportedLanguageError(detected_lang)

        # ── Step 2: Transcribe only if English ───────────────────────────────
        result: dict = model.transcribe(
            str(file_path),
            language="en",
            fp16=use_fp16,
        )

        text: str = result.get("text", "").strip().replace("\n", " ")
        while "  " in text:
            text = text.replace("  ", " ")

        if not text:
            raise SilentAudioError()

        confidence: float = get_confidence(result)

        logger.info(
            "Transcription complete (%d chars, confidence=%.3f): %s",
            len(text), confidence, text[:80],
        )
        return text, confidence

    except TranscriptionError:
        raise
    except Exception as exc:
        logger.error(
            "transcribe_audio failed — type=%s reason=%s path=%s",
            type(exc).__name__, exc, file_path,
        )
        raise