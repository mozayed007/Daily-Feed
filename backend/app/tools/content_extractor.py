"""Content extraction from URLs using trafilatura.

Converts raw HTML or URLs into clean, readable text suitable for
LLM summarization and article processing pipelines.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import httpx
import trafilatura

logger = logging.getLogger(__name__)

# Reusable async client with sane defaults
_DEFAULT_TIMEOUT = httpx.Timeout(15.0, connect=10.0)
_HEADERS = {
    "User-Agent": "DailyFeed/1.0 (news aggregator; +https://github.com/user/Daily_Feed)"
}


@dataclass(frozen=True)
class ExtractedContent:
    """Result of extracting content from a URL or HTML."""

    text: str  # Clean extracted text (markdown-ish)
    title: str  # Page title if found
    url: str  # Source URL
    success: bool  # Whether extraction yielded usable content
    error: Optional[str] = None  # Error message if extraction failed


def extract_from_html(
    html: str,
    url: str = "",
    favor_precision: bool = True,
) -> ExtractedContent:
    """Extract clean text from raw HTML.

    Args:
        html: Raw HTML string.
        url: Source URL (for metadata).
        favor_precision: If True, prefer precise extraction over recall.

    Returns:
        ExtractedContent with the cleaned text.
    """
    if not html or not html.strip():
        return ExtractedContent(text="", title="", url=url, success=False, error="Empty HTML")

    try:
        text = trafilatura.extract(
            html,
            favor_precision=favor_precision,
            include_comments=False,
            include_tables=True,
            deduplicate=True,
            output_format="txt",
        )
        metadata = trafilatura.extract(
            html,
            output_format="json",
            only_with_metadata=False,
        )
        title = ""
        if metadata:
            import json

            try:
                meta = json.loads(metadata)
                title = meta.get("title", "")
            except (json.JSONDecodeError, TypeError):
                pass

        if not text:
            return ExtractedContent(
                text="",
                title=title,
                url=url,
                success=False,
                error="No readable content extracted",
            )

        return ExtractedContent(text=text, title=title, url=url, success=True)

    except Exception as exc:
        logger.warning("trafilatura extraction failed for %s: %s", url, exc)
        return ExtractedContent(text="", title="", url=url, success=False, error=str(exc))


async def extract_from_url(
    url: str,
    timeout: Optional[httpx.Timeout] = None,
    favor_precision: bool = True,
) -> ExtractedContent:
    """Fetch a URL and extract clean text from its HTML.

    Args:
        url: The URL to fetch and extract.
        timeout: HTTP timeout override.
        favor_precision: If True, prefer precise extraction over recall.

    Returns:
        ExtractedContent with the cleaned text.
    """
    if not url:
        return ExtractedContent(text="", title="", url="", success=False, error="Empty URL")

    try:
        async with httpx.AsyncClient(
            timeout=timeout or _DEFAULT_TIMEOUT,
            headers=_HEADERS,
            follow_redirects=True,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        html = response.text
        result = extract_from_html(html, url=url, favor_precision=favor_precision)
        return result

    except httpx.HTTPStatusError as exc:
        logger.warning("HTTP %d fetching %s", exc.response.status_code, url)
        return ExtractedContent(
            text="",
            title="",
            url=url,
            success=False,
            error=f"HTTP {exc.response.status_code}",
        )
    except httpx.RequestError as exc:
        logger.warning("Request error fetching %s: %s", url, exc)
        return ExtractedContent(text="", title="", url=url, success=False, error=str(exc))
    except Exception as exc:
        logger.warning("Unexpected error extracting %s: %s", url, exc)
        return ExtractedContent(text="", title="", url=url, success=False, error=str(exc))


# ── Singleton accessor ──────────────────────────────────────────────────────


_extractor: ContentExtractor | None = None


class ContentExtractor:
    """Stateless wrapper for content extraction functions."""

    async def extract_url(self, url: str) -> ExtractedContent:
        """Extract content from a URL."""
        return await extract_from_url(url)

    def extract_html(self, html: str, url: str = "") -> ExtractedContent:
        """Extract content from raw HTML."""
        return extract_from_html(html, url=url)


def get_content_extractor() -> ContentExtractor:
    """Get or create the singleton ContentExtractor."""
    global _extractor
    if _extractor is None:
        _extractor = ContentExtractor()
    return _extractor
