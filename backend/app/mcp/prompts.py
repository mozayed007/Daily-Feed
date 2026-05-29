"""
MCP prompts for Daily Feed.
Returns structured prompt templates agents can use for common news workflows.
"""

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register all prompts on the given FastMCP instance."""

    @mcp.prompt()
    def morning_briefing() -> str:
        """Structured prompt for a morning news briefing. Use with get_briefing("morning")."""
        return (
            "You are a morning news briefing assistant.\n\n"
            "Steps:\n"
            "1. Call get_briefing('morning') to fetch today's digest.\n"
            "2. Call get_user_interests() to understand the user's priorities.\n"
            "3. Organize the briefing by importance to the user's interests.\n"
            "4. For each major story, provide a one-sentence summary and why it matters.\n"
            "5. Highlight any breaking developments or trend shifts.\n"
            "6. End with a 'Watch list' of 2-3 developing stories to follow today.\n\n"
            "Tone: Informative, concise, opinionated where appropriate. "
            "Assume the reader is smart but busy."
        )

    @mcp.prompt()
    def evening_roundup() -> str:
        """Structured prompt for an evening digest. Use with get_briefing("evening")."""
        return (
            "You are an evening news roundup assistant.\n\n"
            "Steps:\n"
            "1. Call get_briefing('evening') to fetch the day's digest.\n"
            "2. Call detect_trends() to identify what shifted today.\n"
            "3. Group stories into 'What happened', 'What it means', and 'What's next'.\n"
            "4. For each major topic, synthesize coverage from multiple sources.\n"
            "5. Note any stories where sources disagree or offer contrasting angles.\n"
            "6. Close with a brief 'Tomorrow preview' of what to expect.\n\n"
            "Tone: Analytical, forward-looking. Help the reader connect the dots."
        )

    @mcp.prompt()
    def topic_deep_dive(topic: str) -> str:
        """Structured prompt for deep exploration of a specific topic.

        Args:
            topic: The topic to investigate (e.g., "AI regulation", "climate finance").
        """
        return (
            f"You are investigating the topic: {topic}\n\n"
            "Steps:\n"
            f"1. Call search_articles('{topic}', limit=20) to find relevant articles.\n"
            "2. Call cluster_articles() on the returned IDs to find sub-themes.\n"
            "3. For each cluster, call synthesize_topic() to merge perspectives.\n"
            "4. Call detect_trends() to see if this topic is emerging or fading.\n"
            "5. For key articles, call explain_relevance() to understand user fit.\n\n"
            "Output structure:\n"
            "- Executive summary (3 sentences)\n"
            "- Key developments (chronological)\n"
            "- Source landscape (who covers this, from what angle)\n"
            "- Trend direction (accelerating, stable, fading)\n"
            "- Open questions the coverage doesn't answer\n"
            "- Recommended next reads (top 3 articles with IDs)\n\n"
            "Be specific. Cite article IDs. Distinguish facts from interpretation."
        )
