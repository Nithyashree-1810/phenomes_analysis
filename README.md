🎧 AI Speech & Listening Evaluation System

A FastAPI-based backend system that evaluates both:

🗣️ Pronunciation (Speaking Skills)
🎧 Listening Comprehension

using OpenAI models, IPA phoneme analysis, and audio processing.

🚀 Key Features

🗣️ 1. Pronunciation Evaluation
Upload audio input
Transcribe using OpenAI (gpt-4o-transcribe)
Compare reference text vs spoken transcript
Perform phoneme-level analysis using IPA
Detect:
Mispronounced words
Missing/extra phonemes
Word-level differences
Generate:
Phoneme similarity score (0–100)
Fluency score
Mistakes with severity
Pronunciation improvement tips


🎧 2. Listening Comprehension Evaluation
Generate listening passages dynamically
Generate questions based on passage
Accept user audio response
Transcribe response
Evaluate using LLM (semantic scoring)

Metrics:

Relevance (0–100)
Correctness (0–100)
Feedback (AI-generated)


🧠 3. AI-Based Question Generation
Automatic passage creation
Question generation from prompts
Difficulty-based question selection


🗄️ 4. Database Integration

Stores results for both:

Pronunciation analysis
Listening attempts

Using:

SQLAlchemy ORM
Alembic migrations


⚙️ 5. Audio Processing Pipeline

Audio upload → temp storage
Format conversion (via FFmpeg + pydub)
Transcription → scoring → DB storage

📂 Project Structure

phenomes_analysis/
├── app/
│ ├── core/
│ ├── data/
│ │ └── questions.py
│ ├── db/
│ ├── models/
│ │ ├── listening_model.py
│ │ └── pronunciation_result.py
│ ├── prompts/
│ │ ├── pronunciation_prompt.py
│ │ └── question_prompt.py
│ ├── repo/
│ │ └── pronunciation_repo.py
│ ├── routes/
│ │ ├── audio_route.py
│ │ ├── listening_route.py
│ │ ├── listening_test_route.py
│ │ └── question_route.py
│ ├── services/
│ │ ├── agent_service.py
│ │ ├── audio_service.py
│ │ ├── client.py
│ │ ├── phoneme_engine.py
│ │ ├── question_selector.py
│ │ ├── question_service.py
│ │ ├── transcription_service.py
│ │ └── tts_service.py
│ └── qb_agent.py
│
├── alembic/
├── main.py
├── requirements.txt
├── .gitignore
└── .env




📡 API Endpoints


🔹 Pronunciation
POST /test/analyze
Upload audio + reference text
Returns pronunciation analysis

Response:

{
  "reference_text": "...",
  "transcript": "...",
  "phoneme_score": 92,
  "fluency_score": 65.4,
  "mistakes": [...],
  "tips": [...]
}

🔹 Listening Evaluation
POST /listening/submit-audio
Upload audio response for a passage
Evaluates comprehension

Response:

{
  "expected_answer": "...",
  "user_transcript": "...",
  "relevance": 85,
  "correctness": 78,
  "feedback": "Good understanding, but missed key details."
}

🔹 Question Generation
GET /questions
Returns generated listening/pronunciation questions

⚙️ Setup Instructions

1️⃣ Clone Repository
git clone <repo_url>
cd phenomes_analysis

2️⃣ Create Virtual Environment
python -m venv venv
venv\Scripts\activate

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Add Environment Variables

Create .env:

OPENAI_API_KEY=your_api_key

5️⃣ Run Database Migrations
alembic upgrade head

6️⃣ Run Server
uvicorn main:app --reload

🧪 Technologies Used
FastAPI
OpenAI API
SQLAlchemy
Alembic
Pydub + FFmpeg
Librosa (Fluency Analysis)
IPA Phoneme Analysis
Epitran (fallback phoneme generation)

📌 Important Notes

FFmpeg path must be configured in:

audio_service.py

.gitignore should exclude:

__pycache__/
venv/
.env
temp/

