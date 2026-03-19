from app.services.question_selector import QuestionGenerationService

questionGen = QuestionGenerationService()

def get_next_question(score: float):
    return questionGen.generate_question(score)