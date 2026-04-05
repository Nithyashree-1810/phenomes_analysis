<<<<<<< HEAD

import json
import logging
import re
import subprocess
import difflib
from typing import Any

from langchain_core.messages import HumanMessage
from app.services.llm_client import get_chat_llm

logger = logging.getLogger(__name__)

# ── Valid IPA phoneme set ────────────────────────────────────────────────────
VALID_IPA: set[str] = {
    "p", "b", "t", "d", "k", "g",
    "f", "v", "θ", "ð", "s", "z", "ʃ", "ʒ", "h",
    "m", "n", "ŋ",
    "l", "r", "j", "w",
    "i", "ɪ", "e", "ɛ", "æ", "ɑ", "ɔ",
    "oʊ", "u", "ʊ", "ə", "ʌ",
    "aɪ", "aʊ", "ɔɪ",
    "tʃ", "dʒ",
    "ɾ",
}

_DIGRAPHS: list[str] = sorted(
    [ph for ph in VALID_IPA if len(ph) > 1],
    key=len,
    reverse=True,
)


# ── IPA utilities ────────────────────────────────────────────────────────────

def split_ipa(ipa: str) -> list[str]:
    """
    Tokenise an IPA string into a list of phoneme tokens.
    Multi-character digraphs are kept together (e.g. 'tʃ', 'aɪ').
    Stress markers and spaces are dropped.
    """
    tokens: list[str] = []
    i = 0
    while i < len(ipa):
        matched = False
        for dg in _DIGRAPHS:
            if ipa[i:i + len(dg)] == dg:
                tokens.append(dg)
                i += len(dg)
                matched = True
                break
        if not matched:
            ch = ipa[i]
            if ch not in ("ˈ", "ˌ", " "):
                tokens.append(ch)
=======
import json
import re
from app.services.client import client

# ============================================================
# VALID IPA SET
# ============================================================
VALID_IPA = {
    "p","b","t","d","k","g","f","v","θ","ð","s","z","ʃ","ʒ","h",
    "m","n","ŋ","l","r","j","w",
    "i","ɪ","e","ɛ","æ","ɑ","ɔ","oʊ","u","ʊ","ə","ʌ","aɪ","aʊ","ɔɪ",
    "tʃ","dʒ","ɾ"
}

# ============================================================
# CLEANER FOR PHONEME DETAILS
# ============================================================
def clean_phonemes(phoneme_details):
    """
    Removes invalid IPA symbols (ˈ, ˌ, spaces, unknown tokens).
    Ensures DB gets only valid phonemes.
    """
    cleaned = []

    for item in phoneme_details:
        ph = item.get("phoneme", "").strip()

        if not ph:
            continue

        if ph in ("ˈ", "ˌ"):
            continue

        if ph == " ":
            continue

        if ph not in VALID_IPA:
            continue

        cleaned.append(item)

    return cleaned


# -------------------------------
# IPA helpers
# -------------------------------
def gpt_extract_ipa(text: str) -> str:
    prompt = f"""
Convert the following English text to IPA only.
Rules:
- Output ONLY IPA.
- No brackets or slashes.
- No explanation.
TEXT:
{text}
"""
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.0
        )
        ipa = res.choices[0].message.content.strip()
        ipa = re.sub(r"[/\[\]]", "", ipa)
        return ipa
    except:
        return ""


def normalize_ipa(ipa: str) -> str:
    if not ipa:
        return ""
    ipa = ipa.lower()
    ipa = re.sub(r"[^a-zɑ-ɒɔəɜɪʊʌæθðŋʃʒɹɾʔːˑˈˌ ]+", "", ipa)
    return ipa


def split_ipa(ipa: str):
    digraphs = ["tʃ", "dʒ", "aɪ", "ɔɪ", "eɪ", "oʊ"]
    tokens = []
    i = 0
    while i < len(ipa):
        if i + 1 < len(ipa) and ipa[i:i+2] in digraphs:
            tokens.append(ipa[i:i+2])
            i += 2
        else:
            tokens.append(ipa[i])
>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f
            i += 1
    return tokens


<<<<<<< HEAD
def normalize_ipa(ipa: str) -> str:
    """Lowercase and strip bracketing characters."""
    if not ipa:
        return ""
    ipa = ipa.lower()
    ipa = re.sub(r"[/\[\]]", "", ipa)
    return ipa.strip()


def levenshtein_tokens(a: list[str], b: list[str]) -> int:
    """
    Standard Levenshtein edit distance on token lists.
    Correctly handles multi-char IPA digraphs.
    """
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for tok_a in a:
        curr = [prev[0] + 1]
        for j, tok_b in enumerate(b, 1):
            cost = 0 if tok_a == tok_b else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
