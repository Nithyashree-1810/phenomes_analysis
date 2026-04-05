from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import torch
import whisper
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.tracing import setup_tracing

from app.routes.question_route import router as question_router
from app.routes.audio_route import router as audio_router
from app.routes.listening_route import router as listening_router
from app.routes.listening_test_route import router as eval_router
from app.routes.recommendations_route import router as recommendations_router
from app.routes.pronun_profile_route import router as pronun_profile_router

# ── Bootstrap logging & tracing before anything else ────────────────────────
setup_logging()
setup_tracing()

logger = logging.getLogger(__name__)

# ── GPU / CUDA config ────────────────────────────────────────────────────────
# Set to "" to force CPU; set to "0" (or "0,1") to use specific GPU(s).
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")


# ── Lifespan: load heavy models once at startup ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading Whisper model '%s'...", settings.WHISPER_MODEL)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(settings.WHISPER_MODEL, device=device)
    app.state.whisper_model = model
    logger.info("Whisper model loaded on %s.", device)

    # Ensure static audio directory exists
    Path(settings.STATIC_AUDIO_DIR).mkdir(parents=True, exist_ok=True)

    yield  # application runs here

    logger.info("Shutting down.")


# ── Application ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Pronunciation & Listening Analyser",
    description=(
        "Detects mispronounced words, phoneme differences, gives pronunciation "
        "tips, and generates dynamic listening exercises."
    ),
    version="4.0",
    lifespan=lifespan,
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(audio_router)
app.include_router(question_router)
app.include_router(listening_router)
app.include_router(eval_router)
app.include_router(recommendations_router)
app.include_router(pronun_profile_router)

# ── Static files ─────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=settings.STATIC_AUDIO_DIR.rsplit("/", 1)[0]), name="static")


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/healthz", tags=["Health"], include_in_schema=False)
def health():
    return {"status": "ok"}
