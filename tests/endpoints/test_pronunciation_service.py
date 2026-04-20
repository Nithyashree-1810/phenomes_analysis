from __future__ import annotations

import io
import math
import struct
import tempfile
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_wav_path(duration_s: float = 2.0) -> Path:
    sample_rate = 16000
    n_samples = int(duration_s * sample_rate)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            v = int(32767 * math.sin(2 * math.pi * 440 * i / sample_rate))
            wf.writeframes(struct.pack("<h", v))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(buf.getvalue())
    tmp.close()
    return Path(tmp.name)


def _mock_scores(overall: float = 85.0) -> dict:
    return {
        "overall_score": overall,
        "mistakes": [],
        "weak_phonemes": [],
        "tips": [],
        "passed": True,
        "passing_score": 70.0,
        "phoneme_score": 88.0,
        "fluency_score": 0.9,
    }


def _mock_scores_with_mistakes() -> dict:
    return {
        "overall_score": 55.0,
        "mistakes": [
            {"type": "wrong",   "expected": "hello", "spoken": "helo"},
            {"type": "missing", "expected": "world", "spoken": ""},
        ],
        "weak_phonemes": [
            {"word": "hello", "phoneme": "/h/"},
            {"word": "world", "phoneme": "/w/"},
        ],
        "tips": [],
        "passed": False,
        "passing_score": 70.0,
        "phoneme_score": 55.0,
        "fluency_score": 0.6,
    }


# Patch targets — all calls go through the service's own namespace
_SVC = "app.services.pronunciation_service"


# ===========================================================================
# _normalise_cefr()
# ===========================================================================

class TestNormaliseCefr:

    @pytest.fixture(autouse=True)
    def _import(self):
        from app.services.pronunciation_service import _normalise_cefr
        self.fn = _normalise_cefr

    @pytest.mark.parametrize("level", ["A1", "A2", "B1", "B2", "C1", "C2"])
    def test_valid_levels_pass_through(self, level):
        assert self.fn(level) == level

    @pytest.mark.parametrize("level", ["a1", "a2", "b1", "b2", "c1", "c2"])
    def test_lowercase_normalised(self, level):
        assert self.fn(level) == level.upper()

    def test_invalid_falls_back_to_b1(self):
        assert self.fn("Z9") == "B1"

    def test_empty_falls_back_to_b1(self):
        assert self.fn("") == "B1"

    def test_whitespace_stripped(self):
        assert self.fn("  B2  ") == "B2"

    def test_random_string_falls_back_to_b1(self):
        assert self.fn("BEGINNER") == "B1"


# ===========================================================================
# _build_word_breakdown()
# ===========================================================================

class TestBuildWordBreakdown:

    @pytest.fixture(autouse=True)
    def _import(self):
        from app.services.pronunciation_service import _build_word_breakdown
        self.fn = _build_word_breakdown

    def test_returns_list(self):
        assert isinstance(self.fn([], [], "hello world"), list)

    def test_length_matches_word_count(self):
        assert len(self.fn([], [], "hello world foo")) == 3

    def test_correct_word_score_is_one(self):
        assert self.fn([], [], "hello")[0].score == 1.0

    def test_correct_word_marked_correct(self):
        assert self.fn([], [], "hello")[0].correct is True

    def test_correct_word_empty_actual_phoneme(self):
        assert self.fn([], [], "hello")[0].actual_phoneme == ""

    def test_wrong_word_score_is_0_3(self):
        mistakes = [{"type": "wrong", "expected": "hello", "spoken": "helo"}]
        result = self.fn(mistakes, [], "hello world")
        hello = next(w for w in result if w.word == "hello")
        assert hello.score == 0.3

    def test_wrong_word_marked_incorrect(self):
        mistakes = [{"type": "wrong", "expected": "hello", "spoken": "helo"}]
        result = self.fn(mistakes, [], "hello world")
        assert next(w for w in result if w.word == "hello").correct is False

    def test_missing_word_score_is_zero(self):
        mistakes = [{"type": "missing", "expected": "world", "spoken": ""}]
        result = self.fn(mistakes, [], "hello world")
        assert next(w for w in result if w.word == "world").score == 0.0

    def test_missing_word_marked_incorrect(self):
        mistakes = [{"type": "missing", "expected": "world", "spoken": ""}]
        result = self.fn(mistakes, [], "hello world")
        assert next(w for w in result if w.word == "world").correct is False

    def test_actual_phoneme_from_mistake(self):
        mistakes = [{"type": "wrong", "expected": "hello", "spoken": "helo"}]
        assert self.fn(mistakes, [], "hello")[0].actual_phoneme == "helo"

    def test_expected_phoneme_from_weak_phonemes(self):
        mistakes = [{"type": "wrong", "expected": "hello", "spoken": "helo"}]
        weak = [{"word": "hello", "phoneme": "/h/"}]
        assert self.fn(mistakes, weak, "hello")[0].expected_phoneme == "/h/"

    def test_phoneme_map_is_per_word(self):
        mistakes = [
            {"type": "wrong", "expected": "hello", "spoken": "helo"},
            {"type": "wrong", "expected": "world", "spoken": "worl"},
        ]
        weak = [
            {"word": "hello", "phoneme": "/h/"},
            {"word": "world", "phoneme": "/w/"},
        ]
        result = self.fn(mistakes, weak, "hello world")
        assert next(w for w in result if w.word == "hello").expected_phoneme == "/h/"
        assert next(w for w in result if w.word == "world").expected_phoneme == "/w/"

    def test_word_order_matches_reference(self):
        result = self.fn([], [], "the quick brown fox")
        assert [w.word for w in result] == ["the", "quick", "brown", "fox"]

    def test_case_insensitive_matching(self):
        mistakes = [{"type": "wrong", "expected": "Hello", "spoken": "helo"}]
        result = self.fn(mistakes, [], "Hello World")
        assert next(w for w in result if w.word == "hello").correct is False

    def test_empty_reference_returns_empty(self):
        assert self.fn([], [], "") == []

    def test_word_score_fields_present(self):
        w = self.fn([], [], "hello")[0]
        for field in ("word", "expected_phoneme", "actual_phoneme", "score", "correct"):
            assert hasattr(w, field)


