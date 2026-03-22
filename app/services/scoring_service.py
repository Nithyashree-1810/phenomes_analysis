# app/services/scoring_service.py
import sys
import os
from pathlib import Path
import csv

# ---------------------------
# Force UTF-8 on Windows
# ---------------------------
os.environ["PYTHONUTF8"] = "1"
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from app.utils.phenome_utlis import compare_phonemes
from app.services.fluency_service import compute_fluency

# Path to IPA CSV
IPA_CSV_PATH = Path("app/data/ipa_all.csv")  # adjust folder if needed

def safe_encode(text: str) -> str:
    """Safely encode text for Windows console/logging."""
    if not text:
        return ""
    return text.encode("utf-8", errors="replace").decode("utf-8")


def load_ipa_csv(ipa_path: Path):
    """
    Load IPA bases from CSV into a dictionary: {word: phonemes}.
    """
    ipa_dict = {}
    if not ipa_path.exists():
        print(f"[WARNING] IPA CSV not found at {ipa_path}")
        return ipa_dict

    with ipa_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row.get("ipa")
            if word:
                # Collect features as a list of phonemes
                phonemes = [row[k] for k in row if k != "ipa" and row[k]]
                ipa_dict[word] = phonemes
    return ipa_dict


# Preload IPA once
IPA_DICT = load_ipa_csv(IPA_CSV_PATH)


def score_pronunciation(reference: str, transcript: str, audio_path: str) -> dict:
    """
    Computes:
      - phoneme_score
      - fluency_score
      - mistakes
      - tips
    Uses ipa_all.csv for phoneme reference.
    """
    # ---------------------------
    # PHONEME COMPARISON
    # ---------------------------
    try:
        phoneme_score, mistakes, tips = compare_phonemes(
            reference,
            transcript,
            ipa_dict=IPA_DICT  # pass the IPA dictionary
        )
        tips = [safe_encode(t) for t in tips]
    except Exception as e:
        print(f"[ERROR] Phoneme comparison: {safe_encode(str(e))}")
        phoneme_score = 0
        mistakes = []
        tips = ["Pronunciation analysis failed internally."]

    # ---------------------------
    # FLUENCY ANALYSIS
    # ---------------------------
    try:
        fluency_score = compute_fluency(audio_path)
    except Exception as e:
        print(f"[ERROR] Fluency compute: {safe_encode(str(e))}")
        fluency_score = 0.0

    # ---------------------------
    # FINAL STRUCTURE
    # ---------------------------
    return {
        "phoneme_score": phoneme_score,
        "fluency_score": fluency_score,
        "mistakes": mistakes,
        "tips": tips
    }