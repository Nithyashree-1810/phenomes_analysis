# fluency_service.py
import librosa
import numpy as np


def compute_fluency(audio_path):
    """
    Return a normalized fluency score between 0.0 and 1.0.
    Based on voiced-segment ratio.
    """

    y, sr = librosa.load(audio_path)

    # Voice activity detection using RMSE
    frame_length = 2048
    hop_length = 512

    rmse = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

    # Speech threshold (adaptive)
    threshold = 0.04 * np.max(rmse)

    voiced_frames = rmse > threshold
    voiced_ratio = np.sum(voiced_frames) / len(rmse)

    # Normalize into 0.0–1.0
    fluency_score = float(voiced_ratio)

    # clamp to safe range
    fluency_score = max(0.0, min(1.0, fluency_score))

    return fluency_score