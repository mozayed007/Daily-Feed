"""
MCP resources for Daily Feed.
Exposes system state as readable resources agents can subscribe to.
"""

import json

from mcp.server.fastmcp import FastMCP

from app.mcp._http import api


def register_resources(mcp: FastMCP) -> None:
    """Register all resources on the given FastMCP instance."""

    @mcp.resource("daily://digest/latest")
    async def latest_digest() -> str:
        """The most recent news digest. Contains clustered articles, highlights, and delivery status."""
        data = await api("GET", "/digests?limit=1")
        if data.get("error"):
            return json.dumps(data)
        digests = data if isinstance(data, list) else []
        if not digests:
            return json.dumps({"message": "No digests available yet."})
        return json.dumps(digests[0], indent=2)

    @mcp.resource("daily://interests")
    async def user_interests() -> str:
        """The user's learned interest profile. Topics, categories, and reading preferences."""
        data = await api("GET", "/memory/interests")
        return json.dumps(data, indent=2)

    @mcp.resource("daily://config")
    async def system_config() -> str:
        """Current system configuration. LLM provider, scheduler settings, pipeline parameters."""
        data = await api("GET", "/config")
        return json.dumps(data, indent=2)
