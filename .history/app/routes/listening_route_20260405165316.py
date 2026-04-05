"""
app/routes/listening_route.py
GET /listening/module — Generate a listening passage, audio, and questions.
"""
import logging
from app.db.session import get_db
from fastapi import APIRouter, Depends, Query
from app.services.listening_service import generate_listening_module
from app.schema.pronun_schema import ListeningModuleOut
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/listening", tags=["Listening"])


@router.get(
    "/module",
    response_model=ListeningModuleOut,
    summary="Generate listening module",
)
async def get_listening_module(
    difficulty: str = Query(default="medium", pattern="^(easy|medium|hard)$"),
    num_questions: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
):
   
