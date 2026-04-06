import os
import uuid
import json
import re
from gtts import gTTS
from app.services.llclient import client

STATIC_AUDIO_DIR = "app/static/audio"
os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)

class ListeningQuestionsService:
    """
    Generates listening passages, TTS audio, and comprehension questions.
    """

    def generate_passage(self, difficulty: str = "medium") -> str:
        prompt = f"Generate a short {difficulty}-level English passage for listening practice, 3-4 sentences."
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()

    def generate_questions(self, passage: str, num_questions: int = 3):
        prompt = f"Generate {num_questions} comprehension questions from this passage in JSON array:\n{passage}"
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=400
            )
            raw_text = response.choices[0].message.content.strip()
            match = re.search(r"\[.*\]", raw_text, flags=re.DOTALL)
            if match:
                questions = json.loads(match.group())
                for idx, q in enumerate(questions):
                    q.setdefault("id", idx+1)
                return questions
        except:
            pass
        return [{"id": i+1, "text": f"Question {i+1}"} for i in range(num_questions)]

    def generate_listening_module(self, difficulty: str = "medium", num_questions: int = 3):
        passage = self.generate_passage(difficulty)
        questions = self.generate_questions(passage, num_questions)
        audio_filename = f"listening_{uuid.uuid4().hex}.mp3"
        audio_path = os.path.join(STATIC_AUDIO_DIR, audio_filename)
        tts = gTTS(text=passage, lang="en")
        tts.save(audio_path)
        audio_url = f"/static/audio/{audio_filename}"
        return {
            "passage": passage,
            "audio_url": audio_url,
            "listening_questions": questions
        }