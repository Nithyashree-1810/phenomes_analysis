# app/services/pronunciation_service.py
from __future__ import annotations

import logging
from pathlib import Path
import whisper

from app.schema.pronunciation_schema import (
    PronunciationScoreResult,
    TranscribeResult,
    WordScore,
)
from app.services.audio_service import convert_to_wav
from app.services.scoring_service import compute_pronunciation_scores, extract_ipa, normalize_ipa
   

from app.services.transcription_service import TranscriptionError, check_duration, transcribe_audio,UnsupportedLanguageError,SilentAudioError,AudioTooShortError


logger = logging.getLogger(__name__)

_VALID_CEFR = frozenset({"A1", "A2", "B1", "B2", "C1", "C2"})


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint 1 — score with reference text
# ─────────────────────────────────────────────────────────────────────────────


async def score_with_reference(
    tmp_path: Path,
    ext: str,
    reference_text: str,
    model: whisper.Whisper,
    cefr_level: str = "B1",
) -> PronunciationScoreResult:
    import asyncio

    cefr_level = _normalise_cefr(cefr_level)
    wav_path: Path = await asyncio.to_thread(convert_to_wav, tmp_path, ext)

    try:
        await asyncio.to_thread(check_duration, wav_path)
        transcript, _confidence = await asyncio.to_thread(transcribe_audio, wav_path, model)
    except TranscriptionError:
        raise  # ← never swallow, let route handle it
    except Exception:
        raise
    finally:
        if wav_path != tmp_path:
            wav_path.unlink(missing_ok=True)

    if not isinstance(transcript, str) or not transcript:
        raise ValueError("Whisper returned an empty or invalid transcript.")

    scores: dict = await asyncio.to_thread(
        compute_pronunciation_scores,
        reference_text,
        transcript,
        cefr_level,
    )

    if not scores:
        raise ValueError("Scoring service returned no results.")

    required_keys = {"overall_score", "mistakes", "weak_phonemes"}
    missing = required_keys - scores.keys()
    if missing:
        raise ValueError(f"Scoring service response missing keys: {missing}")

    word_breakdown: list[WordScore] = _build_word_breakdown(
        mistakes=scores["mistakes"],
        reference_text=reference_text,
    )

    mispronounced_words: list[str] = [
        ws.word for ws in word_breakdown if not ws.correct
    ]

    overall_score: float = round(scores["overall_score"] / 100, 3)
    overall_score = max(0.0, min(1.0, overall_score))

    return PronunciationScoreResult(
        overall_score=overall_score,
        word_breakdown=word_breakdown,
        mispronounced_words=mispronounced_words,
        transcript=transcript,
    )
# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _normalise_cefr(cefr_level: str) -> str:
    level = cefr_level.upper().strip()
    if level not in _VALID_CEFR:
        logger.warning("Invalid CEFR level '%s' received — defaulting to B1.", cefr_level)
        return "B1"
    return level


def _get_word_ipa(word: str) -> str:
    """
    Extract and normalise IPA for a single word.
    Returns "" if espeak-ng and epitran both fail.
    """
    raw = extract_ipa(word)
    return normalize_ipa(raw)


def _build_word_breakdown(
    mistakes: list[dict],
    reference_text: str,
) -> list[WordScore]:
    """
    Build a WordScore for every word in the reference text.

    expected_phoneme — IPA of the reference word (from espeak-ng/epitran)
    actual_phoneme   — IPA of what was actually spoken (from espeak-ng/epitran
                       applied to the spoken word), or "" if word was missing
    score            — 1.0 if correct, 0.3 if wrong, 0.0 if missing
    correct          — True only when score == 1.0
    """
    ref_words: list[str] = reference_text.lower().split()

    # Index mistakes by expected word — "wrong" and "missing" types only
    mistake_map: dict[str, dict] = {}
    for m in mistakes:
        if m["type"] in ("wrong", "missing") and m.get("expected"):
            mistake_map[m["expected"].lower()] = m

    word_scores: list[WordScore] = []
    for word in ref_words:
        # Always compute expected IPA from the reference word
        expected_phoneme = _get_word_ipa(word)

        mistake = mistake_map.get(word)
        if mistake:
            spoken_word = mistake.get("spoken", "")
            # Compute IPA of what was actually spoken (empty string if missing)
            actual_phoneme = _get_word_ipa(spoken_word) if spoken_word else ""
            score = 0.0 if mistake["type"] == "missing" else 0.3
            word_scores.append(
                WordScore(
                    word=word,
                    expected_phoneme=word,
                    actual_phoneme=spoken_word,
                    score=score,
                    correct=False,
                )
            )
        else:
            # Word matched — actual == expected
            word_scores.append(
                WordScore(
                    word=word,
                    expected_phoneme=word,
                    actual_phoneme=word,  # correctly pronounced
                    score=1.0,
                    correct=True,
                )
            )

    return word_scores