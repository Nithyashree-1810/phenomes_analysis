import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import whisper
import torch

from app.routes.question_route import router as question_router
from app.routes.audio_route import router as audio_router
from app.routes.listening_route import router as listening_router 
from app.routes.listening_test_route import router as eval_router
from app

from dotenv import load_dotenv



load_dotenv()

# ---------- Optional: Force CPU if needed ----------
os.environ["CUDA_VISIBLE_DEVICES"] = os.getenv("CUDA_VISIBLE_DEVICES", "")



# ---------- FastAPI App ----------
app = FastAPI(
    title="AI Pronunciation Analyzer",
    description="Detects mispronounced words, phoneme differences, gives pronunciation tips, and generates dynamic listening exercises",
    version="3.0"
)
 

# ---------- Load Whisper Model ----------

model = whisper.load_model("medium.en")
app.state.whisper_model = model


# ---------- Include Routers ----------
app.include_router(audio_router)
app.include_router(question_router)
app.include_router(listening_router) 
app.include_router(eval_router)

# ---------- Serve Static Audio ----------
# This allows the frontend to access /static/audio/filename.mp3
app.mount("/static", StaticFiles(directory="app/static"), name="static")