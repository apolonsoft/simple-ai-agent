# app/tools/search.py
import logging
import os
from typing import Any, cast

from tavily import TavilyClient

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_tavily_client() -> TavilyClient:
    key = getattr(settings, "TAVILY_API_KEY", "") or os.environ.get(
        "TAVILY_API_KEY", ""
    )
    return TavilyClient(api_key=key if key else None)


tavily_client = _get_tavily_client()


def search_web(
    query: str,
    max_results: int = 5,
    topic: str = "general",
    time_range: str | None = None,
) -> list[Any] | str:
    """Search the web for the given query."""
    try:
        response: dict[str, Any] = tavily_client.search(
            query,
            max_results=max_results,
            topic=cast(Any, topic),
            time_range=cast(Any, time_range),
        )
        results = response.get("results")
        if isinstance(results, list):
            return results
        return str(results) if results is not None else []
    except Exception as e:
        return f"Error: Search failed - {e}"
