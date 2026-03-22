# app/utils/phenome_utils.py
import csv
from pathlib import Path
from difflib import SequenceMatcher
import re
from num2words import num2words
import pyphen

# ---------- Load IPA dictionary ----------
def load_ipa_dict(ipa_csv_path: str):
    """
    Loads ipa_all.csv into a dict:
    key = IPA symbol
    value = feature dictionary
    """
    ipa_dict = {}
    with open(ipa_csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ipa = row.get("ipa")
            features = {k: v for k, v in row.items() if k != "ipa"}
            ipa_dict[ipa] = features
    return ipa_dict

# ---------- Syllable Dictionary ----------
syllable_dic = pyphen.Pyphen(lang="en")

# ---------- Text Normalization ----------
def normalize_word(word: str):
    word = word.lower()
    if word.isdigit():
        word = num2words(int(word))
    elif re.match(r"\d+(st|nd|rd|th)", word):
        number = int(re.match(r"(\d+)", word).group(1))
        word = num2words(number, ordinal=True)
    word = re.sub(r"[^a-zA-Z]", "", word)
    return word

# ---------- Convert Word → Phonemes using ipa_dict ----------
def word_to_phonemes(word: str, ipa_dict: dict):
    """
    Returns a list of phonemes for a word using ipa_dict.
    If word not found, fallback to list of letters.
    """
    phonemes = []
    for char in word:
        if char in ipa_dict:
            phonemes.append(char)
        else:
            phonemes.append(char)  # fallback
    return phonemes

# ---------- Syllable extraction ----------
def get_syllables(word: str):
    try:
        return syllable_dic.inserted(word).split("-")
    except:
        return [word]

# ---------- Phoneme similarity ----------
def phoneme_similarity(ref_ph, sp_ph):
    sm = SequenceMatcher(None, ref_ph, sp_ph)
    return sm.ratio()

# ---------- Pronunciation tips ----------
phoneme_tips = {
    "θ": "Place your tongue between your teeth to produce the 'th' sound.",
    "ð": "Voice the 'th' sound like in 'this'.",
    "r": "Curl the tongue slightly backward when pronouncing 'r'.",
    "l": "Touch the tongue tip to the ridge behind your upper teeth.",
    "v": "Touch lower lip to upper teeth and vibrate.",
    "f": "Blow air between lower lip and upper teeth.",
}

def generate_tip(word, phonemes):
    syllables = get_syllables(word)
    if len(syllables) > 1:
        return f"Try pronouncing it slowly as: {' - '.join(syllables)}"
    for ph in phonemes:
        if ph in phoneme_tips:
            return phoneme_tips[ph]
    return f"Practice the pronunciation of '{word}' slowly."

# ---------- Main comparison ----------
def compare_phonemes(reference: str, transcript: str, ipa_dict: dict):
    """
    Compares reference vs transcript using IPA dictionary.
    Returns:
        phoneme_score: int 0-100
        mistakes: list of dict
        tips: list of strings
    """
    try:
        ref_words = [normalize_word(w) for w in reference.split() if normalize_word(w)]
        sp_words = [normalize_word(w) for w in transcript.split() if normalize_word(w)]

        matcher = SequenceMatcher(None, ref_words, sp_words)
        mistakes = []
        similarity_scores = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for i in range(i1, i2):
                    ref_word = ref_words[i]
                    sp_word = sp_words[i]

                    ref_ph = word_to_phonemes(ref_word, ipa_dict)
                    sp_ph = word_to_phonemes(sp_word, ipa_dict)

                    sim = phoneme_similarity(ref_ph, sp_ph)
                    similarity_scores.append(sim)

                    if sim < 0.85:
                        mistakes.append({
                            "position": i,
                            "expected_word": ref_word,
                            "spoken_word": sp_word,
                            "expected_phonemes": ref_ph,
                            "spoken_phonemes": sp_ph,
                            "phoneme_similarity": round(sim, 2),
                            "severity": "minor" if sim > 0.6 else "major",
                            "syllables": get_syllables(ref_word),
                            "tip": generate_tip(ref_word, ref_ph)
                        })
            else:
                ref_segment = ref_words[i1:i2]
                sp_segment = sp_words[j1:j2]

                for idx, ref_word in enumerate(ref_segment):
                    spoken_word = sp_segment[idx] if idx < len(sp_segment) else ""
                    ref_ph = word_to_phonemes(ref_word, ipa_dict)
                    sp_ph = word_to_phonemes(spoken_word, ipa_dict) if spoken_word else []
                    sim = phoneme_similarity(ref_ph, sp_ph)
                    similarity_scores.append(sim)

                    if sim > 0.8:
                        severity = "minor"
                    elif sim > 0.5:
                        severity = "moderate"
                    else:
                        severity = "major"

                    mistakes.append({
                        "position": i1 + idx,
                        "expected_word": ref_word,
                        "spoken_word": spoken_word,
                        "expected_phonemes": ref_ph,
                        "spoken_phonemes": sp_ph,
                        "phoneme_similarity": round(sim, 2),
                        "severity": severity,
                        "syllables": get_syllables(ref_word),
                        "tip": generate_tip(ref_word, ref_ph)
                    })

        phoneme_score = int(sum(similarity_scores)/len(similarity_scores)*100) if similarity_scores else 0
        tips = list({m["tip"] for m in mistakes})

        return phoneme_score, mistakes, tips

    except Exception as e:
        print("Phoneme comparison error:", str(e))
        return 0, [], ["Pronunciation analysis failed internally."]