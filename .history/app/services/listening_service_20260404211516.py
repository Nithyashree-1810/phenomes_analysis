

import os
import uuid
import re
import json
import logging
from gtts import gTTS
from app.services.client import client  
from app.prompts.question_prompt import PROMPT_LISTENING_ONLY

logger = logging.getLogger(__name__)

STATIC_AUDIO_DIR = "app/static/audio"
os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)


def generate_passage(difficulty: str) -> str:
    """Generate a short English passage for listening practice."""
    prompt = (
        f"Generate a short {difficulty}-level English passage for listening practice. "
        "3-4 sentences. Plain prose only, no bullet points or headers."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",          # was gpt-3.5-turbo (deprecated)
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150,               # was 200; 3-4 sentences fits in 150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("generate_passage failed: %s", e)
        return "The sun is bright today. Birds sing in the trees. A gentle wind blows across the field."


def generate_questions_from_passage(passage: str, num_questions: int = 3) -> list:
    """
    Generate comprehension questions in a single OpenAI call.
    Retries once before falling back to placeholder questions.
    """
    # str.format() — safe substitution, no fragile .replace() chains
    prompt_text = PROMPT_LISTENING_ONLY.format(
        passage=passage,
        difficulty="medium",   # difficulty injected here now (was missing in original)
        num_listening=num_questions,
    )

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",      # was gpt-3.5-turbo (deprecated)
                messages=[{"role": "user", "content": prompt_text}],
                temperature=0.7,
                max_tokens=200,           # was 400; 3 short questions fit in 200
            )
            raw = response.choices[0].message.content.strip()

            # Extract JSON object containing listening_questions key
            match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                questions = parsed.get("listening_questions", [])
                for idx, q in enumerate(questions):
                    if "id" not in q:
                        q["id"] = idx + 1
                if questions:
                    return questions

        except Exception as e:
            logger.warning("generate_questions_from_passage attempt %d failed: %s", attempt + 1, e)

    # Fallback
    return [{"id": i + 1, "question": f"Question {i + 1}", "difficulty": "medium"} for i in range(num_questions)]


def generate_listening_module(difficulty: str = "medium", num_questions: int = 3) -> dict:
    """
    Generate a full listening module: passage + TTS audio + comprehension questions.
    """
    try:
        passage = generate_passage(difficulty)
        listening_questions = generate_questions_from_passage(passage, num_questions)

        audio_filename = f"listening_{uuid.uuid4().hex}.mp3"
        audio_path = os.path.join(STATIC_AUDIO_DIR, audio_filename)
        tts = gTTS(text=passage, lang="en")
        tts.save(audio_path)

        return {
            "passage": passage,
            "audio_url": f"/static/audio/{audio_filename}",
            "listening_questions": listening_questions,
        }

    except Exception as e:
        logger.error("generate_listening_module failed: %s", e)
        fallback_text = "Please repeat the sentence: The sun is bright today."
        fallback_filename = "fallback_passage.mp3"
        try:
            tts = gTTS(text=fallback_text, lang="en")
            tts.save(os.path.join(STATIC_AUDIO_DIR, fallback_filename))
        except Exception:
            pass

        return {
            "passage": fallback_text,
            "audio_url": f"/static/audio/{fallback_filename}",
            "listening_questions": [{"id": 1, "question": fallback_text, "difficulty": "easy"}],
        }


# Keep legacy name alias used by qb_agent.py
generate_questions = generate_questions_from_passage
