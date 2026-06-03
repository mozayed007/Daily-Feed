"""
Daily Feed MCP Server.

Wraps the FastAPI backend as atomic, composable tools for AI agents.
Run: python -m app.mcp.server
"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from app.mcp._http import api

mcp = FastMCP(
    "Daily Feed",
    instructions="Personalized news aggregator. Browse, search, summarize, and analyze articles from curated RSS sources.",
)


def _compact_article(a: dict) -> dict:
    """Strip an article down to the fields an agent needs in a list."""
    return {
        "id": a.get("id"),
        "title": a.get("title"),
        "source": a.get("source"),
        "category": a.get("category"),
        "summary": (a.get("summary") or "")[:200],
    }


# ── Tools ──────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_briefing() -> dict[str, Any]:
    """Get a personalized news digest.

    Runs the full pipeline (fetch, process, digest) and returns the result.

    Returns:
        Digest content with articles, clusters, and highlights.

    Example:
        get_briefing()
    """
    result = await api("POST", "/pipeline/full")
    if result.get("error"):
        return result
    return result.get("result", result)


@mcp.tool()
async def list_articles(
    category: str = None,
    source: str = None,
    processed: bool = None,
    limit: int = 20,
) -> dict[str, Any]:
    """List articles with optional filters.

    Args:
        category: Filter by category name (e.g. "Technology", "Science"). Case-sensitive.
        source: Filter by RSS source name (e.g. "Hacker News").
        processed: True = only AI-processed articles, False = only unprocessed, None = all.
        limit: Max articles to return. Default 20, max 100.

    Returns:
        Compact list with id, title, source, category, and summary snippet for each article.

    Example:
        list_articles(category="Technology", processed=True, limit=10)
    """
    params: dict[str, Any] = {"page_size": min(limit, 100)}
    if category is not None:
        params["category"] = category
    if source is not None:
        params["source"] = source
    if processed is not None:
        params["processed"] = processed

    data = await api("GET", "/articles", params=params)
    if data.get("error"):
        return data

    articles = [_compact_article(a) for a in data.get("articles", [])]
    return {"total": data.get("total", 0), "articles": articles}


@mcp.tool()
async def search_articles(query: str, limit: int = 10) -> dict[str, Any]:
    """Full-text search across article titles, summaries, and content.

    Args:
        query: Search terms. Example: "climate policy", "OpenAI", "supply chain".
        limit: Max results. Default 10, max 100.

    Returns:
        Matching articles with id, title, source, category, and summary snippet.

    Example:
        search_articles("artificial intelligence regulation", limit=5)
    """
    data = await api("GET", "/articles/search", params={"q": query, "limit": min(limit, 100)})
    if data.get("error"):
        return data

    articles = [_compact_article(a) for a in data.get("articles", [])]
    return {"query": query, "total": data.get("total", 0), "articles": articles}


@mcp.tool()
async def get_article(article_id: int) -> dict[str, Any]:
    """Get full details for a single article.

    Args:
        article_id: The article ID (integer). Use list_articles or search_articles to find IDs.

    Returns:
        Full article with title, content, summary, key_points, category, source, and metadata.

    Example:
        get_article(42)
    """
    return await api("GET", f"/articles/{article_id}")


@mcp.tool()
async def summarize_article(article_id: int, style: str = "concise") -> dict[str, Any]:
    """AI-summarize an article with a chosen style.

    Args:
        article_id: The article ID (integer).
        style: Summary style. One of:
            - "concise": 2-3 sentence overview
            - "detailed": thorough summary with context
            - "bullet_points": key takeaways as a list

    Returns:
        Summary text, key_points, category, and critic score.

    Example:
        summarize_article(42, style="bullet_points")
    """
    result = await api("POST", f"/articles/{article_id}/summarize")
    if result.get("error"):
        return result
    return {
        "success": result.get("success"),
        "summary": result.get("summary"),
        "key_points": result.get("key_points"),
        "category": result.get("category"),
        "score": result.get("score"),
    }


@mcp.tool()
async def detect_trends() -> dict[str, Any]:
    """Find emerging topics and patterns from recent articles.

    Scans recent articles to identify trending themes, recurring subjects,
    and topics gaining momentum across sources.

    Returns:
        Trend analysis with topic clusters, frequency, and representative articles.

    Example:
        detect_trends()
    """
    result = await api("POST", "/pipeline/trends")
    if result.get("error"):
        return result
    return result.get("result", result)


@mcp.tool()
async def cluster_articles(article_ids: list[int]) -> dict[str, Any]:
    """Group articles by topic similarity.

    Args:
        article_ids: List of article IDs to cluster. Get IDs from list_articles or search_articles.
            Minimum 2 articles recommended for meaningful clusters.

    Returns:
        Topic clusters with article assignments and cluster labels.

    Example:
        cluster_articles([1, 5, 12, 18, 23])
    """
    result = await api("POST", "/articles/cluster", json={"article_ids": article_ids})
    if result.get("error"):
        return result
    return result


@mcp.tool()
async def synthesize_topic(topic: str, article_ids: list[int]) -> dict[str, Any]:
    """Merge multi-source coverage on a single topic into a unified analysis.

    Args:
        topic: The topic to synthesize. Example: "EU AI Act", "Fed interest rate decision".
        article_ids: Article IDs covering this topic. Get from search_articles or list_articles.

    Returns:
        Synthesized analysis combining perspectives from all provided sources.

    Example:
        synthesize_topic("OpenAI GPT-5 launch", [10, 15, 22, 31])
    """
    result = await api(
        "POST", "/articles/synthesize", json={"topic": topic, "article_ids": article_ids}
    )
    if result.get("error"):
        return result
    return result


@mcp.tool()
async def explain_relevance(article_id: int) -> dict[str, Any]:
    """Explain why an article matches the user's learned interests.

    Args:
        article_id: The article ID (integer).

    Returns:
        Explanation of relevance to user preferences, matching interest categories, and score.

    Example:
        explain_relevance(42)
    """
    return await api("POST", f"/articles/{article_id}/reason")


@mcp.tool()
async def get_user_interests() -> dict[str, Any]:
    """Get the user's learned interest profile.

    Returns topics, categories, and entities the system has identified as user preferences
    based on reading history and interactions.

    Returns:
        Interest categories, topic weights, and preference metadata.

    Example:
        get_user_interests()
    """
    return await api("GET", "/memory/interests")


@mcp.tool()
async def get_sources() -> dict[str, Any]:
    """List all configured RSS sources.

    Returns enabled sources with name, URL, category, and status.

    Example:
        get_sources()
    """
    data = await api("GET", "/sources")
    if data.get("error"):
        return data
    return {"sources": data}


@mcp.tool()
async def trigger_fetch() -> dict[str, Any]:
    """Fetch new articles from all enabled RSS sources.

    Triggers a background fetch job. Returns immediately; new articles
    will appear in subsequent list_articles calls after processing.

    Example:
        trigger_fetch()
    """
    return await api("POST", "/sources/fetch")


@mcp.tool()
async def get_stats() -> dict[str, Any]:
    """Get system statistics and recent activity.

    Returns article counts (total, processed, unprocessed), source counts,
    category breakdown, digest count, and recent activity feed.

    Example:
        get_stats()
    """
    return await api("GET", "/stats")


@mcp.tool()
async def run_pipeline(task_type: str) -> dict[str, Any]:
    """Execute a pipeline task.

    Args:
        task_type: Pipeline to run. One of:
            - "fetch": Fetch articles from all RSS sources
            - "process": AI-summarize unprocessed articles
            - "digest": Generate and deliver a digest
            - "full": Complete pipeline (fetch -> process -> digest)
            - "trends": Detect emerging trends
            - "cluster": Cluster articles by topic
            - "synthesize": Synthesize multi-source coverage
            - "memory_sync": Sync articles to memory store

    Returns:
        Pipeline result with success status and output data.

    Example:
        run_pipeline("process")
    """
    valid = {"fetch", "process", "digest", "full", "trends", "cluster", "synthesize", "memory_sync"}
    if task_type not in valid:
        return {"error": True, "detail": f"Invalid task_type '{task_type}'. Valid: {sorted(valid)}"}

    result = await api("POST", f"/pipeline/{task_type}")
    if result.get("error"):
        return result
    return result


# ── Resources & Prompts ────────────────────────────────────────────────────

from app.mcp.prompts import register_prompts
from app.mcp.resources import register_resources

register_resources(mcp)
register_prompts(mcp)

# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
