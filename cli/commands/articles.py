"""Articles commands — list, search, single article."""

from cli import api_client


def cmd_articles(
    category: str | None = None,
    source: str | None = None,
    limit: int = 20,
) -> dict:
    """List articles with optional filters."""
    return api_client.list_articles(category=category, source=source, limit=limit)


def cmd_search(query: str, limit: int = 10) -> dict:
    """Search articles by query string."""
    return api_client.search_articles(query=query, limit=limit)


def cmd_article(article_id: int) -> dict:
    """Get a single article by ID."""
    return api_client.get_article(article_id)
