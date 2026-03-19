# scoring_service.py
from app.utils import compare_phonemes
from app.services.fluency_service import compute_fluency


def analyze_pronunciation(reference_text, transcript, wav_path):

    # Word/phoneme matching score (0–100)
    raw_pron_score, mistakes, tips = compare_phonemes(
        reference_text,
        transcript
    )

    # Fluency score (returns values like 70,75,90)
    raw_fluency = compute_fluency(wav_path)

    # ----- NORMALIZATION FIX -----
    pron_norm = raw_pron_score / 100         # → 0.0 to 1.0
    fluency_norm = raw_fluency / 100         # → 0.70 to 0.90

    # Weighted score (still 0–1)
    final_norm = (pron_norm * 0.7) + (fluency_norm * 0.3)

    # Convert back to 0–100 scale
    final_score = round(final_norm * 100)

    # Safety clamp
    final_score = max(0, min(100, final_score))

    return final_score, mistakes, tips