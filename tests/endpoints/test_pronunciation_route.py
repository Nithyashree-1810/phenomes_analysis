# tests/endpoints/test_pronunciation_route.py
from __future__ import annotations

import io
import math
import struct
import tempfile
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# WAV helpers
# ---------------------------------------------------------------------------

def _make_wav_bytes(duration_s: float = 2.0, sample_rate: int = 16000) -> bytes:
    n_samples = int(duration_s * sample_rate)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            v = int(32767 * math.sin(2 * math.pi * 440 * i / sample_rate))
            wf.writeframes(struct.pack("<h", v))
    return buf.getvalue()


def _make_short_wav_bytes() -> bytes:
    return _make_wav_bytes(duration_s=0.3)


def _persist_wav(wav_bytes: bytes) -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(wav_bytes)
    tmp.close()
    return Path(tmp.name)


# ---------------------------------------------------------------------------
# Patch targets
# Route-level: patch at the module that imported the name (the route).
# Service-level: patch at the module that imported the name (the service).
# ---------------------------------------------------------------------------

_ROUTE = "app.routes.pronunciation_route"   # patch names imported into the route
_SVC   = "app.services.pronunciation_service"  # patch names imported into the service


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _mock_model(text: str = "hello everyone welcome you all") -> MagicMock:
    m = MagicMock()
    m.device.type = "cpu"
    m.transcribe.return_value = {
        "text": text,
        "language": "en",
        "segments": [{"avg_logprob": -0.3}, {"avg_logprob": -0.2}],
    }
    return m


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


# ---------------------------------------------------------------------------
# Client fixture
# All external I/O (ffmpeg, soundfile, Whisper) is patched out.
# Every patch target uses the module where the name was imported, not defined.
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    from app.main import app

    wav_path = _persist_wav(_make_wav_bytes())
    app.state.whisper_model = _mock_model()

    patches = [
        # ── /pronunciation/transcribe ───────────────────────────────────────
        # convert_to_wav and check_duration are imported into the route module
        patch(f"{_ROUTE}.convert_to_wav", return_value=wav_path),
        patch(f"{_ROUTE}.check_duration"),
        # transcribe_audio is also imported directly into the route — patch there
        patch(
            f"{_ROUTE}.transcribe_audio",
            return_value=("hello everyone welcome you all", 0.85),
        ),

        # ── /pronunciation/score ────────────────────────────────────────────
        # score_with_reference uses convert_to_wav + check_duration from service
        patch(f"{_SVC}.convert_to_wav", return_value=wav_path),
        patch(f"{_SVC}.check_duration"),
        # compute_pronunciation_scores is called inside the service
        patch(
            f"{_SVC}.compute_pronunciation_scores",
            return_value=_mock_scores(),
        ),
        # transcribe_audio is also imported into pronunciation_service — patch there
        patch(
            f"{_SVC}.transcribe_audio",
            return_value=("hello everyone welcome you all", 0.85),   # service expects tuple, not str
        ),
    ]

    started = [p.start() for p in patches]

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    for p in patches:
        p.stop()
    wav_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _post(client, endpoint, wav_bytes, data=None, filename="test.wav"):
    return client.post(
        endpoint,
        files={"file": (filename, io.BytesIO(wav_bytes), "audio/wav")},
        data=data or {},
    )


# ===========================================================================
# POST /pronunciation/transcribe
# ===========================================================================

class TestTranscribeRoute:

    def test_200_with_valid_wav(self, client):
        assert _post(client, "/pronunciation/transcribe", _make_wav_bytes()).status_code == 200

    def test_response_has_transcript_and_confidence(self, client):
        body = _post(client, "/pronunciation/transcribe", _make_wav_bytes()).json()
        assert "transcript" in body
        assert "confidence" in body

    def test_transcript_is_non_empty_string(self, client):
        body = _post(client, "/pronunciation/transcribe", _make_wav_bytes()).json()
        assert isinstance(body["transcript"], str) and body["transcript"]

    def test_confidence_is_float_in_range(self, client):
        body = _post(client, "/pronunciation/transcribe", _make_wav_bytes()).json()
        assert 0.0 <= body["confidence"] <= 1.0

    def test_no_extra_fields(self, client):
        body = _post(client, "/pronunciation/transcribe", _make_wav_bytes()).json()
        assert set(body.keys()) == {"transcript", "confidence"}

    def test_missing_file_returns_422(self, client):
        assert client.post("/pronunciation/transcribe").status_code == 422

    def test_silent_audio_returns_422_silent_code(self, client):
        from app.services.transcription_service import SilentAudioError
        # Override only transcribe_audio in the route for this test
        with patch(f"{_ROUTE}.transcribe_audio", side_effect=SilentAudioError()):
            resp = _post(client, "/pronunciation/transcribe", _make_wav_bytes())
        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "SILENT_AUDIO"

    def test_short_audio_returns_422_too_short_code(self, client):
        from app.services.transcription_service import AudioTooShortError
        with patch(f"{_ROUTE}.check_duration", side_effect=AudioTooShortError(0.3)):
            resp = _post(client, "/pronunciation/transcribe", _make_short_wav_bytes())
        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "AUDIO_TOO_SHORT"

    def test_unsupported_language_returns_422_correct_code(self, client):
        from app.services.transcription_service import UnsupportedLanguageError
        with patch(f"{_ROUTE}.transcribe_audio", side_effect=UnsupportedLanguageError("fr")):
            resp = _post(client, "/pronunciation/transcribe", _make_wav_bytes())
        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "UNSUPPORTED_LANGUAGE"

    def test_unexpected_error_returns_500(self, client):
        with patch(f"{_ROUTE}.transcribe_audio", side_effect=RuntimeError("disk full")):
            resp = _post(client, "/pronunciation/transcribe", _make_wav_bytes())
        assert resp.status_code == 500

    def test_m4a_filename_accepted(self, client):
        resp = _post(client, "/pronunciation/transcribe", _make_wav_bytes(), filename="rec.m4a")
        assert resp.status_code == 200

    def test_content_type_is_json(self, client):
        resp = _post(client, "/pronunciation/transcribe", _make_wav_bytes())
        assert "application/json" in resp.headers["content-type"]


