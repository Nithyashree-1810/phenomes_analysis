import os
from fastapi import FastAPI, UploadFile, File, Form
from pathlib import Path
import whisper
import torch
import panphon.featuretable as pf
import pandas as pd
from app.utils import file_to_wav, compare_phonemes
import epitran

# ------------------------------
# Force CPU usage (optional)
# ------------------------------
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TORCH_USE_CUDA_DSA"] = "0"
os.environ["PYTORCH_NO_CUDA_MEMORY_CACHING"] = "1"

print("CUDA available:", torch.cuda.is_available())

# ------------------------------
# Patch Panphon FeatureTable to use your CSV
# ------------------------------
csv_path = os.path.abspath("data/ipa_all.csv")  # ensure CSV is here

def patched_read_bases(self, bases_fn, weights):
    df = pd.read_csv(csv_path, header=None, encoding="utf-8")
    segments = df[0].tolist()
    seg_dict = {seg: list(df.iloc[i, 1:]) for i, seg in enumerate(segments)}
    names = df.columns[1:].tolist()
    return segments, seg_dict, names

pf.FeatureTable._read_bases = patched_read_bases

# ------------------------------
# Initialize FastAPI
# ------------------------------
app = FastAPI(title="Passage Pronunciation Analyzer")

# ------------------------------
# Whisper model
# ------------------------------
model = whisper.load_model("base")

# ------------------------------
# Cache for Epitran instances
# ------------------------------
epi_map_cache = {}

def get_phonemes(text: str, lang: str = "eng-Latn"):
    if lang not in epi_map_cache:
        epi_map_cache[lang] = epitran.Epitran(lang)
    epi = epi_map_cache[lang]
    return epi.transliterate(text)  # can also use epi.word_to_phonemes(text)

# ------------------------------
# API Endpoint
# ------------------------------
@app.post("/analyze/file")
def analyze_file_audio(
    file: UploadFile = File(...),
    reference_text: str = Form(...),
    audio_format: str = Form("m4a")
):
    temp_path = Path(f"temp_{file.filename}")
    with open(temp_path, "wb") as f:
        f.write(file.file.read())

    # Convert to WAV
    wav_path = file_to_wav(temp_path, audio_format)

    # Transcribe audio using Whisper
    result = model.transcribe(str(wav_path))
    transcript = result['text']

    # Compare phonemes
    score, mistakes, tips = compare_phonemes(reference_text, transcript)

    # Clean up temp files
    temp_path.unlink(missing_ok=True)
    wav_path.unlink(missing_ok=True)

    return {
        "transcript": transcript,
        "reference": reference_text,
        "score": score,
        "mistakes": mistakes,
        "improvement_tips": tips
    }