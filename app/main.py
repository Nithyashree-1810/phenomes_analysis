import os
from fastapi import FastAPI, UploadFile, File, Form
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
app = FastAPI(title="Passage Pronunciation Analyzer")


# ---------- Whisper Model ----------
model = whisper.load_model("small.en")   # better than base


# ---------- API ----------
@app.post("/analyze/file")
def analyze_file_audio(
    file: UploadFile = File(...),
    reference_text: str = Form(...),
    audio_format: str = Form("m4a")
):

    temp_path = Path(f"temp_{file.filename}")

    with open(temp_path, "wb") as f:
        f.write(file.file.read())

    wav_path = file_to_wav(temp_path, audio_format)

    # Transcribe
    result = model.transcribe(str(wav_path))
    transcript = result["text"]

    # Pronunciation comparison
    score, mistakes, tips = compare_phonemes(reference_text, transcript)

    temp_path.unlink(missing_ok=True)
    wav_path.unlink(missing_ok=True)

    return {
        "transcript": transcript,
        "reference": reference_text,
        "score": score,
        "mistakes": mistakes,
        "improvement_tips": tips
    }