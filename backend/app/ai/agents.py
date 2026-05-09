"""Pydantic-ai agents for Daily Feed.

Each agent is a specialized pydantic-ai Agent using structured outputs (result_type)
and backed by litellm for universal provider routing.
"""

import logging
from typing import List, Optional

from app.ai.llm import create_agent
from app.ai.models import (
    ArticleCluster,
    ClusterList,
    CritiqueResult,
    DigestReasoning,
    MultiSourceSynthesis,
    SummaryResult,
    TrendList,
)

logger = logging.getLogger(__name__)


# ── Core Agents ─────────────────────────────────────────────────────────────

summarize_agent = create_agent(
    system_prompt=(
        "You are a professional news summarizer. Create clear, accurate summaries "
        "of news articles. Focus on key facts and main points. Maintain a neutral, "
        "objective tone. Never include your own opinions. "
        "Always respond with valid JSON matching the required schema."
    ),
    result_type=SummaryResult,
    temperature=0.4,
    max_tokens=800,
)

critique_agent = create_agent(
    system_prompt=(
        "You are a quality critic evaluating news summaries. Compare summaries to "
        "original articles and rate them objectively on accuracy, completeness, "
        "clarity, and lack of bias. Be strict but fair. "
        "Always respond with valid JSON matching the required schema."
    ),
    result_type=CritiqueResult,
    temperature=0.3,
    max_tokens=600,
)

cluster_agent = create_agent(
    system_prompt=(
        "You are a content analyst. Given a list of news articles, group them into "
        "thematic clusters based on shared topics, entities, or narratives. "
        "Each cluster should have a clear topic, a brief summary, and a confidence score. "
        "Always respond with valid JSON matching the required schema."
    ),
    result_type=ClusterList,
    temperature=0.4,
    max_tokens=1500,
)

synthesize_agent = create_agent(
    system_prompt=(
        "You are a multi-source news synthesizer. Given articles from multiple sources "
        "covering the same topic, create a unified narrative that highlights consensus, "
        "conflicts, and unique perspectives across sources. "
        "Always respond with valid JSON matching the required schema."
    ),
    result_type=MultiSourceSynthesis,
    temperature=0.5,
    max_tokens=1200,
)

digest_reason_agent = create_agent(
    system_prompt=(
        "You are a personalization analyst. Given a user profile and an article, explain "
        "why this article is relevant to the user in a single clear sentence. Identify "
        "the key insight the user should take away. "
        "Always respond with valid JSON matching the required schema."
    ),
    result_type=DigestReasoning,
    temperature=0.5,
    max_tokens=400,
)

trend_agent = create_agent(
    system_prompt=(
        "You are a trend analyst. Given a batch of recent news articles, identify "
        "emerging trends, rising topics, and breaking stories. Rate urgency and "
        "direction for each trend. "
        "Always respond with valid JSON matching the required schema."
    ),
    result_type=TrendList,
    temperature=0.5,
    max_tokens=1200,
)


# ── Helper wrappers ─────────────────────────────────────────────────────────


async def summarize_article(title: str, content: str, style: str = "concise") -> SummaryResult:
    """Summarize a single article via pydantic-ai agent."""
    style_instruction = {
        "short": "Provide a very brief 1-2 sentence summary.",
        "concise": "Provide a 2-3 sentence summary.",
        "medium": "Provide a 3-4 sentence summary.",
        "long": "Provide a paragraph summary (5-6 sentences).",
    }.get(style, "Provide a 2-3 sentence summary.")

    max_content = 4000
    truncated = content[:max_content] if content else ""

    prompt = (
        f"ARTICLE TITLE: {title}\n\n"
        f"ARTICLE CONTENT:\n{truncated}\n\n"
        f"INSTRUCTIONS:\n"
        f"{style_instruction}\n"
        f"- Focus on key facts and main points\n"
        f"- Maintain a neutral, objective tone\n"
        f"- Do not include your own opinions\n"
        f"- Be accurate and faithful to the original"
    )

    result = await summarize_agent.run(prompt)
    return result.data


async def critique_summary(
    title: str,
    content: str,
    summary: str,
    key_points: Optional[List[str]] = None,
) -> CritiqueResult:
    """Critique a summary via pydantic-ai agent."""
    kp_text = "\n".join(f"- {p}" for p in (key_points or []))

    prompt = (
        f"ORIGINAL ARTICLE TITLE: {title}\n\n"
        f"ORIGINAL ARTICLE CONTENT (first 3000 chars):\n{content[:3000]}\n\n"
        f"SUMMARY TO EVALUATE:\n{summary}\n\n"
        f"KEY POINTS IN SUMMARY:\n{kp_text}\n\n"
        f"Evaluate the summary on accuracy, completeness, clarity, and bias. "
        f"Rate each criterion 1-10. Provide specific issues and suggestions."
    )

    result = await critique_agent.run(prompt)
    return result.data


