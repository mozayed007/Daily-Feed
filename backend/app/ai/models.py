"""Structured output models for pydantic-ai agents."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SummaryResult(BaseModel):
    """Structured article summary output."""

    summary: str = Field(
        description="Concise, accurate summary of the article in 2-4 sentences"
    )
    category: str = Field(
        description="Category: Technology, Business, Science, Politics, Health, Entertainment, Sports, AI/ML, Finance, or General"
    )
    sentiment: str = Field(
        description="Overall sentiment: Positive, Negative, or Neutral"
    )
    key_points: List[str] = Field(
        description="3-5 key points or takeaways from the article",
        min_length=1,
        max_length=5,
    )
    reading_time: int = Field(
        description="Estimated reading time in minutes",
        ge=1,
        le=60,
    )


class CritiqueResult(BaseModel):
    """Structured summary critique output."""

    accuracy: int = Field(description="Accuracy score 1-10", ge=1, le=10)
    completeness: int = Field(description="Completeness score 1-10", ge=1, le=10)
    clarity: int = Field(description="Clarity score 1-10", ge=1, le=10)
    bias: int = Field(
        description="Lack-of-bias score 1-10 (higher = less biased)", ge=1, le=10
    )
    overall_score: int = Field(description="Overall quality score 1-10", ge=1, le=10)
    issues: List[str] = Field(description="Specific issues found, if any")
    suggestions: str = Field(
        description="Concrete suggestions for improvement, or 'None' if excellent"
    )


class ArticleCluster(BaseModel):
    """A cluster of related articles on a common topic."""

    cluster_id: str = Field(description="Unique cluster identifier (e.g., 'c-1')")
    topic: str = Field(description="Main topic or theme of the cluster")
    summary: str = Field(description="Brief summary of what the cluster covers")
    article_ids: List[int] = Field(description="IDs of articles in this cluster")
    confidence: float = Field(
        description="Clustering confidence 0.0-1.0", ge=0, le=1
    )


class ClusterList(BaseModel):
    """Wrapper for returning multiple clusters from an agent."""

    clusters: List[ArticleCluster] = Field(description="Discovered article clusters")


class MultiSourceSynthesis(BaseModel):
    """Synthesis of multiple sources covering the same topic."""

    topic: str = Field(description="The common topic being covered")
    synthesized_summary: str = Field(
        description="Unified narrative synthesizing all sources into one coherent story"
    )
    sources_covered: List[str] = Field(
        description="Names of news sources included in the synthesis"
    )
    consensus_points: List[str] = Field(
        description="Points where all or most sources agree"
    )
    conflicting_points: List[str] = Field(
        description="Points where sources disagree or present conflicting information"
    )
    unique_perspectives: List[str] = Field(
        description="Unique angles or perspectives from individual sources"
    )


class DigestReasoning(BaseModel):
    """Reasoning for why an article was included in a personalized digest."""

    article_id: int = Field(description="Article ID")
    inclusion_reason: str = Field(
        description="Clear explanation of why this article matches the user's interests"
    )
    relevance_score: float = Field(
        description="Personalized relevance score 0.0-1.0", ge=0, le=1
    )
    personalized_for: str = Field(
        description="Specific user interest or preference this article addresses"
    )
    key_insight: str = Field(
        description="The single most important insight the user should take away"
    )


class TrendResult(BaseModel):
    """Detected trend from a set of articles."""

    topic: str = Field(description="The trending topic or theme")
    article_count: int = Field(description="Number of articles on this topic")
    trend_direction: str = Field(
        description="Trend direction: rising, stable, falling, or breaking"
    )
    summary: str = Field(description="Brief summary of the trend and its significance")
    top_sources: List[str] = Field(
        description="Sources that most actively cover this trend"
    )
    urgency: str = Field(
        description="Urgency level: high, medium, or low"
    )


class TrendList(BaseModel):
    """Wrapper for returning multiple trends."""

    trends: List[TrendResult] = Field(description="Detected trends")
