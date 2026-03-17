from app.utils  import compare_phonemes
from app.services.fluency_service import compute_fluency


def analyze_pronunciation(reference_text, transcript, wav_path):

    score, mistakes, tips = compare_phonemes(
        reference_text,
        transcript
    )

    fluency_score = compute_fluency(wav_path)

    final_score = round((score * 0.7) + (fluency_score * 0.3))

    return final_score, mistakes, tips