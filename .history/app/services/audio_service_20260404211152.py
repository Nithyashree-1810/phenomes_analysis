
import os
import logging
from pathlib import Path
from pydub import AudioSegment

logger = logging.getLogger(__name__)

_ffmpeg = os.getenv("FFMPEG_PATH")
if _ffmpeg:
    AudioSegment.converter = _ffmpeg
    logger.info("FFmpeg set from FFMPEG_PATH env var: %s", _ffmpeg)


def convert_to_wav(file_path, audio_format: str = None) -> Path:
    """
    Convert an audio file to WAV format using pydub.

    Args:
        file_path: path to input audio file (str or Path)
        audio_format: format hint e.g. "m4a", "mp3". Inferred from extension if None.

    Returns:
        Path to converted WAV file (same dir, .wav extension).
    """
    file_path = Path(file_path)

    if audio_format is None:
        audio_format = file_path.suffix.replace(".", "").lower()

    audio = AudioSegment.from_file(file_path, format=audio_format)
    wav_path = file_path.with_suffix(".wav")
    audio.export(wav_path, format="wav")
    return wav_path
