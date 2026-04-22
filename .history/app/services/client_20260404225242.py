"""
app/services/llm_client.py

Single source-of-truth for the OpenAI client used by all services.

We expose TWO things:
  1. `openai_client`  – raw OpenAI() instance for audio/transcription calls
                         that the LangChain wrapper does not support yet.
  2. `chat_llm`       – LangChain ChatOpenAI instance wired with LangSmith
                         tracing.  ALL text-generation calls must use this.

By routing every LLM call through the LangChain client, LangSmith
automatically captures input, output, latency, token counts, and errors
without any manual instrumentation.
"""
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
