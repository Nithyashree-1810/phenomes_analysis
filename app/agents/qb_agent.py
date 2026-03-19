# qb_agent.py
# Handles question generation without any LLM.
# Uses your internal hard-coded question bank + logic.

from app.services.question_selector import QuestionGenerationService

# Initialize service
question_gen = QuestionGenerationService()


def generate_question(score: float) -> dict:
    """
    Generate the next pronunciation practice question based on user score.
    Returns:
        {
            "difficulty": "easy",
            "question": "She sells sea shells by the seashore."
        }
    """
    try:
        result = question_gen.generate_question(score)
        return result

    except Exception as e:
        print("Error generating question:", e)

        # fallback safe response
        return {
            "difficulty": "basic",
            "question": "Please repeat the sentence: The sun is bright today."
        }