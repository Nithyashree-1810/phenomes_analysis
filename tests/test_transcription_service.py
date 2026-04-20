import numpy as np
import pytest

from app.services.transcription_service import (
    SilentAudioError,
    is_silent_audio,
    transcribe_audio,
)


class DummyWhisperModel:
    device = "cpu"

    def detect_language(self, mel):
        return None, {"en": 0.99}

    def transcribe(self, file_path, language, fp16):
        return {"text": "hello"}


def test_is_silent_audio_detects_all_zero_audio():
    audio = np.zeros(16000, dtype=np.float32)
    assert is_silent_audio(audio)


def test_is_silent_audio_detects_low_amplitude_audio():
    audio = np.array([0.0, 0.0, 0.0005, -0.0005], dtype=np.float32)
    assert is_silent_audio(audio)


def test_transcribe_audio_raises_silent_audio_when_audio_is_near_silent(monkeypatch, tmp_path):
    wav_path = tmp_path / "silent.wav"
    wav_path.write_bytes(b"\x00")

    monkeypatch.setattr(
        "app.services.transcription_service.sf.info",
        lambda file_path: type("Info", (), {"duration": 2.0})(),
    )
    monkeypatch.setattr(
        "app.services.transcription_service.whisper.load_audio",
        lambda file_path: np.zeros(16000, dtype=np.float32),
    )
    monkeypatch.setattr(
        "app.services.transcription_service.whisper.pad_or_trim",
        lambda audio: audio,
    )
    monkeypatch.setattr(
        "app.services.transcription_service.whisper.log_mel_spectrogram",
        lambda audio: np.zeros((1, 1), dtype=np.float32),
    )

    model = DummyWhisperModel()

    with pytest.raises(SilentAudioError):
        transcribe_audio(wav_path, model)
