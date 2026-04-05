# app/services/pronun_questions_service.py
#
# OPTIMIZATIONS vs original:
#   1. max_tokens reduced 300 → 200 (2 short questions don't need 300)
#   2. Bare except → except Exception as e + logging
#   3. No other changes needed — uses shared client correctly

import re
import json
import logging
from app.services.client import client
from app.prompts.pronounciation_prompt import PRONUNCIATION_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class PronunciationQuestionsService:
    """Generate pronunciation exercises based on user score."""

    @staticmethod
    def score_to_difficulty(score: float) -> str:
        if score < 40:
            return "easy"
        elif score <= 70:
            return "medium"
        else:
            return "hard"

    def generate_questions(self, score: float, num_questions: int = 2) -> list:
        difficulty = self.score_to_difficulty(score)
        prompt = PRONUNCIATION_PROMPT_TEMPLATE.format(
            difficulty=difficulty,
            num_questions=num_questions,
        )
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200,   # was 300; 2 short sentences fit in 200
            )
            content = response.choices[0].message.content.strip()
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                questions = json.loads(match.group())
                for q in questions:
                    q["difficulty"] = difficulty
                return questions
        except Exception as e:
            logger.error("PronunciationQuestionsService.generate_questions failed: %s", e)

        return [{"difficulty": difficulty, "question": "Please repeat: 'The sun is bright today.'"}]


# Module-level function alias used by listening_service.py
def generate_pronunciation_questions(passage: str, num_questions: int = 2) -> list:
    svc = PronunciationQuestionsService()
    return svc.generate_questions(score=50, num_questions=num_questions)
