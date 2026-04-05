# 🎙️ AI Pronunciation & Listening Analyser

A FastAPI-based backend that evaluates English pronunciation and listening comprehension using AI. It transcribes spoken audio, compares phonemes, scores pronunciation accuracy, tracks user progress, and generates adaptive exercises — designed as a microservice within a larger interview/language assessment platform.

---

## 📌 What This Project Does

### Pronunciation Module
- Accepts an audio file from the user
- Transcribes it using **OpenAI Whisper**
- Converts both the reference text and transcript to **IPA phonemes** using `espeak-ng`
- Compares phonemes using **Levenshtein distance** on token sequences
- Scores pronunciation at phoneme, fluency, and overall level
- Detects mistakes (missing, wrong, extra words) using `difflib`
- Generates actionable tips using **GPT-4o-mini** via LangChain
- Persists phoneme performance stats per user in PostgreSQL
- Updates user profile: level, weak/strong phonemes, exercise count, time spent

### Listening Module
- Generates a passage using GPT-4o-mini
- Converts it to audio using **Google TTS (gTTS)**
- Generates comprehension questions from the passage
- Accepts 3 spoken audio answers from the user
- Transcribes all 3 using Whisper
- Evaluates all answers in a **single LLM call** for efficiency
- Saves session results to PostgreSQL

### Adaptive Levelling
- Users progress through `basic -> intermediate -> advanced`
- Level-up requires: minimum exercise count + average score >= 70%
- Personalised practice recommendations based on weak phonemes

### Progress & Recommendations
- Profile endpoint exposes live phoneme stats for the frontend dashboard
- Recommendations target the user's weakest phonemes with difficulty-matched sentences

---

## 🏗️ System Architecture

```
+-------------------------------------------------------------------+
|                        CLIENT / FRONTEND                          |
|                  (Dashboard / Interview Platform)                 |
+-----------------------------+-------------------------------------+
                              | HTTP REST
                              v
+-------------------------------------------------------------------+
|                      FASTAPI APPLICATION                          |
|                                                                   |
|  +--------------+   +---------------+   +----------------------+ |
|  | /test        |   | /question     |   | /listening           | |
|  | /analyze     |   | /next         |   | /module              | |
|  |              |   |               |   | /evaluate            | |
|  +------+-------+   +-------+-------+   +-----------+----------+ |
|         |                   |                       |             |
|  +------v-------------------v-----------------------v----------+ |
|  |                      SERVICE LAYER                           | |
|  |                                                              | |
|  |  scoring_service     leveling_service    listening_service   | |
|  |  transcription_svc   post_ex_service     tts_service         | |
|  |  audio_service       pronun_questions    llm_client          | |
|  +------+-------------------------------------------+----------+ |
|         |                                           |             |
|  +------v--------------+             +--------------v----------+ |
|  |   EXTERNAL APIS     |             |    REPOSITORY LAYER     | |
|  |                     |             |                         | |
|  |  OpenAI Whisper     |             |  pronunciation_repo     | |
|  |  GPT-4o-mini        |             |  phoneme_perform_repo   | |
|  |  gTTS               |             |                         | |
|  |  espeak-ng          |             +-------------+-----------+ |
|  |  LangSmith          |                           |             |
|  +---------------------+             +-------------v-----------+ |
|                                      |      PostgreSQL DB       | |
|                                      |                          | |
|                                      |  user_pronun_profile     | |
|                                      |  phoneme_performance     | |
|                                      |  listening_sessions      | |
|                                      +--------------------------+ |
+-------------------------------------------------------------------+
```

---

## 🔄 Pronunciation Pipeline

```
Audio File (mp3/wav)
       |
       v
  [audio_service]
  Convert to WAV (pydub + ffmpeg)
       |
       v
  [transcription_service]
  Whisper whisper-1 --> transcript text
       |
       v
  [scoring_service]
  |-- espeak-ng --> reference IPA
  |-- espeak-ng --> user IPA
  |-- split_ipa() --> phoneme tokens
  |-- levenshtein_tokens() --> phoneme_score
  |-- compute_fluency() --> fluency_score
  |-- extract_mistakes() --> difflib word diff
  +-- gpt_generate_tips() --> GPT-4o-mini tips
       |
       v
  [post_exercise_hook]
  |-- upsert_phoneme() --> phoneme_performance table
  |-- recompute_weak_strong_and_score()
  +-- update_level_progress()
       |
       v
  JSON Response --> Frontend Dashboard
```

