
import logging
from openai import OpenAI
from langchain_openai import ChatOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Raw OpenAI client (audio / transcription only) ──────────────────────────
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# ── LangChain-wrapped client (all text generation) ──────────────────────────
# temperature=0 for deterministic outputs unless explicitly overridden.
chat_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=settings.OPENAI_API_KEY,
    # LangSmith tags appear in traces
    tags=["phenomes-analysis"],
)

# Convenience builder for one-off calls with custom temperature
def get_chat_llm(temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=temperature,
        openai_api_key=settings.OPENAI_API_KEY,
        tags=["phenomes-analysis"],
    )
