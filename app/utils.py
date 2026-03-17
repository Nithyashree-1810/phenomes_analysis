from pydub import AudioSegment
from pathlib import Path
from difflib import SequenceMatcher
import epitran
from langdetect import detect
import re
from num2words import num2words
import pyphen

# FFmpeg path
AudioSegment.converter = r"C:\Users\fidel\Desktop\FFmpeg\bin\ffmpeg.exe"

# ---------- Audio Conversion ----------
def file_to_wav(file_path: str, audio_format="m4a") -> Path:
    audio = AudioSegment.from_file(file_path, format=audio_format)
    output_path = Path(file_path).with_suffix(".wav")
    audio.export(output_path, format="wav")
    return output_path


# ---------- Epitran Cache ----------
epi_cache = {}

def get_epi(lang="eng-Latn"):
    if lang not in epi_cache:
        epi_cache[lang] = epitran.Epitran(lang)
    return epi_cache[lang]


# ---------- Syllable Dictionary ----------
dic = pyphen.Pyphen(lang="en")


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


# ---------- Convert Word → Phonemes ----------
def word_to_phonemes(word, epi):

    try:
        phones = epi.transliterate(word)
        phones = [p for p in phones if p]

        if phones:
            return phones
        else:
            return list(word)

    except:
        return list(word)


# ---------- Syllable Extraction ----------
def get_syllables(word):

    try:
        return dic.inserted(word).split("-")
    except:
        return [word]


# ---------- Phoneme Similarity ----------
def phoneme_similarity(ref_ph, sp_ph):

    sm = SequenceMatcher(None, ref_ph, sp_ph)
    return sm.ratio()


# ---------- Pronunciation Tips ----------
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



# ---------- Main Comparison ----------

def compare_phonemes(reference: str, transcript: str):

    try:

        # Detect language (default English)
        try:
            lang = detect(reference)
            lang_code = "eng-Latn" if lang.startswith("en") else "eng-Latn"
        except:
            lang_code = "eng-Latn"

        epi = get_epi(lang_code)

        # Normalize words
        ref_words = [normalize_word(w) for w in reference.split()]
        sp_words = [normalize_word(w) for w in transcript.split()]

        ref_words = [w for w in ref_words if w]
        sp_words = [w for w in sp_words if w]

        matcher = SequenceMatcher(None, ref_words, sp_words)

        mistakes = []
        similarity_scores = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():

            # ----------------------------------------------------
            # FIXED BLOCK: Even equal words must be phoneme checked
            # ----------------------------------------------------
            if tag == "equal":

                for i in range(i1, i2):
                    ref_word = ref_words[i]
                    sp_word = sp_words[i]

                    ref_ph = word_to_phonemes(ref_word, epi)
                    sp_ph = word_to_phonemes(sp_word, epi)

                    similarity = phoneme_similarity(ref_ph, sp_ph)
                    similarity_scores.append(similarity)

                    if similarity < 0.85:  # threshold
                        mistakes.append({
                            "position": i,
                            "expected_word": ref_word,
                            "spoken_word": sp_word,
                            "expected_phonemes": ref_ph,
                            "spoken_phonemes": sp_ph,
                            "phoneme_similarity": round(similarity, 2),
                            "severity": "minor" if similarity > 0.6 else "major",
                            "syllables": get_syllables(ref_word),
                            "tip": generate_tip(ref_word, ref_ph)
                        })

            # ----------------------------------------------------
            # Non-equal → existing logic
            # ----------------------------------------------------
            else:

                ref_segment = ref_words[i1:i2]
                sp_segment = sp_words[j1:j2]

                for idx, ref_word in enumerate(ref_segment):

                    spoken_word = sp_segment[idx] if idx < len(sp_segment) else ""

                    ref_ph = word_to_phonemes(ref_word, epi)
                    sp_ph = word_to_phonemes(spoken_word, epi) if spoken_word else []

                    similarity = phoneme_similarity(ref_ph, sp_ph)
                    similarity_scores.append(similarity)

                    if similarity > 0.8:
                        severity = "minor"
                    elif similarity > 0.5:
                        severity = "moderate"
                    else:
                        severity = "major"

                    mistakes.append({
                        "position": i1 + idx,
                        "expected_word": ref_word,
                        "spoken_word": spoken_word,
                        "expected_phonemes": ref_ph,
                        "spoken_phonemes": sp_ph,
                        "phoneme_similarity": round(similarity, 2),
                        "severity": severity,
                        "syllables": get_syllables(ref_word),
                        "tip": generate_tip(ref_word, ref_ph)
                    })

        # ---------- Scoring ----------
        if similarity_scores:
            score = int(sum(similarity_scores) / len(similarity_scores) * 100)
        else:
            score = 0

        # ---------- Unique Tips ----------
        tips = list(set([m["tip"] for m in mistakes]))

        return score, mistakes, tips

    except Exception as e:

        print("Phoneme comparison error:", str(e))
        return 0, [], ["Pronunciation analysis failed internally."]
  

    # ---------- Human Tips ----------
    tips = list(set([m["tip"] for m in mistakes]))

    return score, mistakes, tips
