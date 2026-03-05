from pydub import AudioSegment
from pathlib import Path
from difflib import SequenceMatcher
import epitran
from langdetect import detect
import re
from num2words import num2words

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


# ---------- Convert Sentence → Phonemes ----------
def sentence_to_phonemes(text, epi):

    words = [normalize_word(w) for w in text.split()]
    words = [w for w in words if w]

    phonemes = []

    for word in words:
        phonemes.extend(word_to_phonemes(word, epi))

    return phonemes, words


# ---------- Pronunciation Tips ----------
phoneme_tips = {
    "θ": "Place your tongue between your teeth to produce the 'th' sound.",
    "ð": "Voice the 'th' sound like in 'this'.",
    "r": "Curl the tongue slightly backward when pronouncing 'r'.",
    "l": "Touch the tongue tip to the ridge behind your upper teeth.",
    "v": "Touch lower lip to upper teeth and vibrate.",
    "f": "Blow air between lower lip and upper teeth.",
}


# ---------- Main Comparison ----------
def compare_phonemes(reference: str, transcript: str):

    try:
        lang = detect(reference)
        lang_code = "eng-Latn" if lang.startswith("en") else "eng-Latn"
    except:
        lang_code = "eng-Latn"

    epi = get_epi(lang_code)

    ref_ph, ref_words = sentence_to_phonemes(reference, epi)
    sp_ph, sp_words = sentence_to_phonemes(transcript, epi)

    matcher = SequenceMatcher(None, ref_ph, sp_ph)

    mistakes = []
    wrong_phonemes = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == "equal":
            continue

        ref_segment = ref_ph[i1:i2]
        sp_segment = sp_ph[j1:j2]

        mistakes.append({
            "type": tag,
            "reference_phonemes": ref_segment,
            "spoken_phonemes": sp_segment,
            "position": i1
        })

        wrong_phonemes += len(ref_segment)

    total = len(ref_ph)

    if total > 0:
        score = max(0, int((1 - wrong_phonemes / total) * 100))
    else:
        score = 0


    # ---------- Generate Tips ----------
    tips = []

    for m in mistakes:

        for phoneme in m["reference_phonemes"]:

            if phoneme in phoneme_tips:
                tips.append(phoneme_tips[phoneme])
                break

        else:
            tips.append(
                f"Focus on pronouncing phoneme(s): {' '.join(m['reference_phonemes'])}"
            )


    return score, mistakes, tips