# app/schemas/pronunciation_schema.py
from __future__ import annotations
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------

class WordScore(BaseModel):
    word: str
    expected_phoneme: str
    actual_phoneme: str
    score: float = Field(..., ge=0.0, le=1.0)
    correct: bool


# ---------------------------------------------------------------------------
# POST /pronunciation/score
# ---------------------------------------------------------------------------

class PronunciationScoreRequest(BaseModel):
    audio_bytes: str = Field(..., description="Base64-encoded audio file (WAV preferred).")
    reference_text: str = Field(..., description="The sentence the user was asked to read.")


class PronunciationScoreResult(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=1.0)
    word_breakdown: list[WordScore]
    mispronounced_words: list[str]
    transcript: str


# ---------------------------------------------------------------------------
# POST /pronunciation/transcribe
# ---------------------------------------------------------------------------

class TranscribeRequest(BaseModel):
    audio_bytes: str = Field(..., description="Base64-encoded audio file (WAV preferred).")


class TranscribeResult(BaseModel):
    transcript: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class OpenSpeakingScoreResponse(BaseModel):
    transcription: str
    fluency_score: float = Field(..., ge=0.0, le=1.0)
    content_relevance_score: float = Field(..., ge=0.0, le=1.0)
    grammar_score: float = Field(..., ge=0.0, le=1.0)
    overall_score: float = Field(..., ge=0.0, le=1.0)
    word_count: int
    words_per_minute: float
    filler_words: list[str]
    feedback: str