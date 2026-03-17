from pydub import AudioSegment
from pathlib import Path


def convert_to_wav(file_path: Path, audio_format: str):

    audio = AudioSegment.from_file(file_path, format=audio_format)

    wav_path = file_path.with_suffix(".wav")

    audio.export(wav_path, format="wav")

    return wav_path