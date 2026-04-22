import json
import re
from app.services.client import client

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
    ipa = re.sub(r"[^a-zɑ-ɒɔəɜɪʊʌæθðŋʃʒɹɾʔːˑˈˌ]+", "", ipa)
    return ipa


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
        prev = curr
    return prev[-1]


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
# Mistake extraction and tips
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
        if match:
            return json.loads(match.group(0))
        return []
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
        if match:
            return json.loads(match.group(0))
        return ["Focus on improving the mispronounced words."]
    except:
        return ["Focus on improving the mispronounced words."]


# -------------------------------
# Main scoring
# -------------------------------
