"""Personalization Engine - Core recommendation algorithm.

This module implements the scoring and ranking algorithms that power
personalized content recommendations for each user.
"""

import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from app.models.user import UserPreferencesModel
from app.database import ArticleModel
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ScoredArticle:
    """Article with personalization score."""
    article: ArticleModel
    score: float
    score_breakdown: Dict[str, float]


class PersonalizationEngine:
    """Core recommendation engine for personalized content.
    
    Uses a multi-factor scoring algorithm that considers:
    - Topic interest alignment (35%)
    - Source preference (20%)
    - Content freshness (25%, adjustable)
    - Content quality (15%)
    - Diversity boost (5%)
    """
    
    # Default weights (can be adjusted per user)
    DEFAULT_WEIGHTS = {
        "topic": 0.35,
        "source": 0.20,
        "freshness": 0.25,
        "quality": 0.15,
        "diversity": 0.05,
    }
    
    # Freshness half-life in hours
    FRESHNESS_HALFLIFE = 24.0
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """Initialize with optional custom weights."""
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self._topic_history: Dict[str, int] = {}  # Track topic frequency for diversity
        
        logger.info(
            "personalization_engine_initialized",
            weights=self.weights
        )
    
    def rank_articles(
        self,
        articles: List[ArticleModel],
        preferences: UserPreferencesModel,
        limit: Optional[int] = None
    ) -> List[ScoredArticle]:
        """Rank articles for a specific user.
        
        Args:
            articles: List of candidate articles
            preferences: User's personalization preferences
            limit: Maximum number of articles to return
            
        Returns:
            List of ScoredArticle, sorted by score descending
        """
        if not articles:
            return []
        
        # Reset topic history for this ranking session
        self._topic_history = {}
        
        # Score all articles
        scored = []
        for article in articles:
            score, breakdown = self._calculate_score(article, preferences)
            scored.append(ScoredArticle(article, score, breakdown))
        
        # Sort by score descending
        scored.sort(key=lambda x: x.score, reverse=True)
        
        # Apply limit if specified
        if limit:
            scored = scored[:limit]
        
        logger.info(
            "articles_ranked",
            total_candidates=len(articles),
            returned=len(scored),
            top_score=scored[0].score if scored else 0
        )
        
        return scored
    
    def _calculate_score(
        self,
        article: ArticleModel,
        preferences: UserPreferencesModel
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate personalization score for an article.
        
        Returns:
            Tuple of (final_score, score_breakdown_dict)
        """
        # Get base scores
        topic_score = self._calculate_topic_score(article, preferences)
        source_score = self._calculate_source_score(article, preferences)
        freshness_score = self._calculate_freshness_score(article, preferences)
        quality_score = self._calculate_quality_score(article)
        diversity_score = self._calculate_diversity_score(article, preferences)
        
        # Adjust freshness weight based on user preference
        freshness_weight = self._get_freshness_weight(preferences.freshness_preference)
        
        # Calculate weighted final score
        final_score = (
            topic_score * self.weights["topic"] +
            source_score * self.weights["source"] +
            freshness_score * freshness_weight +
            quality_score * self.weights["quality"] +
            diversity_score * preferences.diversity_boost
        )
        
        # Update topic history for diversity calculation
        topic = article.category or "General"
        self._topic_history[topic] = self._topic_history.get(topic, 0) + 1
        
        breakdown = {
            "topic": round(topic_score, 3),
            "source": round(source_score, 3),
            "freshness": round(freshness_score, 3),
            "quality": round(quality_score, 3),
            "diversity": round(diversity_score, 3),
            "final": round(final_score, 3),
        }
        
        return final_score, breakdown
    
    def _calculate_topic_score(
        self,
        article: ArticleModel,
        preferences: UserPreferencesModel
    ) -> float:
        """Calculate topic interest match score (0-1)."""
        topic = article.category or "General"
        
        # Check if topic is excluded
        if topic in (preferences.exclude_topics or []):
            return 0.0
        
        # Get user interest in this topic
        interests = preferences.topic_interests or {}
        return interests.get(topic, 0.5)  # Default to neutral
    
    def _calculate_source_score(
        self,
        article: ArticleModel,
        preferences: UserPreferencesModel
    ) -> float:
        """Calculate source preference score (0-1)."""
        source = article.source or "Unknown"
        
        # Check if source is excluded
        if source in (preferences.exclude_sources or []):
            return 0.0
        
        # Get user preference for this source
        source_prefs = preferences.source_preferences or {}
        return source_prefs.get(source, 0.5)  # Default to neutral
    
    def _calculate_freshness_score(
        self,
        article: ArticleModel,
        preferences: UserPreferencesModel
    ) -> float:
        """Calculate recency score using exponential decay.
        
        Score = exp(-age_hours / half_life)
        - 0 hours old: 1.0
        - 24 hours old: 0.5
        - 48 hours old: 0.25
        """
        if not article.published_at:
            return 0.5  # Neutral for unknown dates
        
        age = datetime.now(timezone.utc).replace(tzinfo=None) - article.published_at
        age_hours = age.total_seconds() / 3600
        
        # Exponential decay
        score = math.exp(-age_hours / self.FRESHNESS_HALFLIFE)
        
        return min(1.0, max(0.0, score))
    
    def _calculate_quality_score(self, article: ArticleModel) -> float:
        """Calculate content quality score (0-1).
        
        Uses critique score if available, otherwise estimates from content.
        """
        # If we have a critique score, use it
        if hasattr(article, 'critique_score') and article.critique_score:
            return article.critique_score / 10.0
        
        # Estimate from content length and structure
        score = 0.5  # Base score
        
        if article.content:
            content_length = len(article.content)
            # Prefer medium-length articles (500-2000 words ~ 3000-12000 chars)
            if 3000 <= content_length <= 12000:
                score += 0.2
            elif content_length > 500:  # At least some substance
                score += 0.1
        
        # Bonus for having a summary
        if article.summary:
            score += 0.1
        
        # Bonus for having key points extracted
        if hasattr(article, 'key_points') and article.key_points:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_diversity_score(
        self,
        article: ArticleModel,
        preferences: UserPreferencesModel
    ) -> float:
        """Calculate diversity boost to avoid filter bubble.
        
        Rewards underrepresented topics in the current selection.
        """
        topic = article.category or "General"
        
        # Count how many times this topic has appeared
        topic_count = self._topic_history.get(topic, 0)
        
        # Inverse frequency - less common topics get higher score
        if topic_count == 0:
            return 1.0  # New topic, max boost
        else:
            # Decaying boost: 1.0, 0.5, 0.33, 0.25...
            return 1.0 / (topic_count + 1)
    
    def _get_freshness_weight(self, preference: str) -> float:
        """Get freshness weight based on user preference."""
        weights = {
            "breaking": 0.40,  # Prioritize very fresh content
            "daily": 0.25,     # Balanced
            "weekly": 0.10,    # Don't care as much about recency
        }
        return weights.get(preference, 0.25)
    
    def filter_articles(
        self,
        articles: List[ArticleModel],
        preferences: UserPreferencesModel
    ) -> List[ArticleModel]:
        """Filter out articles based on user exclusions.
        
        Args:
            articles: List of articles to filter
            preferences: User preferences with exclusions
            
        Returns:
            Filtered list of articles
        """
        filtered = []
        excluded_count = {"topic": 0, "source": 0}
        
        for article in articles:
            topic = article.category or "General"
            source = article.source or "Unknown"
            
            # Check exclusions
            if topic in (preferences.exclude_topics or []):
                excluded_count["topic"] += 1
                continue
            
            if source in (preferences.exclude_sources or []):
                excluded_count["source"] += 1
                continue
            
            filtered.append(article)
        
        logger.info(
            "articles_filtered",
            input_count=len(articles),
            output_count=len(filtered),
            excluded=excluded_count
        )
        
        return filtered


class UserModelTrainer:
    """Updates user preferences based on interactions.
    
    Implements online learning to adapt to user behavior over time.
    """
    
    # Learning rates
    TOPIC_REINFORCE_RATE = 0.05
    TOPIC_PENALTY_RATE = 0.08  # Penalize more than reward
    SOURCE_REINFORCE_RATE = 0.03
    MIN_INTEREST = 0.1
    MAX_INTEREST = 1.0
    
    def __init__(self):
        self.logger = get_logger(__name__, component="UserModelTrainer")
    
    def update_from_interaction(
        self,
        preferences: UserPreferencesModel,
        article: ArticleModel,
        rating: int = 0,
        read_duration: int = 0,
        saved: bool = False,
        dismissed: bool = False
    ) -> Dict[str, any]:
        """Update user model based on interaction.
        
        Args:
            preferences: User's current preferences
            article: The article that was interacted with
            rating: Explicit rating (-1, 0, 1)
            read_duration: Seconds spent reading
            saved: Whether article was saved
            dismissed: Whether article was dismissed
            
        Returns:
            Dict with changes made
        """
        changes = {
            "topics": {},
            "sources": {},
        }
        
        topic = article.category or "General"
        source = article.source or "Unknown"
        
        # Determine signal strength
        positive_signals = self._calculate_positive_signals(
            rating, read_duration, saved
        )
        negative_signals = self._calculate_negative_signals(
            rating, read_duration, dismissed
        )
        
        # Update topic interests
        if positive_signals > 0:
            delta = self.TOPIC_REINFORCE_RATE * positive_signals
            old_value = self._update_topic_interest(preferences, topic, delta)
            changes["topics"][topic] = {"old": old_value, "new": old_value + delta, "delta": +delta}
            
        elif negative_signals > 0:
            delta = self.TOPIC_PENALTY_RATE * negative_signals
            old_value = self._update_topic_interest(preferences, topic, -delta)
            changes["topics"][topic] = {"old": old_value, "new": old_value - delta, "delta": -delta}
        
        # Update source preferences
        if positive_signals > 0:
            delta = self.SOURCE_REINFORCE_RATE * positive_signals
            old_value = self._update_source_preference(preferences, source, delta)
            changes["sources"][source] = {"old": old_value, "new": old_value + delta, "delta": +delta}
            
        elif negative_signals > 0 and rating < 0:
            # Only penalize source on explicit dislike
            delta = self.SOURCE_REINFORCE_RATE
            old_value = self._update_source_preference(preferences, source, -delta)
            changes["sources"][source] = {"old": old_value, "new": old_value - delta, "delta": -delta}
        
        self.logger.info(
            "user_preferences_updated",
            user_id=preferences.user_id,
            changes=changes,
            positive_signals=positive_signals,
            negative_signals=negative_signals
        )
        
        return changes
    
    def _calculate_positive_signals(
        self,
        rating: int,
        read_duration: int,
        saved: bool
    ) -> float:
        """Calculate strength of positive signals (0-3)."""
        signals = 0.0
        
        # Explicit like
        if rating > 0:
            signals += 1.0
        
        # Read for significant time (> 1 minute)
        if read_duration > 60:
            signals += 1.0
        elif read_duration > 30:
            signals += 0.5
        
        # Saved article
        if saved:
            signals += 1.0
        
        return signals
    
    def _calculate_negative_signals(
        self,
        rating: int,
        read_duration: int,
        dismissed: bool
    ) -> float:
        """Calculate strength of negative signals (0-2)."""
        signals = 0.0
        
        # Explicit dislike
        if rating < 0:
            signals += 1.5
        
        # Quick dismissal (< 5 seconds)
        if dismissed or (0 < read_duration < 5):
            signals += 0.5
        
        return signals
    
    def _update_topic_interest(
        self,
        preferences: UserPreferencesModel,
        topic: str,
        delta: float
    ) -> float:
        """Update topic interest, keeping within bounds."""
        interests = preferences.topic_interests or {}
        current = interests.get(topic, 0.5)
        new_value = max(self.MIN_INTEREST, min(self.MAX_INTEREST, current + delta))
        interests[topic] = round(new_value, 3)
        preferences.topic_interests = interests
        return current
    
    def _update_source_preference(
        self,
        preferences: UserPreferencesModel,
        source: str,
        delta: float
    ) -> float:
        """Update source preference, keeping within bounds."""
        sources = preferences.source_preferences or {}
        current = sources.get(source, 0.5)
        new_value = max(self.MIN_INTEREST, min(self.MAX_INTEREST, current + delta))
        sources[source] = round(new_value, 3)
        preferences.source_preferences = sources
        return current
    
    def decay_old_interests(
        self,
        preferences: UserPreferencesModel,
        days: int = 30,
        decay_rate: float = 0.95
    ):
        """Decay old interests to allow preferences to evolve.
        
        Call this periodically (e.g., weekly) to gradually reduce
        weights of topics/sources that haven't been engaged with.
        """
        # Decay topic interests toward neutral (0.5)
        interests = preferences.topic_interests or {}
        for topic in list(interests.keys()):
            current = interests[topic]
            # Move toward 0.5
            new_value = 0.5 + (current - 0.5) * decay_rate
            if abs(new_value - 0.5) < 0.05:
                # Remove if close to neutral
                del interests[topic]
            else:
                interests[topic] = round(new_value, 3)
        
        # Decay source preferences similarly
        sources = preferences.source_preferences or {}
        for source in list(sources.keys()):
            current = sources[source]
            new_value = 0.5 + (current - 0.5) * decay_rate
            if abs(new_value - 0.5) < 0.05:
                del sources[source]
            else:
                sources[source] = round(new_value, 3)
        
        self.logger.info(
            "interests_decayed",
            user_id=preferences.user_id,
            decay_rate=decay_rate,
            remaining_topics=len(interests),
            remaining_sources=len(sources)
        )


# Singleton instance
_personalization_engine: Optional[PersonalizationEngine] = None
_user_model_trainer: Optional[UserModelTrainer] = None


def get_personalization_engine() -> PersonalizationEngine:
    """Get singleton personalization engine."""
    global _personalization_engine
    if _personalization_engine is None:
        _personalization_engine = PersonalizationEngine()
    return _personalization_engine


def get_user_model_trainer() -> UserModelTrainer:
    """Get singleton user model trainer."""
    global _user_model_trainer
    if _user_model_trainer is None:
        _user_model_trainer = UserModelTrainer()
    return _user_model_trainer
