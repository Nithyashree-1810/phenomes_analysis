🎧 AI Speech & Listening Evaluation System

A FastAPI-based backend system that evaluates both:

🗣️ Pronunciation (Speaking Skills)
🎧 Listening Comprehension

using OpenAI models, IPA phoneme analysis, and audio processing.

🚀 Key Features
🗣️ 1. Pronunciation Evaluation
Upload audio input
Transcribe using OpenAI
Compare reference text vs spoken transcript
Perform IPA-based phoneme analysis
Detect:
Mispronounced words
Missing/extra phonemes
Word-level differences
Generate:
Phoneme similarity score
Fluency score
Mistake list with severity
Improvement tips
🎧 2. Listening Comprehension Evaluation
Auto-generate listening passages
Auto-generate questions
Accept audio response
Transcribe & score using LLM

Metrics:

Relevance
Correctness
Feedback
🧠 3. AI-Based Question Generation
Dynamic passage creation
Structured question generation
Difficulty-based selection
🗄️ 4. Database Integration

Stores results for both modules:

Pronunciation
Listening

Using:

SQLAlchemy ORM
Alembic migrations
⚙️ 5. Audio Processing Pipeline
Upload
Convert (FFmpeg + pydub)
Transcribe
Score
Save to DB
📂 Project Structure

(Fully aligned & correctly rendered)

phenomes_analysis/
├── app/
│   ├── core/
│   ├── data/
│   │   └── questions.py
│   ├── db/
│   ├── models/
│   │   ├── listening_model.py
│   │   └── pronunciation_result.py
│   ├── prompts/
│   │   ├── pronunciation_prompt.py
│   │   └── question_prompt.py
│   ├── repo/
│   │   └── pronunciation_repo.py
│   ├── routes/
│   │   ├── audio_route.py
│   │   ├── listening_route.py
│   │   ├── listening_test_route.py
│   │   └── question_route.py
│   ├── services/
│   │   ├── agent_service.py
│   │   ├── audio_service.py
│   │   ├── client.py
│   │   ├── phoneme_engine.py
│   │   ├── question_selector.py
│   │   ├── question_service.py
│   │   ├── transcription_service.py
│   │   └── tts_service.py
│   └── qb_agent.py
│
├── alembic/
├── main.py
├── requirements.txt
├── .gitignore
└── .env

✔ No backslashes
✔ Correct triple-backtick block
✔ GitHub will render perfectly

📡 API Endpoints
🔹 Pronunciation — POST /test/analyze

Response example:

{
  "reference_text": "...",
  "transcript": "...",
  "phoneme_score": 92,
  "fluency_score": 65.4,
  "mistakes": [],
  "tips": []
}
🔹 Listening Evaluation — POST /listening/submit-audio
{
  "expected_answer": "...",
  "user_transcript": "...",
  "relevance": 85,
  "correctness": 78,
  "feedback": "Good understanding, but missed key details."
}
🔹 Questions — GET /questions
⚙️ Setup Instructions
# 1. Clone
git clone <repo_url>
cd phenomes_analysis

# 2. Create virtual env
python -m venv venv
venv\Scripts\activate

# 3. Install deps
pip install -r requirements.txt

# 4. Add API key
echo OPENAI_API_KEY=your_key > .env

# 5. Run migrations
alembic upgrade head

# 6. Start server
uvicorn main:app --reload
🧪 Technologies Used
FastAPI
OpenAI API
SQLAlchemy
Alembic
Pydub + FFmpeg
Librosa
IPA / phoneme analysis
Epitran
