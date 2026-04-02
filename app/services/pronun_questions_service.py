import re
import json
from app.services.client import client
from app.prompts.pronounciation_prompt import PRONUNCIATION_PROMPT_TEMPLATE

class PronunciationQuestionsService:
    """
    Generate pronunciation exercises based on score.
    """

    @staticmethod
    def score_to_difficulty(score: float) -> str:
        if score < 40:
            return "easy"
        elif score <= 70:
            return "medium"
        else:
            return "hard"

    def generate_questions(self, score: float, num_questions: int = 2):
        difficulty = self.score_to_difficulty(score)
        prompt = PRONUNCIATION_PROMPT_TEMPLATE.format(difficulty=difficulty, num_questions=num_questions)
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            content = response.choices[0].message.content.strip()
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                questions = json.loads(match.group())
            else:
                questions = [{"difficulty": difficulty, "question": "Please repeat: 'The sun is bright today.'"}]
            for q in questions:
                q["difficulty"] = difficulty
            return questions
        except:
            return [{"difficulty": difficulty, "question": "Please repeat: 'The sun is bright today.'"}]