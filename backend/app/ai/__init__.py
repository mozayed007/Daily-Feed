"""AI module - pydantic-ai agents and pydantic-graph workflows for Daily Feed."""

from app.ai.agents import (
    cluster_agent,
    critique_agent,
    digest_reason_agent,
    summarize_agent,
    synthesize_agent,
    trend_agent,
)
from app.ai.graphs import (
    ArticleProcessingGraph,
    DigestGenerationGraph,
    FullPipelineGraph,
)
from app.ai.llm import create_agent, get_model
from app.ai.models import (
    ArticleCluster,
    ClusterList,
    CritiqueResult,
    DigestReasoning,
    MultiSourceSynthesis,
    SummaryResult,
    TrendResult,
)
from app.ai.orchestrator import AIOrchestrator

__all__ = [
    "create_agent",
    "get_model",
    "summarize_agent",
    "critique_agent",
    "cluster_agent",
    "synthesize_agent",
    "digest_reason_agent",
    "trend_agent",
    "ArticleProcessingGraph",
    "DigestGenerationGraph",
    "FullPipelineGraph",
    "AIOrchestrator",
    "SummaryResult",
    "CritiqueResult",
    "ArticleCluster",
    "ClusterList",
    "MultiSourceSynthesis",
    "DigestReasoning",
    "TrendResult",
]