---

## 🗂️ Project Structure

```
phenomes_analysis/
├── app/
│   ├── main.py                           # FastAPI app entry point
│   ├── core/
│   │   ├── config.py                     # Centralised settings (pydantic-settings)
│   │   ├── logging.py                    # Structured logging setup
│   │   ├── tracing.py                    # LangSmith tracing setup
│   │   └── phoneme_example_words.py      # Phoneme to example word mapping
│   ├── db/
│   │   ├── base.py                       # SQLAlchemy declarative base
│   │   └── session.py                    # DB session factory
│   ├── models/
│   │   ├── pronunciation_models.py       # UserPronunciationProfile, PhonemePerformance
│   │   ├── listening_model.py            # ListeningSession
│   │   └── user.py                       # User model
│   ├── repo/
│   │   ├── pronunciation_repo.py         # get_or_create_profile
│   │   └── phoneme_performance_repo.py   # upsert_phoneme (ON CONFLICT DO UPDATE)
│   ├── routes/
│   │   ├── audio_route.py                # POST /test/analyze
│   │   ├── question_route.py             # GET /question/next
│   │   ├── listening_route.py            # GET /listening/module, POST /listening/evaluate
│   │   ├── listening_test_route.py       # POST /listening/submit-audio (legacy)
│   │   ├── pronun_profile_route.py       # GET /api/v1/pronunciation/profile/{user_id}
│   │   └── recommendations_route.py      # GET /api/v1/pronunciation/recommendations/{user_id}
│   ├── services/
│   │   ├── scoring_service.py            # IPA extraction, phoneme scoring, fluency
│   │   ├── transcription_service.py      # Whisper transcription
│   │   ├── audio_service.py              # Audio format conversion (pydub/ffmpeg)
│   │   ├── tts_service.py                # Text-to-speech (gTTS)
│   │   ├── post_ex_service.py            # Post-exercise pipeline (upsert, level update)
│   │   ├── leveling_service.py           # Level-up logic and progress tracking
│   │   ├── listening_service.py          # Passage generation + batch evaluation
│   │   ├── pronun_questions_service.py   # Adaptive question generation
│   │   └── llm_client.py                # OpenAI + LangChain client setup
│   ├── schema/
│   │   └── pronun_schema.py              # Pydantic response schemas
│   └── agents/
│       └── qb_agent.py                   # Question bank agent
├── alembic/                              # Database migrations
│   └── versions/                         # Migration history
├── tests/
│   ├── test_leveling.py                  # Unit tests for leveling logic (7 tests)
│   └── test_pronunciation_pipeline.py    # Integration tests (5 tests)
├── conftest.py                           # Pytest path setup
├── pytest.ini                            # Pytest config
├── requirements.txt                      # Python dependencies
├── alembic.ini                           # Alembic config
└── .env                                  # Environment variables (not committed)
```

---

## 🛠️ Tech Stack

| Layer              | Tool                                       |
| ------------------ | ------------------------------------------ |
| Framework          | FastAPI                                    |
| Database           | PostgreSQL + SQLAlchemy 2.0                |
| Migrations         | Alembic                                    |
| Transcription      | OpenAI Whisper (whisper-1)                 |
| IPA Extraction     | espeak-ng subprocess + epitran fallback    |
| LLM                | GPT-4o-mini via LangChain                  |
| TTS                | gTTS (Google Text-to-Speech)               |
| Audio Processing   | pydub + ffmpeg                             |
| Tracing            | LangSmith                                  |
| Testing            | pytest                                     |
| Config             | pydantic-settings + python-dotenv          |
| Validation         | Pydantic v2                                |

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.12+
- PostgreSQL running locally
- ffmpeg installed and in PATH
- espeak-ng installed

