"""
MCP resources for Daily Feed.
Exposes system state as readable resources agents can subscribe to.
"""

import json
import os

import httpx

BASE_URL = os.environ.get("DAILY_FEED_URL", "http://localhost:8000")
API = f"{BASE_URL}/api/v1"
TIMEOUT = httpx.Timeout(30.0)


async def _fetch(path: str) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(f"{API}{path}")
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            return {"error": str(e)}


def register_resources(mcp) -> None:
    """Register all resources on the given FastMCP instance."""

    @mcp.resource("daily://digest/latest")
    async def latest_digest() -> str:
        """The most recent news digest. Contains clustered articles, highlights, and delivery status."""
        data = await _fetch("/digests?limit=1")
        if data.get("error"):
            return json.dumps(data)
        digests = data if isinstance(data, list) else []
        if not digests:
            return json.dumps({"message": "No digests available yet."})
        return json.dumps(digests[0], indent=2)

    @mcp.resource("daily://interests")
    async def user_interests() -> str:
        """The user's learned interest profile. Topics, categories, and reading preferences."""
        data = await _fetch("/memory/interests")
        return json.dumps(data, indent=2)

    @mcp.resource("daily://config")
    async def system_config() -> str:
        """Current system configuration. LLM provider, scheduler settings, pipeline parameters."""
        data = await _fetch("/config")
        return json.dumps(data, indent=2)
