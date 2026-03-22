# app/services/fluency_service.py
import librosa
import numpy as np
from pathlib import Path

def safe_encode(text: str) -> str:
    """Windows-safe UTF-8 encoding for logs."""
    if not text:
        return ""
    return text.encode("utf-8", errors="replace").decode("utf-8")

def compute_fluency(audio_path: str) -> float:
    """
    Computes a fluency score (0-100) based on proportion of voiced frames in audio.
    Fully Windows-safe.
    """
    try:
        audio_file = Path(audio_path)
        if not audio_file.exists():
            print(f"[ERROR] Audio file does not exist: {audio_path}")
            return 0.0

        y, sr = librosa.load(str(audio_file), sr=None)

        if len(y) < 2048:  # too short to analyze
            return 0.0

        # RMS energy per frame
        rmse = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        if len(rmse) == 0:
            return 0.0

        threshold = 0.04 * np.max(rmse)
        voiced_frames = rmse > threshold
        fluency_score = float(np.sum(voiced_frames) / len(rmse)) * 100  # scale to 0-100
        return max(0.0, min(100.0, fluency_score))

    except Exception as e:
        print(f"[ERROR] Fluency compute failed: {safe_encode(str(e))}")
        return 0.0