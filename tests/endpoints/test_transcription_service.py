from __future__ import annotations

import io
import math
import struct
import tempfile
import wave
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# WAV helpers
# ---------------------------------------------------------------------------

def _make_wav(duration_s: float = 2.0, sample_rate: int = 16000) -> Path:
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


def _make_short_wav() -> Path:
    return _make_wav(duration_s=0.3)


def _mock_model(text: str = "hello world", lang: str = "en") -> MagicMock:
    m = MagicMock()
    m.transcribe.return_value = {
        "text": text,
        "language": lang,
        "segments": [
            {"avg_logprob": -0.3, "tokens": [{"probability": 0.9}]},
            {"avg_logprob": -0.2, "tokens": [{"probability": 0.85}]},
        ],
    }
    return m


# ===========================================================================
# get_confidence()
# ===========================================================================

class TestGetConfidence:

    @pytest.fixture(autouse=True)
    def _import(self):
        from app.services.transcription_service import get_confidence
        self.fn = get_confidence

    def test_returns_float(self):
        assert isinstance(self.fn({"segments": [{"avg_logprob": -0.3}]}), float)

    def test_value_in_range(self):
        c = self.fn({"segments": [{"avg_logprob": -0.3}, {"avg_logprob": -0.5}]})
        assert 0.0 <= c <= 1.0

    def test_logprob_correctness(self):
        expected = round(math.exp(-0.4), 3)
        c = self.fn({"segments": [{"avg_logprob": -0.4}, {"avg_logprob": -0.4}]})
        assert c == expected

    def test_empty_segments_returns_zero(self):
        assert self.fn({"segments": []}) == 0.0

    def test_missing_segments_key_returns_zero(self):
        assert self.fn({}) == 0.0

    def test_none_input_returns_zero(self):
        assert self.fn(None) == 0.0

    def test_token_fallback_when_no_logprob(self):
        result = {
            "segments": [
                {"tokens": [{"probability": 0.8}, {"probability": 0.6}]},
                {"tokens": [{"probability": 0.9}]},
            ]
        }
        assert self.fn(result) == round((0.8 + 0.6 + 0.9) / 3, 3)

    def test_very_low_logprob_clamped_to_zero(self):
        assert self.fn({"segments": [{"avg_logprob": -100.0}]}) >= 0.0

    def test_zero_logprob_returns_one(self):
        assert self.fn({"segments": [{"avg_logprob": 0.0}]}) == 1.0

    def test_rounded_to_three_decimals(self):
        c = self.fn({"segments": [{"avg_logprob": -0.123456}]})
        assert c == round(c, 3)


# ===========================================================================
# check_duration()
# ===========================================================================

class TestCheckDuration:

    @pytest.fixture(autouse=True)
    def _import(self):
        from app.services.transcription_service import (
            AudioTooShortError,
            check_duration,
        )
        self.fn = check_duration
        self.AudioTooShortError = AudioTooShortError

    def test_valid_duration_does_not_raise(self):
        wav = _make_wav(2.0)
        try:
            self.fn(wav)
        finally:
            wav.unlink(missing_ok=True)

    def test_short_audio_raises(self):
        wav = _make_short_wav()
        try:
            with pytest.raises(self.AudioTooShortError):
                self.fn(wav)
        finally:
            wav.unlink(missing_ok=True)

    def test_error_code(self):
        wav = _make_short_wav()
        try:
            with pytest.raises(self.AudioTooShortError) as exc:
                self.fn(wav)
            assert exc.value.code == "AUDIO_TOO_SHORT"
        finally:
            wav.unlink(missing_ok=True)

    def test_accepts_string_path(self):
        wav = _make_wav(2.0)
        try:
            self.fn(str(wav))
        finally:
            wav.unlink(missing_ok=True)

    def test_accepts_path_object(self):
        wav = _make_wav(2.0)
        try:
            self.fn(Path(wav))
        finally:
            wav.unlink(missing_ok=True)


# ===========================================================================
# transcribe_audio()
# ===========================================================================

class TestTranscribeAudio:

    @pytest.fixture(autouse=True)
    def _import(self):
        from app.services.transcription_service import (
            AudioTooShortError,
            SilentAudioError,
            UnsupportedLanguageError,
            transcribe_audio,
        )
        self.fn = transcribe_audio
        self.SilentAudioError = SilentAudioError
        self.AudioTooShortError = AudioTooShortError
        self.UnsupportedLanguageError = UnsupportedLanguageError

    def test_returns_tuple_of_str_and_float(self):
        wav = _make_wav()
        try:
            result = self.fn(wav, _mock_model("hello world"))
            assert isinstance(result, tuple) and len(result) == 2
            assert isinstance(result[0], str)
            assert isinstance(result[1], float)
        finally:
            wav.unlink(missing_ok=True)

    def test_transcript_content(self):
        wav = _make_wav()
        try:
            transcript, _ = self.fn(wav, _mock_model("hello world"))
            assert transcript == "hello world"
        finally:
            wav.unlink(missing_ok=True)

    def test_confidence_in_range(self):
        wav = _make_wav()
        try:
            _, confidence = self.fn(wav, _mock_model("hello"))
            assert 0.0 <= confidence <= 1.0
        finally:
            wav.unlink(missing_ok=True)

    def test_silent_audio_raises(self):
        wav = _make_wav()
        try:
            with pytest.raises(self.SilentAudioError):
                self.fn(wav, _mock_model(text=""))
        finally:
            wav.unlink(missing_ok=True)

    def test_silent_error_code(self):
        wav = _make_wav()
        try:
            with pytest.raises(self.SilentAudioError) as exc:
                self.fn(wav, _mock_model(text=""))
            assert exc.value.code == "SILENT_AUDIO"
        finally:
            wav.unlink(missing_ok=True)

    def test_whitespace_only_raises_silent(self):
        wav = _make_wav()
        try:
            with pytest.raises(self.SilentAudioError):
                self.fn(wav, _mock_model(text="   "))
        finally:
            wav.unlink(missing_ok=True)

    def test_non_english_raises(self):
        wav = _make_wav()
        try:
            with pytest.raises(self.UnsupportedLanguageError):
                self.fn(wav, _mock_model(text="bonjour", lang="fr"))
        finally:
            wav.unlink(missing_ok=True)

    def test_unsupported_language_code_and_detail(self):
        wav = _make_wav()
        try:
            with pytest.raises(self.UnsupportedLanguageError) as exc:
                self.fn(wav, _mock_model(text="bonjour", lang="fr"))
            assert exc.value.code == "UNSUPPORTED_LANGUAGE"
            assert "fr" in exc.value.detail
        finally:
            wav.unlink(missing_ok=True)

    def test_newlines_stripped(self):
        wav = _make_wav()
        try:
            transcript, _ = self.fn(wav, _mock_model("hello\nworld"))
            assert "\n" not in transcript
        finally:
            wav.unlink(missing_ok=True)

    def test_double_spaces_collapsed(self):
        wav = _make_wav()
        try:
            transcript, _ = self.fn(wav, _mock_model("hello  world"))
            assert "  " not in transcript
        finally:
            wav.unlink(missing_ok=True)

    def test_model_called_with_english(self):
        wav = _make_wav()
        model = _mock_model("hello")
        try:
            self.fn(wav, model)
            _, kwargs = model.transcribe.call_args
            assert kwargs.get("language") == "en"
        finally:
            wav.unlink(missing_ok=True)