**Install espeak-ng (Windows):**
Download from https://github.com/espeak-ng/espeak-ng/releases and add to PATH.

**Install ffmpeg (Windows):**
Download from https://ffmpeg.org/download.html and add to PATH.

### 1. Clone the repository

```bash
git clone <repo-url>
cd phenomes_analysis
```

### 2. Create and activate virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create `.env` file in project root

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/phenomes_analysis
OPENAI_API_KEY=sk-your-openai-key

# LangSmith (optional - for tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__your-langsmith-key
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_PROJECT=phenome_analysis_agent

# App settings
ENVIRONMENT=development
LOG_LEVEL=INFO
WHISPER_MODEL=medium.en
STATIC_AUDIO_DIR=app/static/audio
TEMP_DIR=temp
```

### 5. Create the database

```sql
CREATE DATABASE phenomes_analysis;
```

### 6. Run migrations

```bash
alembic upgrade head
```

### 7. Start the server

```bash
uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

---

## 🔌 API Endpoints

### Pronunciation

| Method | Endpoint                                          | Description                           |
| ------ | ------------------------------------------------- | ------------------------------------- |
| GET    | `/question/next?user_id=`                         | Get next adaptive practice question   |
| POST   | `/test/analyze?user_id=`                          | Upload audio and get pronunciation score |
| GET    | `/api/v1/pronunciation/profile/{user_id}`         | Get user profile and phoneme stats    |
| GET    | `/api/v1/pronunciation/recommendations/{user_id}` | Get personalised practice exercises   |

### Listening

| Method | Endpoint                                              | Description                              |
| ------ | ----------------------------------------------------- | ---------------------------------------- |
| GET    | `/listening/module?difficulty=medium&num_questions=3` | Generate passage and audio and questions |
| POST   | `/listening/evaluate`                                 | Submit 3 audio answers, get batch evaluation |

### Health

| Method | Endpoint   | Description  |
| ------ | ---------- | ------------ |
| GET    | `/healthz` | Health check |

---

## 🔄 Typical User Flow

### Pronunciation Practice

```
1. GET  /question/next?user_id={uuid}
        Response: { "question": "The cat sat on the mat.", "difficulty": "basic" }

2. User records themselves saying the question

3. POST /test/analyze?user_id={uuid}
        Body: audio file (mp3/wav)
        Response: { phoneme_score, fluency_score, overall_score, weak_phonemes, mistakes, tips }

4. GET  /api/v1/pronunciation/profile/{uuid}
        Response: Full profile with level progress and phoneme accuracy

5. GET  /api/v1/pronunciation/recommendations/{uuid}
        Response: Targeted exercises for weak phonemes
```

### Listening Practice

```
1. GET  /listening/module?difficulty=medium&num_questions=3
        Response: { session_id, passage, audio_url, listening_questions }

2. User listens to the audio and records 3 spoken answers

3. POST /listening/evaluate
        Form: session_id + audio_1 + audio_2 + audio_3
        Response: { total_score, results: [{ question, transcript, score, feedback }] }
```

---

## 🧪 Running Tests

### Unit tests — leveling logic

```bash
pytest tests/test_leveling.py -v
```

Expected: **7/7 PASSED**

### Integration tests — full pipeline

First create the test database:

```sql
CREATE DATABASE test_phenomes;
```

Then run:

```bash
pytest tests/test_pronunciation_pipeline.py -v
```

Expected: **5/5 PASSED**

### Run all tests

```bash
pytest -v
```

---

## 🗄️ Database Schema

### `user_pronunciation_profile`

| Column                | Type          | Description                          |
| --------------------- | ------------- | ------------------------------------ |
| id                    | UUID (PK)     | Auto-generated row ID                |
| user_id               | UUID (unique) | Caller-supplied user identifier      |
| current_level         | String        | basic / intermediate / advanced      |
| overall_score_avg     | Numeric       | Running average score                |
| exercises_completed   | Integer       | Total exercises done                 |
| time_spent_total_secs | Integer       | Total practice time in seconds       |
| weak_phonemes         | JSONB         | Phonemes with accuracy below 50%     |
| strong_phonemes       | JSONB         | Phonemes with accuracy above 70%     |
| level_progress        | JSONB         | Progress toward next level           |
| current_question      | String        | Stored question for current session  |
| last_practice_at      | Timestamp     | Last exercise timestamp              |