# ===========================================================================
# score_with_reference() — async pipeline
# ===========================================================================

class TestScoreWithReference:

    async def _call(self, ref: str = "hello world", scores: dict | None = None, transcript: str = "hello world"):
        from app.services.pronunciation_service import score_with_reference

        wav = _make_wav_path()
        model = MagicMock()

        with (
            patch(f"{_SVC}.convert_to_wav", return_value=wav),
            patch(f"{_SVC}.check_duration"),
            patch(f"{_SVC}.transcribe_audio", return_value=(transcript, 0.9)),
            patch(f"{_SVC}.compute_pronunciation_scores", return_value=scores or _mock_scores()),
        ):
            result = await score_with_reference(wav, "wav", ref, model)

        wav.unlink(missing_ok=True)
        return result

    async def test_returns_pronunciation_score_result(self):
        from app.schema.pronunciation_schema import PronunciationScoreResult
        assert isinstance(await self._call(), PronunciationScoreResult)

    async def test_overall_score_in_0_1(self):
        result = await self._call(scores=_mock_scores(overall=85.0))
        assert 0.0 <= result.overall_score <= 1.0

    async def test_overall_score_normalised_from_100(self):
        result = await self._call(scores=_mock_scores(overall=80.0))
        assert result.overall_score == pytest.approx(0.8, abs=0.01)

    async def test_transcript_in_result(self):
        result = await self._call(transcript="hello world")
        assert result.transcript == "hello world"

    async def test_mispronounced_words_from_breakdown(self):
        result = await self._call(
            ref="hello world",
            scores=_mock_scores_with_mistakes(),
            transcript="hello world",
        )
        assert "hello" in result.mispronounced_words or "world" in result.mispronounced_words

    async def test_empty_transcript_raises(self):
        from app.services.pronunciation_service import score_with_reference
        wav = _make_wav_path()
        model = MagicMock()
        with (
            patch(f"{_SVC}.convert_to_wav", return_value=wav),
            patch(f"{_SVC}.check_duration"),
            patch(f"{_SVC}.transcribe_audio", return_value=("", 0.0)),
        ):
            with pytest.raises(ValueError, match="empty or invalid"):
                await score_with_reference(wav, "wav", "hello world", model)
        wav.unlink(missing_ok=True)

    async def test_none_scores_raises(self):
        from app.services.pronunciation_service import score_with_reference
        wav = _make_wav_path()
        model = MagicMock()
        with (
            patch(f"{_SVC}.convert_to_wav", return_value=wav),
            patch(f"{_SVC}.check_duration"),
            patch(f"{_SVC}.transcribe_audio", return_value=("hello", 0.9)),
            patch(f"{_SVC}.compute_pronunciation_scores", return_value=None),
        ):
            with pytest.raises(ValueError, match="no results"):
                await score_with_reference(wav, "wav", "hello world", model)
        wav.unlink(missing_ok=True)

    async def test_missing_keys_raises(self):
        from app.services.pronunciation_service import score_with_reference
        wav = _make_wav_path()
        model = MagicMock()
        with (
            patch(f"{_SVC}.convert_to_wav", return_value=wav),
            patch(f"{_SVC}.check_duration"),
            patch(f"{_SVC}.transcribe_audio", return_value=("hello", 0.9)),
            patch(f"{_SVC}.compute_pronunciation_scores", return_value={"overall_score": 80.0}),
        ):
            with pytest.raises(ValueError, match="missing keys"):
                await score_with_reference(wav, "wav", "hello world", model)
        wav.unlink(missing_ok=True)

    async def test_cefr_normalised_before_scoring(self):
        from app.services.pronunciation_service import score_with_reference
        wav = _make_wav_path()
        model = MagicMock()
        captured = {}

        def capture(ref, transcript, cefr):
            captured["cefr"] = cefr
            return _mock_scores()

        with (
            patch(f"{_SVC}.convert_to_wav", return_value=wav),
            patch(f"{_SVC}.check_duration"),
            patch(f"{_SVC}.transcribe_audio", return_value=("hello", 0.9)),
            patch(f"{_SVC}.compute_pronunciation_scores", side_effect=capture),
        ):
            await score_with_reference(wav, "wav", "hello", model, cefr_level="b2")

        assert captured["cefr"] == "B2"
        wav.unlink(missing_ok=True)

    async def test_invalid_cefr_defaults_to_b1(self):
        from app.services.pronunciation_service import score_with_reference
        wav = _make_wav_path()
        model = MagicMock()
        captured = {}

        def capture(ref, transcript, cefr):
            captured["cefr"] = cefr
            return _mock_scores()

        with (
            patch(f"{_SVC}.convert_to_wav", return_value=wav),
            patch(f"{_SVC}.check_duration"),
            patch(f"{_SVC}.transcribe_audio", return_value=("hello", 0.9)),
            patch(f"{_SVC}.compute_pronunciation_scores", side_effect=capture),
        ):
            await score_with_reference(wav, "wav", "hello", model, cefr_level="Z9")

        assert captured["cefr"] == "B1"
        wav.unlink(missing_ok=True)