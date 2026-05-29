"""
Shared HTTP helper for the MCP server.
Single source of truth for backend URL, auth, and request handling.
"""

import os
from typing import Any

import httpx

BASE_URL = os.environ.get("DAILY_FEED_URL", "http://localhost:8000")
API = f"{BASE_URL}/api/v1"
TIMEOUT = httpx.Timeout(30.0)
TOKEN = os.environ.get("DAILY_FEED_TOKEN")

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """Return a module-level AsyncClient, creating it on first call."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=TIMEOUT)
    return _client


async def api(method: str, path: str, **kwargs) -> dict[str, Any]:
    """Call the backend API. Returns JSON on success, error dict on failure."""
    headers = kwargs.pop("headers", {})
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    client = _get_client()
    try:
        resp = await client.request(method, f"{API}{path}", headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        return {"error": True, "status": e.response.status_code, "detail": e.response.text}
    except httpx.RequestError as e:
        return {"error": True, "detail": f"Request failed: {e}"}
