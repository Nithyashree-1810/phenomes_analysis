from pydub import AudioSegment
from pathlib import Path
from difflib import SequenceMatcher
import epitran
from langdetect import detect
import re
from num2words import num2words  

# FFmpeg path for Windows
AudioSegment.converter = r"C:\Users\fidel\Desktop\FFmpeg\bin\ffmpeg.exe"

def file_to_wav(file_path: str, audio_format="m4a") -> Path:
    """
    Converts audio file to WAV format.
    """
    audio = AudioSegment.from_file(file_path, format=audio_format)
    output_path = Path(file_path).with_suffix(".wav")
    audio.export(output_path, format="wav")
    return output_path

# ----- Phoneme comparison -----
epi_map_cache = {}

def get_phonemes(text: str, lang: str = "eng-Latn") -> list:
    """
    Convert text to a phoneme list using Epitran.
    Handles numbers, ordinals, and unknown words to prevent KeyError.
    """
    if lang not in epi_map_cache:
        epi_map_cache[lang] = epitran.Epitran(lang)
    epi = epi_map_cache[lang]
    phonemes = []

    words = text.lower().split()
    processed_words = []

    for w in words:
        # Convert digits to words
        if w.isdigit():
            w = num2words(int(w))
        # Convert ordinals like 16th → sixteenth
        elif re.match(r'\d+(st|nd|rd|th)', w):
            w = num2words(int(re.match(r'(\d+)', w).group(1)), ordinal=True)
        # Keep only letters for phonemization
        w_clean = re.sub(r'[^a-zA-Z]', '', w)
        if w_clean:
            processed_words.append(w_clean)

    for word in processed_words:
        try:
            phones = epi.transliterate(word)
            phones = [p for p in phones if p]  # remove empty phonemes
            if phones:
                phonemes.extend(phones)
            else:
                # fallback: split letters if Epitran fails
                phonemes.extend(list(word))
        except KeyError:
            phonemes.extend(list(word))  # rough fallback

    return phonemes

def compare_phonemes(reference: str, transcript: str):
    """
    Compare phonemes for full passages and return score, mistakes, and improvement tips.
    """
    # Detect language; fallback to English
    try:
        lang = detect(reference)
        lang_code = "eng-Latn" if lang.startswith("en") else "eng-Latn"
    except:
        lang_code = "eng-Latn"

    # Convert text to phonemes
    ref_phones = get_phonemes(reference, lang_code)
    trans_phones = get_phonemes(transcript, lang_code)

    # Compare sequences
    sm = SequenceMatcher(None, ref_phones, trans_phones)
    mistakes = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            mistakes.append({
                "type": tag,
                "reference_phonemes": ref_phones[i1:i2],
                "spoken_phonemes": trans_phones[j1:j2],
                "position": i1
            })

    # Calculate score
    total = len(ref_phones)
    errors = sum(len(m['reference_phonemes']) for m in mistakes)
    score = max(0, int((1 - errors / total) * 100)) if total else 0

    # Generate improvement tips
    tips = [
        f"Check pronunciation of phonemes {m['reference_phonemes']} at position {m['position']}"
        for m in mistakes
    ]

    return score, mistakes, tips