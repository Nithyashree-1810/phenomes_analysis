import logging
from openai import OpenAI
from langchain_openai import AzureChatOpenAI

from app.core.config import get_settings
logger = logging.getLogger(__name__)



cfg=get_settings()  # load settings once at module level to avoid repeated env var lookups

# ── LangChain-wrapped client (all text generation) ──────────────────────────
# temperature=0 for deterministic outputs unless explicitly overridden.
"""chat_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=cfg.OPENAI_API_KEY,
    # LangSmith tags appear in traces
    tags=["phenomes-analysis"],
)"""

def get_azure_chat_llm(temperature: float = 0.7) -> AzureChatOpenAI:
    """Azure OpenAI LLM — used by listening module."""
    settings = get_settings()
    return AzureChatOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        temperature=temperature,
    )
