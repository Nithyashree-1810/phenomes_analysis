import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pathlib import Path
import whisper
import torch
import panphon.featuretable as pf
import pandas as pd

from app.utils import file_to_wav, compare_phonemes


# ---------- Force CPU ----------
os.environ["CUDA_VISIBLE_DEVICES"] = ""

print("CUDA available:", torch.cuda.is_available())


# ---------- Patch Panphon CSV ----------
csv_path = os.path.abspath("data/ipa_all.csv")

def patched_read_bases(self, bases_fn, weights):
    df = pd.read_csv(csv_path, header=None, encoding="utf-8")
    segments = df[0].tolist()
    seg_dict = {seg: list(df.iloc[i, 1:]) for i, seg in enumerate(segments)}
    names = df.columns[1:].tolist()
    return segments, seg_dict, names

pf.FeatureTable._read_bases = patched_read_bases


# ---------- FastAPI ----------
app = FastAPI(
    title="AI Pronunciation Analyzer",
    description="Detects mispronounced words, phoneme differences, and gives pronunciation tips",
    version="2.0"
)


# ---------- Load Whisper ----------
model = whisper.load_model("small.en")


# ---------- API ----------
@app.post("/analyze/file")
def analyze_file_audio(
    file: UploadFile = File(...),
    reference_text: str = Form(...),
    audio_format: str = Form("m4a")
):

    try:

        # ---------- Save uploaded file ----------
        temp_path = Path(f"temp_{file.filename}")

        with open(temp_path, "wb") as f:
            f.write(file.file.read())


        # ---------- Convert to WAV ----------
        wav_path = file_to_wav(temp_path, audio_format)


        # ---------- Speech → Text ----------
        result = model.transcribe(
            str(wav_path),
            language="en",
            fp16=False
        )

        transcript = result["text"].strip()


        # ---------- Pronunciation Analysis ----------
        score, mistakes, tips = compare_phonemes(reference_text, transcript)


        # ---------- Cleanup ----------
        temp_path.unlink(missing_ok=True)
        wav_path.unlink(missing_ok=True)


        # ---------- API Response ----------
        return {
            "transcript": transcript,
            "reference_text": reference_text,
            "pronunciation_score": score,
            "total_mistakes": len(mistakes),
            "mistakes": mistakes,
            "improvement_tips": tips
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Pronunciation analysis failed: {str(e)}"
        )