=======
def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j-1] + 1, prev[j-1] + cost))
>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f
        prev = curr
    return prev[-1]


<<<<<<< HEAD
def clean_phonemes(phoneme_details: list[dict]) -> list[dict]:
    """Remove entries whose 'phoneme' key is not in VALID_IPA."""
    return [
        item for item in phoneme_details
        if item.get("phoneme") in VALID_IPA
    ]


# ── Fluency scoring ──────────────────────────────────────────────────────────

_DISFLUENCY_MARKERS = ("um", "uh", "erm", "like", "...", "--")


def compute_fluency(transcript: str) -> float:
    """
    Simple disfluency-based fluency score in [0, 1].
    Each disfluency marker subtracts 0.1 (capped at 0.5 total penalty).
    """
    if not transcript:
        return 0.0
    lower = transcript.lower()
    penalties = sum(lower.count(m) for m in _DISFLUENCY_MARKERS)
    score = max(0.5, 1.0 - penalties * 0.1)
    return round(score, 3)


# ── IPA Extraction (espeak-ng + epitran fallback, zero LLM cost) ─────────────

def _ipa_via_espeak(text: str) -> str:
    """
    Use espeak-ng subprocess to convert text → IPA.
    Returns empty string if espeak-ng is not installed or fails.

    Install: sudo apt-get install espeak-ng   (Linux)
             brew install espeak-ng            (macOS)
    """
    try:
        result = subprocess.run(
            ["espeak-ng", "-q", "--ipa", "-v", "en-us", text],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # espeak-ng outputs one IPA line per input line; join them
            ipa = " ".join(result.stdout.strip().splitlines())
            return ipa.strip()
    except FileNotFoundError:
        logger.warning("espeak-ng not found, falling back to epitran.")
    except subprocess.TimeoutExpired:
        logger.warning("espeak-ng timed out for input: %s", text[:50])
    except Exception as exc:
        logger.error("espeak-ng error: %s", exc)
    return ""


def _ipa_via_epitran(text: str) -> str:
    """
    Use epitran as fallback IPA converter.
    Returns empty string if epitran is not installed or fails.

    Install: pip install epitran
    """
    try:
        import epitran  # lazy import — optional dependency
        epi = epitran.Epitran("eng-Latn")
        return epi.transliterate(text).strip()
    except ImportError:
        logger.warning("epitran not installed. pip install epitran to enable fallback.")
    except Exception as exc:
        logger.error("epitran error: %s", exc)
    return ""


def extract_ipa(text: str) -> str:
    """
    Public IPA extraction entry point.
    Priority: espeak-ng → epitran → empty string.
    No LLM used.
    """
    if not text:
        return ""

    ipa = _ipa_via_espeak(text)
    if ipa:
        return ipa

    ipa = _ipa_via_epitran(text)
    if ipa:
        return ipa

    logger.error(
        "Both espeak-ng and epitran failed for text: %s. "
        "Install espeak-ng (recommended) or epitran.",
        text[:80],
    )
    return ""


# ── Mistake extraction (difflib, zero LLM cost) ──────────────────────────────

def extract_mistakes(reference: str, transcript: str) -> list[dict]:
    """
    Word-level diff between reference and spoken transcript using difflib.
    Returns list of {expected, spoken, type} dicts.
    Types: 'missing' | 'wrong' | 'extra'

    Replaces the previous GPT-based gpt_extract_mistakes — same output
    schema, fully deterministic, zero API cost.
    """
    if not reference or not transcript:
        return []

    ref_words = reference.lower().split()
    spoken_words = transcript.lower().split()

    matcher = difflib.SequenceMatcher(None, ref_words, spoken_words, autojunk=False)
    mistakes: list[dict] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        elif tag == "replace":
            # Pair up words where possible; remainder treated as missing/extra
            ref_chunk = ref_words[i1:i2]
            spk_chunk = spoken_words[j1:j2]
            for exp, spk in zip(ref_chunk, spk_chunk):
                mistakes.append({"expected": exp, "spoken": spk, "type": "wrong"})
            # Handle length mismatch within a replace block
            for exp in ref_chunk[len(spk_chunk):]:
                mistakes.append({"expected": exp, "spoken": "", "type": "missing"})
            for spk in spk_chunk[len(ref_chunk):]:
                mistakes.append({"expected": "", "spoken": spk, "type": "extra"})

        elif tag == "delete":
            for exp in ref_words[i1:i2]:
                mistakes.append({"expected": exp, "spoken": "", "type": "missing"})

        elif tag == "insert":
            for spk in spoken_words[j1:j2]:
                mistakes.append({"expected": "", "spoken": spk, "type": "extra"})

    return mistakes


# ── Tip generation (GPT-4o-mini, ~240 tokens/call) ───────────────────────────

def gpt_generate_tips(
    reference_text: str,
    transcript: str,
    mistakes: list[dict],
) -> list[str]:
    """
    Generate 2-3 actionable pronunciation tips via GPT-4o-mini.
    This is the only remaining LLM call (~120-160 input + ~60-80 output tokens).
    """
    if not mistakes:
        return ["Great job! Keep practising for fluency."]

    # Tight prompt — avoids verbose preamble to minimize tokens
    prompt = (
        f"Pronunciation mistakes:\n"
        f"Ref: {reference_text}\n"
        f"Spoken: {transcript}\n"
        f"Errors: {json.dumps(mistakes)}\n\n"
        "Give 2-3 concise actionable tips targeting these mistakes.\n"
        "Return ONLY a JSON array of strings. No explanation."
    )

    llm = get_chat_llm(temperature=0.2)
    try:
        response = llm.invoke(
            [HumanMessage(content=prompt)],
            config={"run_name": "tip_generation"},
        )
        raw = response.content.strip()
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return ["Focus on the mispronounced words and repeat slowly."]
    except Exception as exc:
        logger.error("gpt_generate_tips failed: %s", exc)
        return ["Focus on the mispronounced words and repeat slowly."]


# ── Main scoring entry point ─────────────────────────────────────────────────

def compute_pronunciation_scores(
    reference_text: str,
    transcript: str,
) -> dict[str, Any]:
    """
    Full pronunciation scoring pipeline.

    Returns a dict with keys:
        reference_text, transcript, ref_ipa, user_ipa,
        phoneme_score (0-100), fluency_score (0-1), overall_score (0-100),
        mistakes, tips,
        phoneme_details, strong_phonemes, weak_phonemes
    """
    # ── Step 1: IPA extraction (espeak-ng / epitran, no LLM) ─────────────────
    ref_ipa_raw = extract_ipa(reference_text)
    user_ipa_raw = extract_ipa(transcript)

    ref_ipa = normalize_ipa(ref_ipa_raw)
    user_ipa = normalize_ipa(user_ipa_raw)

    # ── Step 2: Phoneme-level comparison ─────────────────────────────────────
    phoneme_details: list[dict] = []
    strong_phonemes: list[dict] = []
    weak_phonemes: list[dict] = []
=======
# -------------------------------
# Fluency scoring
# -------------------------------
def compute_fluency(transcript: str) -> float:
    if not transcript:
        return 0.0
    penalties = sum(transcript.lower().count(f) for f in ["um", "uh", "erm", "like", "...", "--"])
    score = 1.0 - min(0.5, penalties * 0.1)
    return round(score, 3)


# -------------------------------
# Mistakes & tips
# -------------------------------
def gpt_extract_mistakes(reference: str, transcript: str):
    prompt = f"""
Compare the reference sentence and the spoken transcript.
REFERENCE:
{reference}
TRANSCRIPT:
{transcript}
Return ONLY a JSON array named "mistakes" with:
{{"expected":"<word>","spoken":"<word>","type":"missing|wrong|extra"}}
"""
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.0
        )
        match = re.search(r"\[.*\]", res.choices[0].message.content.strip(), re.DOTALL)
        return json.loads(match.group(0)) if match else []
    except:
        return []


