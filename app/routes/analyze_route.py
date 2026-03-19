from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
from fastapi import Request

from app.services.audio_service import convert_to_wav
from app.services.transcription_service import transcribe_audio
from app.services.scoring_service import analyze_pronunciation
from app.services.question_service import get_next_question   # ✅ ADDED

router = APIRouter(prefix="/analyze", tags=["analysis"])

@router.post("/file")
async def analyze_file_audio(
    request: Request,
    file: UploadFile = File(...),
    reference_text: str = Form(...),
    audio_format: str = Form("m4a")
):

    try:
        # -----------------------------
        # 1. Save the uploaded audio
        # -----------------------------
        temp_path = Path(f"temp_{file.filename}")

        with open(temp_path, "wb") as f:
            f.write(file.file.read())

        # -----------------------------
        # 2. Convert to WAV
        # -----------------------------
        wav_path = convert_to_wav(temp_path, audio_format)

        # -----------------------------
        # 3. Transcribe using Whisper
        # -----------------------------
        transcript = transcribe_audio(
            request.app.state.whisper_model,
            wav_path
        )

        # -----------------------------
        # 4. Pronunciation scoring
        # -----------------------------
        score, mistakes, tips = analyze_pronunciation(
            reference_text,
            transcript,
            wav_path
        )

        # -----------------------------
        # 5. Generate NEXT QUESTION
        # -----------------------------
        next_question = get_next_question(score)

        # -----------------------------
        # 6. Clean temporary files
        # -----------------------------
        temp_path.unlink(missing_ok=True)
        wav_path.unlink(missing_ok=True)

        # -----------------------------
        # 7. Final JSON Response
        # -----------------------------
        return {
            "transcript": transcript,
            "reference_text": reference_text,

            # 🎯 Pronunciation Analysis
            "pronunciation_score": score,
            "total_mistakes": len(mistakes),
            "mistakes": mistakes,
            "improvement_tips": tips,

            # 🆕 Adaptive Question
            "next_question": next_question
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Pronunciation analysis failed: {str(e)}"
        )