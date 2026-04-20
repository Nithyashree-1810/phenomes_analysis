# app/routes/pronunciation_route.py
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import tempfile
from pathlib import Path

from app.services.audio_service import convert_to_wav
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
import asyncio

if TYPE_CHECKING:
    import whisper

from app.schema.pronunciation_schema import (
    PronunciationScoreResult,
    TranscribeResult,
)
from app.services.pronunciation_service import  score_with_reference
from app.services.transcription_service import (
    get_whisper_model,
    transcribe_audio,
    TranscriptionError,
    SilentAudioError,
    AudioTooShortError,
    UnsupportedLanguageError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pronunciation", tags=["Pronunciation"])


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

async def _upload_to_tmp(file: UploadFile) -> tuple[Path, str]:
    audio_bytes = await file.read()
    suffix = Path(file.filename).suffix if file.filename else ".wav"
    if not suffix:
        suffix = ".wav"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(audio_bytes)
    tmp.close()
    return Path(tmp.name), suffix.lstrip(".")


def _raise_transcription_http_error(exc: TranscriptionError) -> None:
    """Map TranscriptionError subclasses to appropriate HTTP status + detail."""
    status_map = {
        UnsupportedLanguageError: 422,
        AudioTooShortError:       422,
        SilentAudioError:         422,
    }
    status_code = status_map.get(type(exc), 422)
    raise HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "message": exc.detail},
    )


# ---------------------------------------------------------------------------
# POST /pronunciation/score
# ---------------------------------------------------------------------------

@router.post(
    "/score",
    response_model=PronunciationScoreResult,
    summary="Score pronunciation against a reference sentence",
)
async def pronunciation_score(
    file: UploadFile = File(..., description="Audio file (WAV preferred)."),
    reference_text: str = Form(..., description="The sentence the user was asked to read."),
    model: "whisper.Whisper" = Depends(get_whisper_model),
) -> PronunciationScoreResult:
    logger.info("POST /pronunciation/score — reference='%s'", reference_text[:60])

    tmp_path, ext = await _upload_to_tmp(file)
    try:
        result = await score_with_reference(
            tmp_path=tmp_path,
            ext=ext,
            reference_text=reference_text,
            model=model,
        )
        return result
    except UnsupportedLanguageError as exc:
        logger.warning("Unsupported language [%s]: %s", exc.code, exc.detail)
        raise HTTPException(
            status_code=422,
            detail={"code": exc.code, "message": exc.detail},
        )
    except AudioTooShortError as exc:
        logger.warning("Audio too short [%s]: %s", exc.code, exc.detail)
        _raise_transcription_http_error(exc)
    except SilentAudioError as exc:
        logger.warning("Silent audio [%s]: %s", exc.code, exc.detail)
        _raise_transcription_http_error(exc)
    except TranscriptionError as exc:
        logger.warning("Transcription issue [%s]: %s", exc.code, exc.detail)
        _raise_transcription_http_error(exc)
    except Exception as exc:
        logger.exception("Unexpected error in /pronunciation/score")
        raise HTTPException(status_code=500, detail="Scoring failed.") from exc
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# POST /pronunciation/transcribe
# ---------------------------------------------------------------------------

@router.post(
    "/transcribe",
    response_model=TranscribeResult,
    summary="Transcribe audio and return confidence",
)
async def pronunciation_transcribe(
    file: UploadFile = File(..., description="Audio file (WAV preferred)."),
    model: "whisper.Whisper" = Depends(get_whisper_model),
) -> TranscribeResult:
    logger.info("POST /pronunciation/transcribe — file='%s'", file.filename)

    tmp_path, ext = await _upload_to_tmp(file)
    wav_path: Path | None = None
    try:
        wav_path = await asyncio.to_thread(convert_to_wav, tmp_path, ext)
        transcript, confidence = await asyncio.to_thread(transcribe_audio, wav_path, model)
        return TranscribeResult(transcript=transcript, confidence=confidence)
    except UnsupportedLanguageError as exc:
        logger.warning("Unsupported language [%s]: %s", exc.code, exc.detail)
        _raise_transcription_http_error(exc)
    except AudioTooShortError as exc:
        logger.warning("Audio too short [%s]: %s", exc.code, exc.detail)
        _raise_transcription_http_error(exc)
    except SilentAudioError as exc:
        logger.warning("Silent audio [%s]: %s", exc.code, exc.detail)
        _raise_transcription_http_error(exc)
    except TranscriptionError as exc:
        logger.warning("Transcription issue [%s]: %s", exc.code, exc.detail)
        _raise_transcription_http_error(exc)
    except Exception as exc:
        logger.exception("Unexpected error in /pronunciation/transcribe")
        raise HTTPException(status_code=500, detail="Transcription failed.") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
        if wav_path and wav_path != tmp_path:
            wav_path.unlink(missing_ok=True)