async def cluster_articles(
    article_texts: List[str], article_ids: List[int]
) -> List[ArticleCluster]:
    """Cluster articles by topic via pydantic-ai agent."""
    if not article_texts:
        return []

    lines = []
    for i, (aid, text) in enumerate(zip(article_ids, article_texts)):
        lines.append(f"Article {aid}: {text[:300]}...")

    prompt = (
        "Group the following articles into thematic clusters. "
        "Return clusters with topic, summary, article IDs, and confidence.\n\n" + "\n\n".join(lines)
    )

    result = await cluster_agent.run(prompt)
    return result.data.clusters


async def synthesize_multi_source(topic: str, articles: List[dict]) -> MultiSourceSynthesis:
    """Synthesize multiple sources on a shared topic."""
    lines = []
    for a in articles:
        lines.append(
            f"Source: {a.get('source', 'Unknown')}\n"
            f"Title: {a.get('title', '')}\n"
            f"Summary: {a.get('summary', '')}\n"
            f"Key Points: {', '.join(a.get('key_points', []))}"
        )

    prompt = (
        f"TOPIC: {topic}\n\n"
        f"ARTICLES FROM MULTIPLE SOURCES:\n\n"
        + "\n---\n".join(lines)
        + "\n\nSynthesize these into a unified narrative."
    )

    result = await synthesize_agent.run(prompt)
    return result.data


async def reason_digest_inclusion(
    article_title: str,
    article_summary: str,
    article_category: str,
    user_interests: List[str],
    user_sources: List[str],
) -> DigestReasoning:
    """Reason why an article should be in a personalized digest."""
    prompt = (
        f"ARTICLE: {article_title}\n"
        f"SUMMARY: {article_summary}\n"
        f"CATEGORY: {article_category}\n\n"
        f"USER INTERESTS: {', '.join(user_interests)}\n"
        f"USER PREFERRED SOURCES: {', '.join(user_sources)}\n\n"
        f"Explain why this article is relevant to the user."
    )
    result = await digest_reason_agent.run(prompt)
    return result.data


async def detect_trends(article_texts: List[str]) -> TrendList:
    """Detect trends from a batch of articles."""
    lines = [f"- {t[:200]}..." for t in article_texts]
    prompt = "Analyze these recent news articles and identify emerging trends:\n\n" + "\n".join(
        lines
    )
    result = await trend_agent.run(prompt)
    return result.data


# ── Optional Web-Search-Enabled Agents (unstructured output) ────────────────
# These use provider-adaptive capabilities (WebSearch, WebFetch) which fall
# back to local DuckDuckGo/markdownify when the model doesn't natively support
# builtin tools.  Because Gemini cannot mix builtin tools with structured
# output, these agents return plain text and rely on prompt-based formatting.


def _search_capabilities() -> list | None:
    """Build capabilities list based on feature toggles."""
    caps = []
    from app.config import get_settings

    s = get_settings()
    if s.ENABLE_WEB_SEARCH:
        from pydantic_ai.capabilities import WebSearch

        caps.append(WebSearch())
    if s.ENABLE_URL_FETCH:
        from pydantic_ai.capabilities import WebFetch

        caps.append(WebFetch())
    return caps or None


summarize_agent_with_search = create_agent(
    system_prompt=(
        "You are a professional news summarizer with real-time web access. "
        "Create clear, accurate summaries of news articles. Focus on key facts "
        "and main points. If the article lacks context, search the web to fill "
        "gaps. Maintain a neutral, objective tone. "
        "Return your response as plain text."
    ),
    result_type=None,  # plain text (no structured output — avoids Gemini conflict)
    temperature=0.4,
    max_tokens=1200,
    capabilities=_search_capabilities(),
)

critique_agent_with_search = create_agent(
    system_prompt=(
        "You are a quality critic with web access. Evaluate news summaries "
        "against original articles and rate them objectively. If facts are "
        "questionable, verify them online. Be strict but fair. "
        "Return your response as plain text."
    ),
    result_type=None,
    temperature=0.3,
    max_tokens=1000,
    capabilities=_search_capabilities(),
)

synthesize_agent_with_search = create_agent(
    system_prompt=(
        "You are a multi-source news synthesizer with web access. Given articles "
        "from multiple sources, create a unified narrative. If coverage is thin, "
        "search for additional perspectives. Highlight consensus, conflicts, "
        "and unique angles. Return your response as plain text."
    ),
    result_type=None,
    temperature=0.5,
    max_tokens=1500,
    capabilities=_search_capabilities(),
)
