# app/services/scoring_service.py
import json
import logging
import re
import subprocess
import difflib
from typing import Any

from langchain_core.messages import HumanMessage
from app.services.llm_client import get_azure_chat_llm

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


# ── CEFR config ──────────────────────────────────────────────────────────────

# For each CEFR level:
#   phoneme_weight    — how much phoneme accuracy contributes to overall score
#   fluency_weight    — how much fluency contributes
#   correct_threshold — min phoneme accuracy % to mark a phoneme as "strong"
#   passing_score     — minimum overall score to be considered passing
#   tip_focus         — natural language hint fed into the tip-generation prompt

_CEFR_CONFIG: dict[str, dict] = {
    "A1": {
        "phoneme_weight": 0.50,
        "fluency_weight": 0.50,
        "correct_threshold": 50,   # very forgiving — reward any attempt
        "passing_score": 40.0,
        "tip_focus": "basic sounds and very simple words. Keep feedback encouraging.",
    },
    "A2": {
        "phoneme_weight": 0.55,
        "fluency_weight": 0.45,
        "correct_threshold": 55,
        "passing_score": 45.0,
        "tip_focus": "common everyday sounds and short phrases.",
    },
    "B1": {
        "phoneme_weight": 0.65,
        "fluency_weight": 0.35,
        "correct_threshold": 65,
        "passing_score": 55.0,
        "tip_focus": "intermediate sounds, stress patterns, and connected speech.",
    },
    "B2": {
        "phoneme_weight": 0.70,
        "fluency_weight": 0.30,
        "correct_threshold": 70,
        "passing_score": 62.0,
        "tip_focus": "natural rhythm, linking sounds, and reduction of weak forms.",
    },
    "C1": {
        "phoneme_weight": 0.75,
        "fluency_weight": 0.25,
        "correct_threshold": 78,
        "passing_score": 70.0,
        "tip_focus": "subtle phoneme distinctions, intonation, and native-like delivery.",
    },
    "C2": {
        "phoneme_weight": 0.80,
        "fluency_weight": 0.20,
        "correct_threshold": 85,   # near-native standard
        "passing_score": 78.0,
        "tip_focus": "native-level precision, intonation contours, and stylistic variation.",
    },
}

_VALID_CEFR = frozenset(_CEFR_CONFIG.keys())


def _get_cefr_config(cefr_level: str) -> dict:
    level = cefr_level.upper().strip()
    if level not in _VALID_CEFR:
        logger.warning("Unknown CEFR level '%s', defaulting to B1.", cefr_level)
        level = "B1"
    return _CEFR_CONFIG[level]


# ── IPA utilities ────────────────────────────────────────────────────────────

def split_ipa(ipa: str) -> list[str]:
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
            i += 1
    return tokens


def normalize_ipa(ipa: str) -> str:
    if not ipa:
        return ""
    ipa = ipa.lower()
    ipa = re.sub(r"[/\[\]]", "", ipa)
    return ipa.strip()


def levenshtein_tokens(a: list[str], b: list[str]) -> int:
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
        prev = curr
    return prev[-1]


def clean_phonemes(phoneme_details: list[dict]) -> list[dict]:
    return [
        item for item in phoneme_details
        if item.get("phoneme") in VALID_IPA
    ]


# ── Fluency scoring ──────────────────────────────────────────────────────────

_DISFLUENCY_MARKERS = ("um", "uh", "erm", "like", "...", "--")


def compute_fluency(transcript: str) -> float:
    if not transcript:
        return 0.0
    lower = transcript.lower()
    penalties = sum(lower.count(m) for m in _DISFLUENCY_MARKERS)
    score = max(0.5, 1.0 - penalties * 0.1)
    return round(score, 3)


# ── IPA extraction ───────────────────────────────────────────────────────────

def _ipa_via_espeak(text: str) -> str:
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
    try:
        import epitran
        epi = epitran.Epitran("eng-Latn")
        return epi.transliterate(text).strip()
    except ImportError:
        logger.warning("epitran not installed.")
    except Exception as exc:
        logger.error("epitran error: %s", exc)
    return ""


def extract_ipa(text: str) -> str:
    if not text:
        return ""
    ipa = _ipa_via_espeak(text)
    if ipa:
        return ipa
    ipa = _ipa_via_epitran(text)
    if ipa:
        return ipa
    logger.error("Both espeak-ng and epitran failed for: %s", text[:80])
    return ""


# ── Mistake extraction ───────────────────────────────────────────────────────

def extract_mistakes(reference: str, transcript: str) -> list[dict]:
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
            ref_chunk = ref_words[i1:i2]
            spk_chunk = spoken_words[j1:j2]
            for exp, spk in zip(ref_chunk, spk_chunk):
                mistakes.append({"expected": exp, "spoken": spk, "type": "wrong"})
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


# ── CEFR-aware tip generation ────────────────────────────────────────────────

