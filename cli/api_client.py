"""HTTP client for the Daily Feed backend API."""

import os

import httpx

BASE_URL = os.environ.get("DAILY_FEED_URL", "http://localhost:8000")
TIMEOUT = 30.0


def _client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=TIMEOUT)


def _get(path: str, params: dict | None = None) -> dict | list:
    """GET request. Returns parsed JSON or raises."""
    with _client() as c:
        r = c.get(path, params=params)
        r.raise_for_status()
        return r.json()


def _post(path: str, json: dict | None = None) -> dict | list:
    """POST request. Returns parsed JSON or raises."""
    with _client() as c:
        r = c.post(path, json=json)
        r.raise_for_status()
        return r.json()


# ---- Public API ----


def health() -> dict:
    return _get("/api/v1/health")


def list_articles(
    category: str | None = None,
    source: str | None = None,
    limit: int = 20,
) -> dict:
    params: dict = {"page_size": limit}
    if category:
        params["category"] = category
    if source:
        params["source"] = source
    return _get("/api/v1/articles", params=params)


def search_articles(query: str, limit: int = 10) -> dict:
    return _get("/api/v1/articles/search", params={"q": query, "limit": limit})


def get_article(article_id: int) -> dict:
    return _get(f"/api/v1/articles/{article_id}")


def get_sources() -> list:
    return _get("/api/v1/sources")


def get_digests(limit: int = 10) -> list:
    return _get("/api/v1/digests", params={"limit": limit})


def get_stats() -> dict:
    return _get("/api/v1/stats")


def get_interests() -> dict:
    return _get("/api/v1/memory/interests")


def trigger_fetch() -> dict:
    return _post("/api/v1/sources/fetch")


def run_pipeline(task_type: str) -> dict:
    return _post(f"/api/v1/pipeline/{task_type}")
