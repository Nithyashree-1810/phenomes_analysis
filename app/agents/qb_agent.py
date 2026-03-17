import os
from openai import OpenAI


   
from dotenv import load_dotenv
load_dotenv()



def get_client():
    """Create and return an OpenAI client using OPENAI_API_KEY.

    Raises a RuntimeError with instructions if the key is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    print("Loaded API KEY =", api_key)
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def generate_question(level, weak_phonemes=None):

    prompt = f"""
    Generate one pronunciation practice sentence.

    Difficulty: {level}

    Keep it natural. Do not include any phoneme list.
    Output only the sentence.
    """

    client = get_client()

    if client is None:
        level_text = str(level)
        return f"({level_text}) Practice this sentence."
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()