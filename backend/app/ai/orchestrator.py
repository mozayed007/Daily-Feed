"""AI Orchestrator - Replaces the legacy AgentLoop with pydantic-ai + pydantic-graph.

Provides a unified interface that the API routes use, delegating to either
individual agents or full graph workflows depending on the task.
"""

import logging
from typing import Any, Dict, List, Optional

from app.ai.agents import (
    cluster_articles,
    critique_summary,
    reason_digest_inclusion,
    summarize_article,
    synthesize_multi_source,
    detect_trends,
)
from app.ai.graphs import (
    get_article_processing_graph,
    get_digest_generation_graph,
    get_full_pipeline_graph,
)
from app.ai.llm import get_available_providers
from app.core.personalization import get_personalization_engine
from app.database import ArticleModel
from app.models.user import UserPreferencesModel

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """High-level orchestrator for all AI operations in Daily Feed.

    This replaces the old AgentLoop and provides:
    - Agent-based operations (single-shot pydantic-ai agents)
    - Graph-based workflows (parallel pydantic-graph execution)
    - Personalization-aware digest generation
    - Trend detection and multi-source synthesis
    """

    def __init__(self):
        self._article_graph = None
        self._digest_graph = None
        self._pipeline_graph = None

    # ── Tool-like interface (mirrors old AgentLoop) ────────────────────────

    async def summarize(self, article_id: int, style: str = "concise") -> Dict[str, Any]:
        """Summarize a single article using pydantic-ai."""
        from app.database import Database
        from sqlalchemy import select

        async with Database.get_session() as db:
            result = await db.execute(
                select(ArticleModel).where(ArticleModel.id == article_id)
            )
            article = result.scalar_one_or_none()
            if not article:
                return {"success": False, "error": f"Article {article_id} not found"}

            summary = await summarize_article(
                title=article.title,
                content=article.content or "",
                style=style,
            )

            article.summary = summary.summary
            article.category = summary.category
            article.sentiment = summary.sentiment
            article.key_points = summary.key_points
            article.reading_time = summary.reading_time
            article.is_processed = True
            await db.commit()

            return {
                "success": True,
                "data": summary.model_dump(),
                "message": f"Summarized article {article_id}",
            }

    async def critique(self, article_id: int) -> Dict[str, Any]:
        """Critique a summary using pydantic-ai."""
        from app.database import Database
        from sqlalchemy import select

        async with Database.get_session() as db:
            result = await db.execute(
                select(ArticleModel).where(ArticleModel.id == article_id)
            )
            article = result.scalar_one_or_none()
            if not article or not article.summary:
                return {
                    "success": False,
                    "error": f"Article {article_id} has no summary to critique",
                }

            critique = await critique_summary(
                title=article.title,
                content=article.content or "",
                summary=article.summary,
                key_points=article.key_points,
            )

            article.critic_score = critique.overall_score
            await db.commit()

            return {
                "success": critique.overall_score >= 7,
                "data": critique.model_dump(),
                "message": f"Critique score: {critique.overall_score}/10",
            }

    async def cluster(self, article_ids: List[int]) -> Dict[str, Any]:
        """Cluster articles by topic using AI."""
        from app.database import Database
        from sqlalchemy import select

        async with Database.get_session() as db:
            result = await db.execute(
                select(ArticleModel).where(ArticleModel.id.in_(article_ids))
            )
            articles = result.scalars().all()

        texts = [
            f"{a.title}. {a.summary or a.content[:200]}"
            for a in articles
        ]
        ids = [a.id for a in articles]

        clusters = await cluster_articles(texts, ids)
        return {
            "success": True,
            "data": [c.model_dump() for c in clusters],
            "message": f"Found {len(clusters)} clusters",
        }

    async def synthesize(self, topic: str, article_ids: List[int]) -> Dict[str, Any]:
        """Synthesize multiple sources on a topic."""
        from app.database import Database
        from sqlalchemy import select

        async with Database.get_session() as db:
            result = await db.execute(
                select(ArticleModel).where(ArticleModel.id.in_(article_ids))
            )
            articles = result.scalars().all()

        article_dicts = [
            {
                "source": a.source,
                "title": a.title,
                "summary": a.summary or "",
                "key_points": a.key_points or [],
            }
            for a in articles
        ]

        synthesis = await synthesize_multi_source(topic, article_dicts)
        return {
            "success": True,
            "data": synthesis.model_dump(),
            "message": f"Synthesized {len(article_dicts)} sources on '{topic}'",
        }

    async def detect_trends(self, article_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Detect trends from articles."""
        from app.database import Database
        from sqlalchemy import select

        async with Database.get_session() as db:
            if article_ids:
                result = await db.execute(
                    select(ArticleModel).where(ArticleModel.id.in_(article_ids))
                )
            else:
                from datetime import datetime, timezone, timedelta
                cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
                result = await db.execute(
                    select(ArticleModel)
                    .where(ArticleModel.is_processed == True)
                    .where(ArticleModel.fetched_at >= cutoff)
                    .limit(50)
                )
            articles = result.scalars().all()

        texts = [
            f"{a.title}. {a.summary or a.content[:200]}"
            for a in articles
        ]

        trend_list = await detect_trends(texts)
        return {
            "success": True,
            "data": [t.model_dump() for t in trend_list.trends],
            "message": f"Detected {len(trend_list.trends)} trends",
        }

    async def reason_inclusion(
        self,
        article_id: int,
        user_preferences: UserPreferencesModel,
    ) -> Dict[str, Any]:
        """Explain why an article was included in a personalized digest."""
        from app.database import Database
        from sqlalchemy import select

        async with Database.get_session() as db:
            result = await db.execute(
                select(ArticleModel).where(ArticleModel.id == article_id)
            )
            article = result.scalar_one_or_none()
            if not article:
                return {"success": False, "error": "Article not found"}

            interests = list((user_preferences.topic_interests or {}).keys())
            sources = list((user_preferences.source_preferences or {}).keys())

            reasoning = await reason_digest_inclusion(
                article_title=article.title,
                article_summary=article.summary or "",
                article_category=article.category or "General",
                user_interests=interests,
                user_sources=sources,
            )

            return {
                "success": True,
                "data": reasoning.model_dump(),
                "message": reasoning.inclusion_reason,
            }

    # ── Graph-based workflows ────────────────────────────────────────────────

    async def run_article_processing(self) -> Dict[str, Any]:
        """Run the full article processing graph (parallel summarize + critique + memory)."""
        graph = get_article_processing_graph()
        return await graph.run()

    async def run_digest_generation(self) -> Dict[str, Any]:
        """Run the digest generation graph (cluster + synthesize + rank + deliver)."""
        graph = get_digest_generation_graph()
        return await graph.run()

    async def run_full_pipeline(self) -> Dict[str, Any]:
        """Run the complete pipeline graph (fetch -> process -> digest)."""
        graph = get_full_pipeline_graph()
        return await graph.run()

    # ── Pipeline entry point (mirrors old AgentLoop.run_pipeline) ────────────

    async def run_pipeline(self, task_type: str, **params) -> Dict[str, Any]:
        """Run a named pipeline task.

        Maps old task types to new graph/agent workflows.
        """
        if task_type == "fetch":
            from app.tools.fetch_tool import FetchTool
            tool = FetchTool()
            result = await tool.execute(**params)
            return {
                "success": result.success,
                "data": result.data,
                "message": result.message,
            }

        elif task_type == "process":
            return await self.run_article_processing()

        elif task_type == "digest":
            return await self.run_digest_generation()

        elif task_type == "full":
            return await self.run_full_pipeline()

        elif task_type == "memory_sync":
            from app.core.memory import get_memory_store
            memory = get_memory_store()
            stats = memory.get_stats()
            return {
                "success": True,
                "data": stats,
                "message": f"Memory contains {stats['total_units']} units",
            }

        elif task_type == "trends":
            return await self.detect_trends()

        elif task_type == "cluster":
            article_ids = params.get("article_ids", [])
            return await self.cluster(article_ids)

        elif task_type == "synthesize":
            topic = params.get("topic", "")
            article_ids = params.get("article_ids", [])
            return await self.synthesize(topic, article_ids)

        else:
            return {"error": f"Unknown pipeline type: {task_type}"}

    # ── Utility ────────────────────────────────────────────────────────────

    async def get_llm_status(self) -> Dict[str, Any]:
        """Get LLM provider status."""
        providers = await get_available_providers()
        return {
            "litellm_available": providers.get("litellm", {}).get("available", False),
            "providers": {k: v for k, v in providers.items() if k != "litellm"},
        }


# ── Singleton ───────────────────────────────────────────────────────────────

_orchestrator: Optional[AIOrchestrator] = None


def get_orchestrator() -> AIOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIOrchestrator()
    return _orchestrator