def gpt_generate_tips(reference_text, transcript, mistakes):
    prompt = f"""
The user read a sentence aloud and made the following pronunciation mistakes:
REFERENCE: {reference_text}
TRANSCRIPT: {transcript}
MISTAKES: {json.dumps(mistakes, indent=2)}
Give 2-3 actionable pronunciation tips ONLY targeting these mistakes.
Return ONLY a JSON list of strings.
"""
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=120
        )
        match = re.search(r"\[.*\]", res.choices[0].message.content.strip(), re.DOTALL)
        return json.loads(match.group(0)) if match else ["Focus on the mispronounced words."]
    except:
        return ["Focus on the mispronounced words."]


# ============================================================
# MAIN PRONUNCIATION SCORING
# ============================================================
def compute_pronunciation_scores(reference_text: str, transcript: str):
    ref_ipa = normalize_ipa(gpt_extract_ipa(reference_text))
    user_ipa = normalize_ipa(gpt_extract_ipa(transcript))

    phoneme_details = []
    strong_phonemes = []
    weak_phonemes = []
>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f

    if ref_ipa and user_ipa:
        ref_tokens = split_ipa(ref_ipa)
        user_tokens = split_ipa(user_ipa)
<<<<<<< HEAD
        min_len = min(len(ref_tokens), len(user_tokens))

        for i in range(min_len):
            ref_ph = ref_tokens[i]
            user_ph = user_tokens[i]
            correct = ref_ph == user_ph
            accuracy = 100.0 if correct else 0.0

            entry = {
                "phoneme": ref_ph,
                "total_attempts": 1,
                "correct_attempts": 1 if correct else 0,
                "accuracy": accuracy,
            }
            phoneme_details.append(entry)

            if accuracy >= 70:
                strong_phonemes.append({"phoneme": ref_ph})
            elif accuracy < 50:
                weak_phonemes.append({"phoneme": ref_ph})

        # Extra reference phonemes not spoken at all
        for i in range(min_len, len(ref_tokens)):
            ref_ph = ref_tokens[i]
            entry = {
                "phoneme": ref_ph,
                "total_attempts": 1,
                "correct_attempts": 0,
                "accuracy": 0.0,
            }
            phoneme_details.append(entry)
            weak_phonemes.append({"phoneme": ref_ph})

    # ── Step 3: Filter invalid IPA ────────────────────────────────────────────