# ===========================================================================
# POST /pronunciation/score
# ===========================================================================

class TestScoreRoute:

    def test_200_with_valid_input(self, client):
        resp = _post(client, "/pronunciation/score", _make_wav_bytes(),
                     data={"reference_text": "hello everyone welcome you all"})
        assert resp.status_code == 200

    def test_response_schema_fields(self, client):
        body = _post(client, "/pronunciation/score", _make_wav_bytes(),
                     data={"reference_text": "hello everyone"}).json()
        for field in ("overall_score", "word_breakdown", "mispronounced_words", "transcript"):
            assert field in body

    def test_overall_score_in_range(self, client):
        body = _post(client, "/pronunciation/score", _make_wav_bytes(),
                     data={"reference_text": "hello everyone"}).json()
        assert 0.0 <= body["overall_score"] <= 100.0

    def test_word_breakdown_length_matches_reference(self, client):
        ref = "hello everyone welcome"
        body = _post(client, "/pronunciation/score", _make_wav_bytes(),
                     data={"reference_text": ref}).json()
        assert len(body["word_breakdown"]) == len(ref.split())

    def test_word_score_fields_present(self, client):
        body = _post(client, "/pronunciation/score", _make_wav_bytes(),
                     data={"reference_text": "hello everyone"}).json()
        word = body["word_breakdown"][0]
        for f in ("word", "expected_phoneme", "actual_phoneme", "score", "correct"):
            assert f in word

    def test_each_word_score_in_range(self, client):
        body = _post(client, "/pronunciation/score", _make_wav_bytes(),
                     data={"reference_text": "hello everyone"}).json()
        for w in body["word_breakdown"]:
            assert 0.0 <= w["score"] <= 1.0

    def test_mispronounced_words_is_list(self, client):
        body = _post(client, "/pronunciation/score", _make_wav_bytes(),
                     data={"reference_text": "hello everyone"}).json()
        assert isinstance(body["mispronounced_words"], list)

    def test_mispronounced_subset_of_breakdown(self, client):
        body = _post(client, "/pronunciation/score", _make_wav_bytes(),
                     data={"reference_text": "hello everyone welcome"}).json()
        breakdown_words = {w["word"] for w in body["word_breakdown"]}
        for w in body["mispronounced_words"]:
            assert w in breakdown_words

    def test_missing_reference_text_returns_422(self, client):
        assert _post(client, "/pronunciation/score", _make_wav_bytes()).status_code == 422

    def test_missing_file_returns_422(self, client):
        resp = client.post("/pronunciation/score", data={"reference_text": "hello"})
        assert resp.status_code == 422

    @pytest.mark.parametrize("level", ["A1", "A2", "B1", "B2", "C1", "C2"])
    def test_all_cefr_levels_return_200(self, client, level):
        resp = _post(client, "/pronunciation/score", _make_wav_bytes(),
                     data={"reference_text": "hello everyone", "cefr_level": level})
        assert resp.status_code == 200, f"Failed for {level}"

    def test_invalid_cefr_falls_back_gracefully(self, client):
        resp = _post(client, "/pronunciation/score", _make_wav_bytes(),
                     data={"reference_text": "hello everyone", "cefr_level": "Z9"})
        assert resp.status_code == 200

    def test_short_audio_returns_422_too_short_code(self, client):
        from app.services.transcription_service import AudioTooShortError
        with patch(f"{_SVC}.check_duration", side_effect=AudioTooShortError(0.3)):
            resp = _post(client, "/pronunciation/score", _make_short_wav_bytes(),
                         data={"reference_text": "hello everyone"})
        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "AUDIO_TOO_SHORT"

    def test_silent_audio_returns_422_silent_code(self, client):
        from app.services.transcription_service import SilentAudioError
        with patch(f"{_SVC}.transcribe_audio", side_effect=SilentAudioError()):
            resp = _post(client, "/pronunciation/score", _make_wav_bytes(),
                         data={"reference_text": "hello everyone"})
        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "SILENT_AUDIO"

    def test_scoring_failure_returns_500(self, client):
        with patch(f"{_SVC}.compute_pronunciation_scores",
                   side_effect=RuntimeError("engine down")):
            resp = _post(client, "/pronunciation/score", _make_wav_bytes(),
                         data={"reference_text": "hello everyone"})
        assert resp.status_code == 500

    def test_transcript_in_response(self, client):
        body = _post(client, "/pronunciation/score", _make_wav_bytes(),
                     data={"reference_text": "hello everyone welcome you all"}).json()
        assert isinstance(body["transcript"], str) and body["transcript"]

    def test_content_type_is_json(self, client):
        resp = _post(client, "/pronunciation/score", _make_wav_bytes(),
                     data={"reference_text": "hello everyone"})
        assert "application/json" in resp.headers["content-type"]