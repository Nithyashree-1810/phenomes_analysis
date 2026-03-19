from app.data.questions import QUESTIONS
import random

class QuestionGenerationService:

    def get_difficulty(self, score: float) -> str:
        if score < 0.20:
            return "basic"
        elif score < 0.40:
            return "easy"
        elif score < 0.60:
            return "intermediate"
        elif score < 0.80:
            return "advanced"
        return "very_difficult"

    def generate_question(self, score: float) -> dict:
        normalized = score / 100  # FIXED SCORE NORMALIZATION

        difficulty = self.get_difficulty(normalized)
        question_list = QUESTIONS[difficulty]

        question = random.choice(question_list)

        return {
            "difficulty": difficulty,
            "question": question
        }