### `phoneme_performance`

| Column            | Type      | Description            |
| ----------------- | --------- | ---------------------- |
| id                | UUID (PK) | Auto-generated         |
| user_id           | UUID (FK) | Links to profile       |
| phoneme           | String    | IPA phoneme symbol     |
| total_attempts    | Integer   | Cumulative attempts    |
| correct_attempts  | Integer   | Cumulative correct     |
| accuracy_pct      | Numeric   | Running accuracy %     |
| last_attempted_at | Timestamp | Last attempt timestamp |

### `listening_sessions`

| Column           | Type         | Description                        |
| ---------------- | ------------ | ---------------------------------- |
| id               | Integer (PK) | Auto-increment                     |
| session_id       | String       | UUID string from module generation |
| passage          | Text         | Generated passage                  |
| questions        | JSONB        | Questions list                     |
| user_transcript  | Text         | JSON array of transcribed answers  |
| similarity_score | Float        | Average evaluation score           |
| created_at       | Timestamp    | Session creation time              |

---

## 📊 Scoring System

### Pronunciation Score

```
phoneme_score  = (1 - levenshtein_distance / max_phoneme_length) x 100
fluency_score  = 1.0 - (disfluency_count x 0.1)   [min: 0.5]
overall_score  = phoneme_score x 0.7 + fluency_score x 100 x 0.3
```

### Level Progression

```
basic        --> intermediate : 20 exercises + avg score >= 70
intermediate --> advanced     : 20 exercises + avg score >= 70
advanced     --> (max level)  : 30 exercises
```

---

## 🔍 Observability

LangSmith tracing is enabled when `LANGCHAIN_TRACING_V2=true`. Every LLM call is traced with input/output tokens, latency, and run name tags.

Profile API logs response time and warns if it exceeds 200ms:

```
INFO | profile API: user_id=... responded in 12.3ms
WARN | profile API slow: user_id=... took 312.4ms (threshold=200ms)
```

---

## 🔧 Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "describe_change"

# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

---

## 📝 Environment Variables Reference

| Variable             | Required | Default                | Description                    |
| -------------------- | -------- | ---------------------- | ------------------------------ |
| DATABASE_URL         | Yes      | -                      | PostgreSQL connection string   |
| OPENAI_API_KEY       | Yes      | -                      | OpenAI API key                 |
| LANGCHAIN_TRACING_V2 | No       | false                  | Enable LangSmith tracing       |
| LANGCHAIN_API_KEY    | No       | ""                     | LangSmith API key              |
| LANGCHAIN_PROJECT    | No       | phenome_analysis_agent | LangSmith project name         |
| WHISPER_MODEL        | No       | medium.en              | Whisper model size             |
| STATIC_AUDIO_DIR     | No       | app/static/audio       | TTS audio output directory     |
| TEMP_DIR             | No       | temp                   | Temp directory for audio files |
| LOG_LEVEL            | No       | INFO                   | Logging level                  |

---

## ⚠️ Windows-Specific Notes

- **espeak-ng encoding**: subprocess called with `encoding="utf-8", errors="replace"` to avoid `cp1252` codec errors
- **ffmpeg**: must be in system PATH for pydub audio conversion to work
- **CUDA**: `CUDA_VISIBLE_DEVICES=""` is set by default to force CPU inference

---

## 📦 Key Dependencies

```
fastapi              # Web framework
uvicorn              # ASGI server
openai-whisper       # Local speech transcription
openai               # OpenAI API (Whisper + GPT)
langchain-openai     # LangChain LLM wrapper
pydantic-settings    # Settings management
SQLAlchemy==2.0.23   # ORM
psycopg2-binary      # PostgreSQL driver
alembic              # DB migrations
pydub                # Audio processing
gtts                 # Text-to-speech
torch                # PyTorch (Whisper dependency)
pytest               # Testing
python-dotenv        # .env loading
```
