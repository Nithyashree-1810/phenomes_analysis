import re
from typing import List, Tuple


def normalize_word(word: str) -> str:
    return re.sub(r"[^a-zA-Z']+", "", word).lower()


def word_to_phonemes(word: str, epi=None) -> List[str]:
    # Placeholder: return characters as 'phonemes' for simple comparison
    return list(word)


def phoneme_similarity(ref_ph: List[str], sp_ph: List[str]) -> float:
    # Simple similarity: proportion of matching phonemes in order
    if not ref_ph:
        return 0.0
    matches = sum(1 for a, b in zip(ref_ph, sp_ph) if a == b)
    return matches / len(ref_ph)


def compare_phonemes(reference: str, transcript: str) -> Tuple[int, List[dict], List[str]]:
    """Compare reference and transcript at a word-ish level and return
    (score, mistakes, tips).

    This is a lightweight fallback implementation used when a more
    sophisticated phoneme-based comparison is not available.
    """
    if reference is None:
        reference = ""
    if transcript is None:
        transcript = ""

    ref_words = [normalize_word(w) for w in reference.split() if normalize_word(w)]
    sp_words = [normalize_word(w) for w in transcript.split() if normalize_word(w)]

    total = max(len(ref_words), 1)
    correct = 0
    mistakes = []

    for i, ref_w in enumerate(ref_words):
        sp_w = sp_words[i] if i < len(sp_words) else ""
        if ref_w == sp_w:
            correct += 1
        else:
            mistakes.append({"position": i + 1, "expected": ref_w, "observed": sp_w})

    score = round((correct / total) * 100)

    tips = []
    if mistakes:
        tips.append("Practice the mismatched words slowly and focus on articulation.")
        tips.extend([f"Repeat: '{m['expected']}'" for m in mistakes[:5]])

    return score, mistakes, tips