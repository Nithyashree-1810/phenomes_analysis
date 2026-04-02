from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class PhonemeStat(BaseModel):
    phoneme: str
    accuracy: float
    total_attempts: int
    correct_attempts: int
    last_attempted_at: Optional[datetime]


class WeakPhoneme(BaseModel):
    phoneme: str
    error_rate: float
    example_word: Optional[str] = None


class StrongPhoneme(BaseModel):
    phoneme: str
    accuracy: float


class LevelProgress(BaseModel):
    current: str
    exercises_at_level: int
    required_for_next: int
    avg_score_at_level: float


class UserPronunciationProfileOut(BaseModel):
    user_id: int   # ← UPDATED (was UUID)
    current_level: str
    overall_score_avg: float
    exercises_completed: int
    time_spent_total_mins: float
    weak_phonemes: List[WeakPhoneme]
    strong_phonemes: List[StrongPhoneme]
    level_progress: LevelProgress
    last_practice: Optional[datetime]

    mo Config:
        orm_mode = True


class RecommendationSentence(BaseModel):
    sentence: str
    difficulty: str


class RecommendationItem(BaseModel):
    phoneme: str
    exercises: List[RecommendationSentence]


class PronunciationRecommendationOut(BaseModel):
    focus_areas: List[RecommendationItem]
    suggested_practice_time_mins: int
    next_milestone: str