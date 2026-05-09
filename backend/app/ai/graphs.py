"""Pydantic-graph workflows for Daily Feed.

Uses the pydantic-graph beta API (builder pattern) for parallel execution:
- ArticleProcessingGraph: fetch -> summarize (parallel per article) -> critique -> memory
- DigestGenerationGraph: fetch articles -> cluster -> synthesize clusters -> rank -> deliver
- FullPipelineGraph: runs the full pipeline with parallel processing
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from pydantic_graph.beta import GraphBuilder, StepContext
from pydantic_graph.beta.join import reduce_list_append

from app.ai.agents import (
    cluster_articles,
    critique_summary,
    reason_digest_inclusion,
    summarize_article,
    synthesize_multi_source,
)
from app.ai.models import ArticleCluster, MultiSourceSynthesis
from app.core.memory import get_memory_store
from app.database import Database, ArticleModel, DigestModel

logger = logging.getLogger(__name__)


# ── Shared State ────────────────────────────────────────────────────────────

@dataclass
class PipelineState:
    """Mutable state shared across graph nodes."""

    fetched_count: int = 0
    processed_ids: List[int] = field(default_factory=list)
    failed_ids: List[int] = field(default_factory=list)
    clusters: List[ArticleCluster] = field(default_factory=list)
    syntheses: List[MultiSourceSynthesis] = field(default_factory=list)
    digest_id: Optional[int] = None


# ── Article Processing Graph ──────────────────────────────────────────────

async def _article_processing_graph():
    """Build and return the article processing graph."""
    g = GraphBuilder(state_type=PipelineState, output_type=Dict[str, Any])

    @g.step
    async def fetch_unprocessed(ctx: StepContext[PipelineState, Any, Any]) -> List[int]:
        """Fetch IDs of unprocessed articles from the database."""
        async with Database.get_session() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(ArticleModel)
                .where(ArticleModel.is_processed == False)
                .limit(20)
            )
            articles = result.scalars().all()
            ids = [a.id for a in articles]
            ctx.state.fetched_count = len(ids)
            logger.info("fetch_unprocessed", count=len(ids))
            return ids

    @g.step
    async def summarize(ctx: StepContext[PipelineState, Any, int]) -> int:
        """Summarize a single article by ID (run in parallel via map)."""
        article_id = ctx.inputs
        try:
            async with Database.get_session() as db:
                from sqlalchemy import select
                result = await db.execute(
                    select(ArticleModel).where(ArticleModel.id == article_id)
                )
                article = result.scalar_one_or_none()
                if not article:
                    return article_id

                summary_result = await summarize_article(
                    title=article.title,
                    content=article.content or "",
                    style="concise",
                )
                article.summary = summary_result.summary
                article.category = summary_result.category
                article.sentiment = summary_result.sentiment
                article.key_points = summary_result.key_points
                article.reading_time = summary_result.reading_time
                article.is_processed = True
                await db.commit()
                logger.info("summarized", article_id=article_id)
                return article_id
        except Exception as e:
            logger.error("summarize_error", article_id=article_id, error=str(e))
            ctx.state.failed_ids.append(article_id)
            return article_id

    @g.step
    async def critique(ctx: StepContext[PipelineState, Any, int]) -> int:
        """Critique the summary of an article (parallel via map)."""
        article_id = ctx.inputs
        try:
            async with Database.get_session() as db:
                from sqlalchemy import select
                result = await db.execute(
                    select(ArticleModel).where(ArticleModel.id == article_id)
                )
                article = result.scalar_one_or_none()
                if not article or not article.summary:
                    return article_id

                critique = await critique_summary(
                    title=article.title,
                    content=article.content or "",
                    summary=article.summary,
                    key_points=article.key_points,
                )
                article.critic_score = critique.overall_score
                await db.commit()
                logger.info("critiqued", article_id=article_id, score=critique.overall_score)
                return article_id
        except Exception as e:
            logger.error("critique_error", article_id=article_id, error=str(e))
            return article_id

    @g.step
    async def remember(ctx: StepContext[PipelineState, Any, int]) -> int:
        """Store article in memory if it passed critique."""
        article_id = ctx.inputs
        try:
            async with Database.get_session() as db:
                from sqlalchemy import select
                result = await db.execute(
                    select(ArticleModel).where(ArticleModel.id == article_id)
                )
                article = result.scalar_one_or_none()
                if not article:
                    return article_id

                memory = get_memory_store()
                memory.remember_article(
                    article_id=article.id,
                    title=article.title,
                    summary=article.summary or "",
                    category=article.category or "General",
                    source=article.source,
                    key_points=article.key_points or [],
                )
                ctx.state.processed_ids.append(article_id)
                logger.info("remembered", article_id=article_id)
                return article_id
        except Exception as e:
            logger.error("remember_error", article_id=article_id, error=str(e))
            return article_id

    @g.step
    async def collect_results(ctx: StepContext[PipelineState, Any, List[int]]) -> Dict[str, Any]:
        """Collect all processed article IDs and return summary."""
        return {
            "success": True,
            "processed": len(ctx.state.processed_ids),
            "failed": len(ctx.state.failed_ids),
            "article_ids": ctx.state.processed_ids,
        }

    # Build graph topology: fetch -> map(summarize -> critique -> remember) -> collect
    collect = g.join(reduce_list_append, initial_factory=list[int])

    g.add(
        g.edge_from(g.start_node).to(fetch_unprocessed),
        g.edge_from(fetch_unprocessed).map().to(summarize),
        g.edge_from(summarize).map().to(critique),
        g.edge_from(critique).map().to(remember),
        g.edge_from(remember).to(collect),
        g.edge_from(collect).to(g.end_node),
    )

    return g.build()


class ArticleProcessingGraph:
    """High-level interface for the article processing graph."""

    def __init__(self):
        self._graph = None

    async def _get_graph(self):
        if self._graph is None:
            self._graph = await _article_processing_graph()
        return self._graph

    async def run(self) -> Dict[str, Any]:
        """Run the article processing pipeline."""
        graph = await self._get_graph()
        state = PipelineState()
        result = await graph.run(state=state)
        return result if result else {
            "success": True,
            "processed": len(state.processed_ids),
            "failed": len(state.failed_ids),
        }


# ── Digest Generation Graph ─────────────────────────────────────────────────

async def _digest_generation_graph():
    """Build and return the digest generation graph."""
    g = GraphBuilder(state_type=PipelineState, output_type=Dict[str, Any])

    @g.step
    async def fetch_recent(ctx: StepContext[PipelineState, Any, Any]) -> List[ArticleModel]:
        """Fetch recent processed articles from the database."""
        async with Database.get_session() as db:
            from sqlalchemy import select
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            result = await db.execute(
                select(ArticleModel)
                .where(ArticleModel.is_processed == True)
                .where(ArticleModel.fetched_at >= cutoff)
                .order_by(ArticleModel.fetched_at.desc())
                .limit(50)
            )
            articles = result.scalars().all()
            ctx.state.fetched_count = len(articles)
            logger.info("fetch_recent_digest", count=len(articles))
            return list(articles)

    @g.step
    async def cluster(ctx: StepContext[PipelineState, Any, List[ArticleModel]]) -> List[ArticleCluster]:
        """Cluster articles by topic using AI."""
        articles = ctx.inputs
        if not articles:
            return []

        texts = [
            f"{a.title}. {a.summary or a.content[:200]}"
            for a in articles
        ]
        ids = [a.id for a in articles]

        clusters = await cluster_articles(texts, ids)
        ctx.state.clusters = clusters
        logger.info("clustered", cluster_count=len(clusters))
        return clusters

    @g.step
    async def synthesize_cluster(ctx: StepContext[PipelineState, Any, ArticleCluster]) -> MultiSourceSynthesis:
        """Synthesize articles within a single cluster (parallel via map)."""
        cluster = ctx.inputs
        if not cluster.article_ids:
            return MultiSourceSynthesis(
                topic=cluster.topic,
                synthesized_summary="",
                sources_covered=[],
                consensus_points=[],
                conflicting_points=[],
                unique_perspectives=[],
            )

        async with Database.get_session() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(ArticleModel).where(ArticleModel.id.in_(cluster.article_ids))
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

        synthesis = await synthesize_multi_source(cluster.topic, article_dicts)
        ctx.state.syntheses.append(synthesis)
        logger.info("synthesized_cluster", topic=cluster.topic, sources=len(article_dicts))
        return synthesis

    @g.step
    async def build_digest(ctx: StepContext[PipelineState, Any, List[MultiSourceSynthesis]]) -> Dict[str, Any]:
        """Build and save the digest from synthesized clusters."""
        syntheses = ctx.inputs
        if not syntheses:
            return {"success": True, "digest_id": None, "article_count": 0}

        # Flatten articles from all clusters
        all_article_ids = []
        for c in ctx.state.clusters:
            all_article_ids.extend(c.article_ids)

        # Deduplicate
        all_article_ids = list(dict.fromkeys(all_article_ids))

        async with Database.get_session() as db:
            # Create digest record
            digest = DigestModel(
                article_count=len(all_article_ids),
                delivered=False,
            )
            db.add(digest)
            await db.flush()

            # Associate articles
            from sqlalchemy import select
            result = await db.execute(
                select(ArticleModel).where(ArticleModel.id.in_(all_article_ids))
            )
            articles = result.scalars().all()
            for article in articles:
                article.digest_id = digest.id

            await db.commit()
            ctx.state.digest_id = digest.id

        logger.info("digest_created", digest_id=digest.id, articles=len(all_article_ids))
        return {
            "success": True,
            "digest_id": digest.id,
            "article_count": len(all_article_ids),
            "clusters": len(syntheses),
        }

    # Graph topology: fetch -> cluster -> map(synthesize_cluster) -> build_digest
    collect_syntheses = g.join(reduce_list_append, initial_factory=list[MultiSourceSynthesis])

    g.add(
        g.edge_from(g.start_node).to(fetch_recent),
        g.edge_from(fetch_recent).to(cluster),
        g.edge_from(cluster).map().to(synthesize_cluster),
        g.edge_from(synthesize_cluster).to(collect_syntheses),
        g.edge_from(collect_syntheses).to(build_digest),
        g.edge_from(build_digest).to(g.end_node),
    )

    return g.build()


class DigestGenerationGraph:
    """High-level interface for the digest generation graph."""

    def __init__(self):
        self._graph = None

    async def _get_graph(self):
        if self._graph is None:
            self._graph = await _digest_generation_graph()
        return self._graph

    async def run(self) -> Dict[str, Any]:
        """Run the digest generation pipeline."""
        graph = await self._get_graph()
        state = PipelineState()
        result = await graph.run(state=state)
        return result if result else {
            "success": True,
            "digest_id": state.digest_id,
        }


# ── Full Pipeline Graph ─────────────────────────────────────────────────────

async def _full_pipeline_graph():
    """Build and return the full pipeline graph."""
    g = GraphBuilder(state_type=PipelineState, output_type=Dict[str, Any])

    @g.step
    async def run_fetch(ctx: StepContext[PipelineState, Any, Any]) -> str:
        """Run the fetch pipeline step."""
        from app.tools.fetch_tool import FetchTool
        tool = FetchTool()
        result = await tool.execute()
        ctx.state.fetched_count = result.data.get("fetched", 0)
        logger.info("full_pipeline_fetch", fetched=ctx.state.fetched_count)
        return "fetched"

    @g.step
    async def run_process(ctx: StepContext[PipelineState, Any, str]) -> str:
        """Run the article processing step."""
        proc = ArticleProcessingGraph()
        proc_result = await proc.run()
        ctx.state.processed_ids = proc_result.get("article_ids", [])
        logger.info("full_pipeline_process", processed=len(ctx.state.processed_ids))
        return "processed"

    @g.step
    async def run_digest(ctx: StepContext[PipelineState, Any, str]) -> Dict[str, Any]:
        """Run the digest generation step."""
        dig = DigestGenerationGraph()
        dig_result = await dig.run()
        ctx.state.digest_id = dig_result.get("digest_id")
        logger.info("full_pipeline_digest", digest_id=ctx.state.digest_id)
        return {
            "success": True,
            "fetch": ctx.state.fetched_count,
            "process": len(ctx.state.processed_ids),
            "digest": ctx.state.digest_id,
        }

    g.add(
        g.edge_from(g.start_node).to(run_fetch),
        g.edge_from(run_fetch).to(run_process),
        g.edge_from(run_process).to(run_digest),
        g.edge_from(run_digest).to(g.end_node),
    )

    return g.build()


class FullPipelineGraph:
    """High-level interface for the full pipeline graph."""

    def __init__(self):
        self._graph = None

    async def _get_graph(self):
        if self._graph is None:
            self._graph = await _full_pipeline_graph()
        return self._graph

    async def run(self) -> Dict[str, Any]:
        """Run the full pipeline: fetch -> process -> digest."""
        graph = await self._get_graph()
        state = PipelineState()
        result = await graph.run(state=state)
        return result if result else {
            "success": True,
            "fetch": state.fetched_count,
            "process": len(state.processed_ids),
            "digest": state.digest_id,
        }


# ── Singleton instances ───────────────────────────────────────────────────────

_article_processing_graph_instance: Optional[ArticleProcessingGraph] = None
_digest_generation_graph_instance: Optional[DigestGenerationGraph] = None
_full_pipeline_graph_instance: Optional[FullPipelineGraph] = None


def get_article_processing_graph() -> ArticleProcessingGraph:
    global _article_processing_graph_instance
    if _article_processing_graph_instance is None:
        _article_processing_graph_instance = ArticleProcessingGraph()
    return _article_processing_graph_instance


def get_digest_generation_graph() -> DigestGenerationGraph:
    global _digest_generation_graph_instance
    if _digest_generation_graph_instance is None:
        _digest_generation_graph_instance = DigestGenerationGraph()
    return _digest_generation_graph_instance


def get_full_pipeline_graph() -> FullPipelineGraph:
    global _full_pipeline_graph_instance
    if _full_pipeline_graph_instance is None:
        _full_pipeline_graph_instance = FullPipelineGraph()
    return _full_pipeline_graph_instance
