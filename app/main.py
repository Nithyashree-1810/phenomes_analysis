import os
from fastapi import FastAPI
import whisper
import torch

from app.routes.analyze_route import router as analyze_router
from app.routes.question_route import router as question_router

# ---------- Force CPU ----------
os.environ["CUDA_VISIBLE_DEVICES"] = ""

print("CUDA available:", torch.cuda.is_available())

# ---------- FastAPI ----------
app = FastAPI(
    title="AI Pronunciation Analyzer",
    description="Detects mispronounced words, phoneme differences, and gives pronunciation tips",
    version="3.0"
)

# ---------- Load Whisper ----------
model = whisper.load_model("medium.en")

# ---------- Attach model to app state ----------
app.state.whisper_model = model

# ---------- Routers ----------
app.include_router(analyze_router)
app.include_router(question_router)