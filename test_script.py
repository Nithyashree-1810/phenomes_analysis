import os
from openai import OpenAI
from gtts import gTTS
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Write a short 3-4 sentence English listening passage."}],
        temperature=0.7,
        max_tokens=150
    )
    passage = response.choices[0].message.content.strip()
    print("Passage generated:", passage)

    # Test TTS
    tts = gTTS(text=passage, lang="en")
    tts.save("test_passage.mp3")
    print("Audio saved as test_passage.mp3")

except Exception as e:
    print("Error:", e)