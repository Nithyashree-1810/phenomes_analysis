# app/routes/audio_route.py

from fastapi import APIRouter, UploadFile, Request
from pathlib import Path
import os

from app.services.audio_service import convert_to_wav
from app.services.transcription_service import transcribe_audio
from app.services.scoring_service import analyze_pronunciation
from app.services.question_service import get_next_question

router = APIRouter(prefix="/test", tags=["pronunciation"])

@router.post("/analyze")
async def analyze_audio(
    request: Request,
    file: UploadFile,
    reference_text: str
):

    # -------------------------
    # 1. Save Uploaded File
    # -------------------------
    os.makedirs("temp", exist_ok=True)
    temp_path = Path(f"temp/{file.filename}")

    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # -------------------------
    # 2. Convert to WAV
    # -------------------------
    audio_format = temp_path.suffix.replace(".", "")
    wav_path = convert_to_wav(temp_path, audio_format)

    # -------------------------
    # 3. Transcription (uses whisper_model from main.py)
    # -------------------------
    transcript = transcribe_audio(
        request.app.state.whisper_model,
        wav_path
    )

    # -------------------------
    # 4. Pronunciation scoring (your existing logic)
    # -------------------------
    final_score, mistakes, tips = analyze_pronunciation(
        reference_text,
        transcript,
        wav_path
    )

    # -------------------------
    # 5. Get next question (your hardcoded questions.py logic)
    # -------------------------
    next_q = get_next_question(final_score)

    # -------------------------
    # 6. Return Response
    # -------------------------
    return {
        "reference_text": reference_text,
        "transcript": transcript,
        "score": final_score,
        "mistakes": mistakes,
        "tips": tips
        
    }