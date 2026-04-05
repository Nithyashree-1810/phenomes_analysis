"""
app/core/tracing.py
Bootstrap LangSmith tracing.  Call setup_tracing() once at startup.
"""
import os
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def setup_tracing() -> None:
    """
    Configure LangSmith environment variables so LangChain picks them up
    automatically for every chain / LLM call made after this point.
    """

    tracing_enabled = os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    api_key = os.environ.get("LANGCHAIN_API_KEY", "")
    endpoint = os.environ.get("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    project = os.environ.get("LANGCHAIN_PROJECT", "phenome-analysis")

    if not settings.LANGCHAIN_TRACING_V2:
        logger.info("LangSmith tracing disabled (LANGCHAIN_TRACING_V2=false)")
        return

    if not settings.LANGCHAIN_API_KEY:
        logger.warning(
            "LANGCHAIN_TRACING_V2 is true but LANGCHAIN_API_KEY is empty — tracing skipped"
        )
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT

    logger.info(
        "LangSmith tracing enabled → project=%s  endpoint=%s",
        settings.LANGCHAIN_PROJECT,
        settings.LANGCHAIN_ENDPOINT,
    )
