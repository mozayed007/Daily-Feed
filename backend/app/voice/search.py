"""
Web Search tool using DuckDuckGo — no API key needed, entirely free.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from duckduckgo_search import DDGS

logger = logging.getLogger("voice.search")


class WebSearchTool:
    """Search the web via DuckDuckGo."""

    async def search(self, query: str, max_results: int = 5) -> List[dict]:
        """Return a list of results: [{title, href, body}]."""
        logger.info("Web search: %s", query)
        results = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "href": r.get("href", ""),
                        "body": r.get("body", ""),
                    })
        except Exception as exc:
            logger.warning("Web search failed: %s", exc)
        return results

    async def news(self, query: str, max_results: int = 5) -> List[dict]:
        """Search news via DuckDuckGo."""
        logger.info("News search: %s", query)
        results = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.news(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "href": r.get("url", ""),
                        "body": r.get("body", ""),
                        "source": r.get("source", ""),
                        "date": r.get("date", ""),
                    })
        except Exception as exc:
            logger.warning("News search failed: %s", exc)
        return results


_search_tool: WebSearchTool | None = None


def get_web_search_tool() -> WebSearchTool:
    global _search_tool
    if _search_tool is None:
        _search_tool = WebSearchTool()
    return _search_tool
