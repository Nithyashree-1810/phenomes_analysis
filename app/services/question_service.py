def next_question_level(score):

    if score >= 85:
        return "advanced"

    if score >= 60:
        return "intermediate"

    return "beginner"