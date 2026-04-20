# Pronunciation Endpoint Workflow

This document describes the request flow for the two pronunciation endpoints and the services they use.

## Overview

The pronunciation functionality is implemented in two HTTP endpoints in `app/routes/pronunciation_route.py`.

The router delegates all business logic to `app/services/pronunciation_service.py`.

Shared processing steps for both endpoints:
- persist uploaded audio to a temporary file
- validate that the audio file format is supported (`m4a`, `wav`)
- convert audio to WAV if needed
- transcribe audio locally using Whisper
- generate a typed response model
- delete temporary files after processing

---

## Endpoint 1: `POST /pronunciation/score`

### Input
- `audio_file` (UploadFile): audio recording in `m4a` or `wav`
- `reference_text` (Form): sentence the user was supposed to speak
- `mode` (Form): either `read_aloud` or `listen_repeat`

### Router behavior
- `score_endpoint()` in `app/routes/pronunciation_route.py`
- validates `mode`
- persists upload with `_persist_upload()`
- calls `score_with_reference(tmp_path, ext, reference_text, mode)`
- wraps `ValueError` as `HTTPException`

### Service flow
- `score_with_reference()` in `app/services/pronunciation_service.py`
- convert audio to WAV via `app/services/audio_service.py:convert_to_wav()`
- transcribe WAV via `app/services/transcription_service.py:transcribe_audio()`
- compute pronunciation scores via `app/services/scoring_service.py:compute_pronunciation_scores()`

### Scoring details
- extracts IPA for reference and transcript
- compares phoneme sequences
- computes phoneme score, fluency score, accuracy score, overall score
- builds phoneme error details
- generates feedback text
- returns `PronunciationScoreResponse`

### Response model
- `transcription`
- `pronunciation_score`
- `fluency_score`
- `accuracy_score`
- `overall_score`
- `phoneme_errors`
- `word_count`
- `mode`
- `feedback`

---

## Endpoint 2: `POST /pronunciation/score-open`

### Input
- `audio_file` (UploadFile): audio recording in `m4a` or `wav`
- `topic` (Form): speaking prompt given to the user
- `max_duration_seconds` (Form): maximum allowed duration, between 5 and 300

### Router behavior
- `score_open_endpoint()` in `app/routes/pronunciation_route.py`
- persists upload with `_persist_upload()`
- calls `score_open_speaking(tmp_path, ext, topic, max_duration_seconds)`
- wraps `ValueError` as `HTTPException`

### Service flow
- `score_open_speaking()` in `app/services/pronunciation_service.py`
- convert audio to WAV via `app/services/audio_service.py:convert_to_wav()`
- transcribe WAV via `app/services/transcription_service.py:transcribe_audio()`
- score fluency, content relevance, and grammar using `app/services/open_scoring_service.py`

### Scoring details
- `score_fluency(transcript, max_duration_seconds)` evaluates pace and filler words
- `score_content_relevance(transcript, topic)` measures keyword overlap with the prompt
- `score_grammar(transcript)` checks basic grammar patterns
- `build_open_feedback(...)` assembles human-readable feedback
- calculates overall score from fluency, content, and grammar
- returns `OpenSpeakingScoreResponse`

### Response model
- `transcription`
- `fluency_score`
- `content_relevance_score`
- `grammar_score`
- `overall_score`
- `word_count`
- `words_per_minute`
- `filler_words`
- `feedback`

---

## Service responsibilities

### `app/services/audio_service.py`
- Converts uploaded audio to WAV with `convert_to_wav()`
- Uses `pydub` and optional `ffmpeg`

### `app/services/transcription_service.py`
- Transcribes audio locally via Whisper
- Loads model once with `_get_model()` and caches it
- Returns clean transcript text

### `app/services/scoring_service.py`
- Extracts IPA using `espeak-ng` or `epitran`
- Compares phoneme sequences and computes pronunciation score
- Computes fluency score from transcript disfluency markers
- Computes word-level mistakes with `difflib`
- Generates pronunciation tips via GPT-4o-mini

### `app/services/open_scoring_service.py`
- Computes fluency metrics, WPM, and filler words
- Scores topic relevance through keyword recall
- Scores grammar using simple regex-based rules
- Builds open-speaking feedback text

---

## Notes

- The router layer is intentionally thin: it only handles request validation, file persistence, and response mapping.
- The service layer holds the core audio, transcription, and scoring logic.
- Temporary audio files are cleaned up after each request.
