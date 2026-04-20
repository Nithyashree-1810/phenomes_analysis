import json
import logging
import re
import uuid

from langchain_core.messages import HumanMessage

from app.services.llm_client import get_azure_chat_llm
from app.services.cefr_grading_service import CEFRGradingService
from app.services.tts_service import text_to_speech

logger = logging.getLogger(__name__)


_PASSAGE_PROMPT = (
    "Generate a short {difficulty}-level English passage for listening practice. "
    "The passage should be 3-4 sentences long, natural, and engaging. "
    "Output ONLY the passage text. No title, no explanation."
)

_QUESTIONS_PROMPT = (
    "You are an English language teacher. Given the passage below, generate "
    "{num_questions} unique multiple-choice comprehension questions.\n\n"
    "PASSAGE:\n{passage}\n\n"
    "DIFFICULTY: {difficulty}\n\n"
    "Rules:\n"
    "- Each question must focus on a different detail or idea in the passage.\n"
    "- Questions must be clear and directly answerable from the passage.\n"
    "- Each question must have exactly 4 options labeled A, B, C, D.\n"
    "- Only one option must be correct.\n"
    "- Assign each question a CEFR level (A1, A2, B1, B2, C1, C2) based on its complexity.\n"
    "- Return ONLY a JSON array in this exact format:\n"
    '  [{{"id": 1, "cefr_level": "B1", "question": "...", '
    '"options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, '
    '"correct_option": "A"}}]\n'
    "No other text."
)


def generate_listening_module(
    difficulty: str = "medium",
    num_questions: int = 3,
) -> dict:
    session_id = str(uuid.uuid4())
    try:
        passage = generate_passage(difficulty)
        questions = generate_questions_from_passage(passage, num_questions, difficulty)
        audio_filename = f"listening_{uuid.uuid4().hex}.mp3"
        audio_url = text_to_speech(passage, audio_filename)
        if not audio_url:
            audio_url = "/static/audio/fallback_passage.mp3"

        return {
            "session_id": session_id,
            "passage": passage,
            "audio_url": audio_url,
            "listening_questions": questions,
        }
    except Exception as exc:
        logger.exception("generate_listening_module failed: %s", exc)
        fallback = "Please listen carefully and answer the questions."
        return {
            "session_id": session_id,
            "passage": fallback,
            "audio_url": "/static/audio/fallback_passage.mp3",
            "listening_questions": [
                {
                    "id": 1,
                    "difficulty": difficulty,
                    "question": "What did you hear?",
                    "options": {"A": "Nothing", "B": "Music", "C": "A passage", "D": "Silence"},
                    "correct_option": "C",
                }
            ],
        }



def generate_passage(difficulty: str = "medium") -> str:
    llm = get_azure_chat_llm(temperature=0.7)
    prompt = _PASSAGE_PROMPT.format(difficulty=difficulty)
    try:
        response = llm.invoke(
            [HumanMessage(content=prompt)],
            config={"run_name": "generate_listening_passage"},
        )
        return response.content.strip()
    except Exception as exc:
        logger.error("generate_passage failed: %s", exc)
        return "The sun rises in the east and sets in the west."


def generate_questions_from_passage(
    passage: str,
    num_questions: int = 3,
    difficulty: str = "medium",
) -> list[dict]:
    llm = get_azure_chat_llm(temperature=0.5)
    prompt = _QUESTIONS_PROMPT.format(
        passage=passage,
        num_questions=num_questions,
        difficulty=difficulty,
    )
    for attempt in range(2):
        try:
            response = llm.invoke(
                [HumanMessage(content=prompt)],
                config={"run_name": "generate_listening_questions"},
            )
            raw = response.content.strip()
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                questions = json.loads(match.group(0))
                for idx, q in enumerate(questions):
                    q.setdefault("id", idx + 1)
                    q.setdefault("difficulty", difficulty)
                    # Validate MCQ structure
                    if "options" not in q or "correct_option" not in q:
                        raise ValueError(f"Question {idx + 1} missing MCQ fields")
                return questions
        except Exception as exc:
            logger.warning("generate_questions attempt %d failed: %s", attempt + 1, exc)

    # Fallback MCQ questions
    return [
        {
            "id": i + 1,
            "difficulty": difficulty,
            "question": f"Question {i + 1}.",
            "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
            "correct_option": "A",
        }
        for i in range(num_questions)
    ]



def evaluate_answers_batch(passage: str, answers: list[dict]) -> dict:
    """
    Pure logic MCQ evaluation using existing CEFRGradingService.

    Each answer dict must contain:
        {
            "question_id": 1,
            "question": "...",
            "selected_option": "B",
            "correct_option": "B",
            "cefr_level": CEFRLevel.B1,       # from the question itself
            "difficulty_score": 3              # optional, falls back to CEFR weight
        }

    Returns:
        {
            "results": [...per question...],
            "grading": {
                "cefr_level": "B1",
                "ability_score": 0.72,
                "accuracy_by_level": {"A1": 1.0, "B1": 0.5, ...}
            }
        }
    """
    results = []
    attempts = []  # fed into CEFRGradingService

    for a in answers:
        selected   = a.get("selected_option", "").strip().upper()
        correct    = a.get("correct_option", "").strip().upper()
        is_correct = selected == correct

        feedback = (
            f"Correct! The answer is {correct}."
            if is_correct
            else f"Incorrect. You selected {selected}, but the correct answer is {correct}."
        )

        results.append({
            "question_id": a["question_id"],
            "correct":     is_correct,
            "feedback":    feedback,
        })

        # Build attempt dict expected by CEFRGradingService
        attempts.append({
            "cefr_level":       a["cefr_level"],         # CEFRLevel enum value
            "is_correct":       is_correct,
            "difficulty_score": a.get("difficulty_score"),  # optional
        })

    # Use existing grading service
    grading_result = CEFRGradingService().grade(attempts)

    return {
        "results": results,
        "grading": {
            "cefr_level":       grading_result.cefr_level,
            "ability_score":    grading_result.ability_score,
            "accuracy_by_level": grading_result.accuracy_by_level,
        },
    }