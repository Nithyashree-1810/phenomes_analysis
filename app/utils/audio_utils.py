from pydub import AudioSegment
from pathlib import Path


def file_to_wav(file_path: str, audio_format="m4a") -> Path:

    audio = AudioSegment.from_file(file_path, format=audio_format)

    output_path = Path(file_path).with_suffix(".wav")

    audio.export(output_path, format="wav")

    return output_path