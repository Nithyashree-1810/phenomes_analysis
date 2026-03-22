# app/services/question_service.py
import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI
from app.prompts.pronounciation_prompt import PRONUNCIATION_PROMPT_TEMPLATE

# ---------------------------
# Load environment and initialize OpenAI
# ---------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def safe_print(text: str):
    """Print text safely in Windows console."""
    print(text.encode("utf-8", errors="replace").decode("utf-8"))

def score_to_difficulty(score: float) -> str:
    """Map normalized score 0-100 to difficulty string"""
    if score < 40:
        return "easy"
    elif score <= 70:
        return "medium"
    else:
        return "hard"

def generate_pronunciation_question(score: float, num_questions: int = 1) -> list:
    """
    Generate pronunciation questions dynamically using OpenAI based on score.
    Returns a list of dicts: [{"difficulty": "...", "question": "..."}]
    """
    difficulty = score_to_difficulty(score)
    prompt = PRONUNCIATION_PROMPT_TEMPLATE.format(
        difficulty=difficulty,
        num_questions=num_questions
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()
        safe_print(f"RAW MODEL OUTPUT: {repr(content)}")

        # Extract JSON safely even if model adds extra text
        match = re.search(r"\[.*\]", content, re.DOTALL)
        if match:
            try:
                questions = json.loads(match.group())
            except Exception as e:
                safe_print(f"JSON parse failed: {e}. Using fallback.")
                questions = [{"difficulty": difficulty,
                              "question": "Please repeat: 'The sun is bright today.'"}]
        else:
            safe_print("WARNING: No JSON found in model output. Using fallback.")
            questions = [{"difficulty": difficulty,
                          "question": "Please repeat: 'The sun is bright today.'"}]

        # Ensure difficulty is set
        for q in questions:
            q["difficulty"] = difficulty

        return questions

    except Exception as e:
        safe_print(f"OpenAI question generation error: {e}")
        return [{"difficulty": difficulty,
                 "question": "Please repeat: 'The sun is bright today.'"}]