=======

        min_len = min(len(ref_tokens), len(user_tokens))

        for i in range(min_len):
            r = ref_tokens[i]
            u = user_tokens[i]

            total_attempts = 1
            correct = (r == u)
            accuracy = 100 if correct else 0

            phoneme_details.append({
                "phoneme": r,
                "total_attempts": 1,
                "correct_attempts": 1 if correct else 0,
                "accuracy": accuracy
            })

            if accuracy >= 70:
                strong_phonemes.append({"phoneme": r})
            if accuracy < 50:
                weak_phonemes.append({"phoneme": r})

    # -------------------------------
    # CLEAN INVALID PHONEMES
    # -------------------------------
>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f
    phoneme_details = clean_phonemes(phoneme_details)
    strong_phonemes = clean_phonemes(strong_phonemes)
    weak_phonemes = clean_phonemes(weak_phonemes)

<<<<<<< HEAD
    # ── Step 4: Phoneme score (token-level Levenshtein) ───────────────────────
    if not ref_ipa or not user_ipa:
        phoneme_score = 0.0
    else:
        ref_tokens_full = split_ipa(ref_ipa)
        user_tokens_full = split_ipa(user_ipa)
        dist = levenshtein_tokens(ref_tokens_full, user_tokens_full)
        max_len = max(len(ref_tokens_full), len(user_tokens_full), 1)
        phoneme_score = round(max(0.0, 1.0 - dist / max_len) * 100, 2)

    # ── Step 5: Fluency score ─────────────────────────────────────────────────
    fluency_score = compute_fluency(transcript)

    # ── Step 6: Mistakes (difflib, no LLM) ───────────────────────────────────
    mistakes = extract_mistakes(reference_text, transcript)

    # ── Step 7: Tips (GPT-4o-mini, only LLM call) ────────────────────────────
    tips = gpt_generate_tips(reference_text, transcript, mistakes)

    # ── Step 8: Overall score ─────────────────────────────────────────────────
=======
    # -------------------------------
    # SCORE CALCULATIONS
    # -------------------------------
    if not ref_ipa or not user_ipa:
        phoneme_score = 0
    else:
        dist = levenshtein(ref_ipa, user_ipa)
        max_len = max(len(ref_ipa), len(user_ipa))
        phoneme_score = round(max(1 - dist / max_len, 0) * 100)

    fluency_score = compute_fluency(transcript)
    mistakes = gpt_extract_mistakes(reference_text, transcript)
    tips = gpt_generate_tips(reference_text, transcript, mistakes) if mistakes else ["Great job!"]

>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f
    overall_score = round(phoneme_score * 0.7 + fluency_score * 100 * 0.3, 2)

    return {
        "reference_text": reference_text,
        "transcript": transcript,
        "ref_ipa": ref_ipa,
        "user_ipa": user_ipa,
        "phoneme_score": phoneme_score,
        "fluency_score": fluency_score,
        "overall_score": overall_score,
        "mistakes": mistakes,
        "tips": tips,
        "phoneme_details": phoneme_details,
        "strong_phonemes": strong_phonemes,
<<<<<<< HEAD
        "weak_phonemes": weak_phonemes,
=======
        "weak_phonemes": weak_phonemes
>>>>>>> bee88e98780f18963f2282e9f3b190f58784ae4f
    }