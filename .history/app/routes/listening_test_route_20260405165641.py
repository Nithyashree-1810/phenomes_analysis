import json
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.listening_model import ListeningSession
from app.services.listening_service import evaluate_answers_batch
from app.services.transcription_service import transcribe_audio
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/listening", tags=["Listening"])