def gpt_generate_tips(
    reference_text: str,
    transcript: str,
    mistakes: list[dict],
    cefr_level: str = "B1",
) -> list[str]:
    """
    Generate 2-3 actionable tips via GPT-4o-mini, calibrated to CEFR level.
    Tips phrasing, difficulty, and focus shift with the level.
    """
    if not mistakes:
        return ["Great job! Keep practising for fluency."]

    cfg = _get_cefr_config(cefr_level)
    tip_focus = cfg["tip_focus"]

    prompt = (
        f"The learner is at CEFR level {cefr_level.upper()}.\n"
        f"Focus your feedback on: {tip_focus}\n\n"
        f"Pronunciation mistakes:\n"
        f"Reference: {reference_text}\n"
        f"Spoken:    {transcript}\n"
        f"Errors: {json.dumps(mistakes)}\n\n"
        "Give 2-3 concise actionable pronunciation tips targeting these mistakes, "
        f"pitched at a {cefr_level.upper()} learner.\n"
        "Return ONLY a JSON array of strings. No explanation."
    )

    llm = get_azure_chat_llm(temperature=0.2)
    try:
        response = llm.invoke(
            [HumanMessage(content=prompt)],
            config={"run_name": f"tip_generation_{cefr_level}"},
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
    cefr_level: str = "B1",
) -> dict[str, Any]:
    """
    Full pronunciation scoring pipeline, calibrated to CEFR level.

    Weights, thresholds, and tip focus all shift per level:
      A1/A2 — forgiving, fluency-heavy, encouraging tips
      B1/B2 — balanced, stress/rhythm focus
      C1/C2 — strict, intonation/native-like precision

    Returns a dict with keys:
        reference_text, transcript, ref_ipa, user_ipa,
        cefr_level, phoneme_score (0-100), fluency_score (0-1),
        overall_score (0-100), passing_score, passed,
        mistakes, tips,
        phoneme_details, strong_phonemes, weak_phonemes
    """
    cfg = _get_cefr_config(cefr_level)
    correct_threshold = cfg["correct_threshold"]
    phoneme_weight = cfg["phoneme_weight"]
    fluency_weight = cfg["fluency_weight"]
    passing_score = cfg["passing_score"]

    # ── Step 1: IPA extraction ────────────────────────────────────────────────
    ref_ipa_raw = extract_ipa(reference_text)
    user_ipa_raw = extract_ipa(transcript)
    ref_ipa = normalize_ipa(ref_ipa_raw)
    user_ipa = normalize_ipa(user_ipa_raw)

    # ── Step 2: Phoneme-level comparison ─────────────────────────────────────
    phoneme_details: list[dict] = []
    strong_phonemes: list[dict] = []
    weak_phonemes: list[dict] = []

    if ref_ipa and user_ipa:
        ref_tokens = split_ipa(ref_ipa)
        user_tokens = split_ipa(user_ipa)
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

            # Use CEFR-calibrated threshold for strong/weak classification
            if accuracy >= correct_threshold:
                strong_phonemes.append({"phoneme": ref_ph})
            elif accuracy < correct_threshold * 0.7:  # proportional weak cutoff
                weak_phonemes.append({"phoneme": ref_ph})

        # Extra reference phonemes not spoken at all → always weak
        for i in range(min_len, len(ref_tokens)):
            ref_ph = ref_tokens[i]
            phoneme_details.append({
                "phoneme": ref_ph,
                "total_attempts": 1,
                "correct_attempts": 0,
                "accuracy": 0.0,
            })
            weak_phonemes.append({"phoneme": ref_ph})

    # ── Step 3: Filter invalid IPA ────────────────────────────────────────────
    phoneme_details = clean_phonemes(phoneme_details)
    strong_phonemes = clean_phonemes(strong_phonemes)
    weak_phonemes = clean_phonemes(weak_phonemes)

    # ── Step 4: Phoneme score ─────────────────────────────────────────────────
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

    # ── Step 6: Mistakes ──────────────────────────────────────────────────────
    mistakes = extract_mistakes(reference_text, transcript)

    # ── Step 7: CEFR-aware tips ───────────────────────────────────────────────
    tips = gpt_generate_tips(reference_text, transcript, mistakes, cefr_level)

    # ── Step 8: Overall score (CEFR-weighted) ─────────────────────────────────
    overall_score = round(
        phoneme_score * phoneme_weight + fluency_score * 100 * fluency_weight, 2
    )
    passed = overall_score >= passing_score

    logger.info(
        "Scoring complete — cefr=%s phoneme=%.1f fluency=%.3f overall=%.1f passed=%s",
        cefr_level, phoneme_score, fluency_score, overall_score, passed,
    )

    return {
        "reference_text": reference_text,
        "transcript": transcript,
        "ref_ipa": ref_ipa,
        "user_ipa": user_ipa,
        "cefr_level": cefr_level.upper(),
        "phoneme_score": phoneme_score,
        "fluency_score": fluency_score,
        "overall_score": overall_score,
        "passing_score": passing_score,
        "passed": passed,
        "mistakes": mistakes,
        "tips": tips,
        "phoneme_details": phoneme_details,
        "strong_phonemes": strong_phonemes,
        "weak_phonemes": weak_phonemes,
    }