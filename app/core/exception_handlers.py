
from fastapi import Request
from fastapi.responses import JSONResponse
from app.services.transcription_service import TranscriptionError

async def transcription_error_handler(request: Request, exc: TranscriptionError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"code": exc.code, "detail": exc.detail},
    )