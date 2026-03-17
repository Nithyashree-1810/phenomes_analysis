import librosa


def compute_fluency(audio_path):

    y, sr = librosa.load(audio_path)

    duration = librosa.get_duration(y=y, sr=sr)

    speech_rate = len(y) / duration

    if speech_rate > 180:
        return 70

    if speech_rate < 80:
        return 75

    return 90