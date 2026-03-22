# app/routes/audio_route.py
from fastapi import APIRouter, UploadFile, Request, Depends, Query
from sqlalchemy.orm import Session
from pathlib import Path
import os

from app.services.audio_service import convert_to_wav
from app.services.transcription_service import transcribe_audio
from app.services.scoring_service import score_pronunciation
from app.services.question_service import generate_pronunciation_question
from app.repo.prounciation_repo import save_pronunciation_result
from app.db.session import get_db

router = APIRouter(prefix="/test", tags=["pronunciation"])

@router.post("/analyze")
async def analyze_audio(
    request: Request,
    file: UploadFile,
    reference_text: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Analyze uploaded audio for pronunciation:
        - Transcribe via Whisper
        - Score phonemes + fluency
        - Store results in DB
    """
    try:
        # 1️⃣ Save uploaded file safely in binary mode
        os.makedirs("temp", exist_ok=True)
        temp_path = Path("temp") / file.filename
        file_content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(file_content)

        # 2️⃣ Convert to WAV
        audio_format = temp_path.suffix.replace(".", "").lower()
        wav_path = convert_to_wav(temp_path, audio_format)

        # 3️⃣ Transcription using Whisper
        transcript = transcribe_audio(wav_path)

        # 4️⃣ Pronunciation scoring (returns dict)
        result = score_pronunciation(
            reference_text,
            transcript,
            wav_path
        )

        phoneme_score = result.get("phoneme_score", 0)
        fluency_score = result.get("fluency_score", 0)
        mistakes = result.get("mistakes", [])
        tips = result.get("tips", [])

        # 5️⃣ Save results in DB
        db_data = {
            "transcript": transcript,
            "reference_text": reference_text,
            "pronunciation_score": phoneme_score,
            "total_mistakes": len(mistakes),
            "mistakes": mistakes,
            "improvement_tips": tips,
            "audio_path": str(wav_path)
        }
        save_pronunciation_result(db, db_data)

        # 6️⃣ Get next question based on score
        next_q = generate_pronunciation_question(phoneme_score)

        # 7️⃣ Return API response
        return {
            "reference_text": reference_text,
            "transcript": transcript,
            "phoneme_score": phoneme_score,
            "fluency_score": fluency_score,
            "mistakes": mistakes,
            "tips": tips,
        }

    except Exception as e:
        # Handle any unexpected errors
        return {
            "error": str(e),
            "message": "Failed to process audio. Ensure the file is valid and in a compatible audio format."
        }