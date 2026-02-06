"""Tests for personalization engine and user models."""

import pytest
from datetime import datetime, timedelta

from app.core.personalization import (
    PersonalizationEngine, UserModelTrainer, ScoredArticle
)
from app.models.user import (
    UserModel, UserPreferencesModel, UserInteractionModel,
    UserCreate, UserPreferencesUpdate, OnboardingData
)
from app.database import ArticleModel


class TestPersonalizationEngine:
    """Tests for the personalization scoring engine."""
    
    @pytest.fixture
    def engine(self):
        return PersonalizationEngine()
    
    @pytest.fixture
    def sample_preferences(self):
        prefs = UserPreferencesModel(
            user_id="test-user-123",
            topic_interests={"AI": 0.9, "Technology": 0.8, "Sports": 0.2},
            source_preferences={"TechCrunch": 1.0, "Verge": 0.7},
            summary_length="medium",
            daily_article_limit=10,
            exclude_topics=["Crypto"],
            exclude_sources=["BlockedSource"],
            freshness_preference="daily",
            diversity_boost=0.1,
        )
        return prefs
    
    @pytest.fixture
    def sample_articles(self):
        now = datetime.utcnow()
        return [
            ArticleModel(
                id=1,
                title="AI Breakthrough",
                url="https://example.com/ai",
                content="AI news content...",
                source="TechCrunch",
                category="AI",
                published_at=now - timedelta(hours=2),
                is_processed=True,
            ),
            ArticleModel(
                id=2,
                title="Tech Update",
                url="https://example.com/tech",
                content="Tech news content...",
                source="Verge",
                category="Technology",
                published_at=now - timedelta(hours=5),
                is_processed=True,
            ),
            ArticleModel(
                id=3,
                title="Sports News",
                url="https://example.com/sports",
                content="Sports content...",
                source="ESPN",
                category="Sports",
                published_at=now - timedelta(hours=1),
                is_processed=True,
            ),
            ArticleModel(
                id=4,
                title="Crypto Update",
                url="https://example.com/crypto",
                content="Crypto content...",
                source="CryptoNews",
                category="Crypto",
                published_at=now - timedelta(hours=3),
                is_processed=True,
            ),
        ]
    
    def test_filter_excludes_blocked_topics(self, engine, sample_preferences, sample_articles):
        """Test that excluded topics are filtered out."""
        filtered = engine.filter_articles(sample_articles, sample_preferences)
        
        # Crypto article should be excluded
        assert len(filtered) == 3
        assert all(a.category != "Crypto" for a in filtered)
    
    def test_rank_articles_returns_scored_articles(self, engine, sample_preferences, sample_articles):
        """Test that ranking returns ScoredArticle objects."""
        filtered = engine.filter_articles(sample_articles, sample_preferences)
        scored = engine.rank_articles(filtered, sample_preferences)
        
        assert len(scored) > 0
        assert all(isinstance(s, ScoredArticle) for s in scored)
        assert all(hasattr(s, 'score') for s in scored)
        assert all(hasattr(s, 'score_breakdown') for s in scored)
    
    def test_high_interest_topics_score_higher(self, engine, sample_preferences, sample_articles):
        """Test that articles in high-interest topics score higher."""
        filtered = engine.filter_articles(sample_articles, sample_preferences)
        scored = engine.rank_articles(filtered, sample_preferences)
        
        # AI article should be highest (interest 0.9)
        assert scored[0].article.category in ["AI", "Technology"]
    
    def test_preferred_sources_score_higher(self, engine, sample_preferences):
        """Test that articles from preferred sources score higher."""
        now = datetime.utcnow()
        
        articles = [
            ArticleModel(
                id=1,
                title="From Preferred",
                url="https://example.com/pref",
                content="Content...",
                source="TechCrunch",  # Preferred source
                category="Technology",
                published_at=now,
                is_processed=True,
            ),
            ArticleModel(
                id=2,
                title="From Neutral",
                url="https://example.com/neutral",
                content="Content...",
                source="Unknown",  # Neutral source
                category="Technology",
                published_at=now,
                is_processed=True,
            ),
        ]
        
        scored = engine.rank_articles(articles, sample_preferences)
        
        # TechCrunch article should score higher
        assert scored[0].article.source == "TechCrunch"
    
    def test_freshness_decay(self, engine, sample_preferences):
        """Test that older articles score lower on freshness."""
        now = datetime.utcnow()
        
        articles = [
            ArticleModel(
                id=1,
                title="Recent",
                url="https://example.com/recent",
                content="Content...",
                source="TechCrunch",
                category="Technology",
                published_at=now - timedelta(hours=1),
                is_processed=True,
            ),
            ArticleModel(
                id=2,
                title="Old",
                url="https://example.com/old",
                content="Content...",
                source="TechCrunch",
                category="Technology",
                published_at=now - timedelta(hours=48),
                is_processed=True,
            ),
        ]
        
        scored = engine.rank_articles(articles, sample_preferences)
        
        # Recent article should have higher freshness score
        assert scored[0].article.title == "Recent"
        assert scored[0].score_breakdown['freshness'] > scored[1].score_breakdown['freshness']
    
    def test_diversity_boost_rewards_variety(self, engine, sample_preferences):
        """Test that diversity boost rewards variety of topics."""
        now = datetime.utcnow()
        
        articles = [
            ArticleModel(
                id=1,
                title="AI 1",
                url="https://example.com/ai1",
                content="Content...",
                source="TechCrunch",
                category="AI",
                published_at=now,
                is_processed=True,
            ),
            ArticleModel(
                id=2,
                title="AI 2",
                url="https://example.com/ai2",
                content="Content...",
                source="Verge",
                category="AI",
                published_at=now,
                is_processed=True,
            ),
            ArticleModel(
                id=3,
                title="Sports",
                url="https://example.com/sports",
                content="Content...",
                source="ESPN",
                category="Sports",
                published_at=now,
                is_processed=True,
            ),
        ]
        
        # Set same interest for fair comparison
        sample_preferences.topic_interests = {"AI": 0.8, "Sports": 0.8}
        
        scored = engine.rank_articles(articles, sample_preferences)
        
        # Sports article should get diversity boost (different topic)
        # and might rank higher than the second AI article
        topic_order = [s.article.category for s in scored]
        assert "Sports" in topic_order[:2]  # Sports should be in top 2


class TestUserModelTrainer:
    """Tests for user model learning."""
    
    @pytest.fixture
    def trainer(self):
        return UserModelTrainer()
    
    @pytest.fixture
    def sample_preferences(self):
        return UserPreferencesModel(
            user_id="test-user-123",
            topic_interests={"AI": 0.5, "Technology": 0.5},
            source_preferences={"TechCrunch": 0.5},
        )
    
    @pytest.fixture
    def sample_article(self):
        return ArticleModel(
            id=1,
            title="AI News",
            url="https://example.com/ai",
            content="Content...",
            source="TechCrunch",
            category="AI",
            is_processed=True,
        )
    
    def test_positive_rating_increases_topic_interest(
        self, trainer, sample_preferences, sample_article
    ):
        """Test that liking an article increases topic interest."""
        initial_interest = sample_preferences.topic_interests.get("AI", 0.5)
        
        trainer.update_from_interaction(
            sample_preferences,
            sample_article,
            rating=1,
            read_duration=120,
            saved=False
        )
        
        new_interest = sample_preferences.topic_interests.get("AI", 0.5)
        assert new_interest > initial_interest
    
    def test_negative_rating_decreases_topic_interest(
        self, trainer, sample_preferences, sample_article
    ):
        """Test that disliking an article decreases topic interest."""
        initial_interest = sample_preferences.topic_interests.get("AI", 0.5)
        
        trainer.update_from_interaction(
            sample_preferences,
            sample_article,
            rating=-1,
            read_duration=5,
            saved=False
        )
        
        new_interest = sample_preferences.topic_interests.get("AI", 0.5)
        assert new_interest < initial_interest
    
    def test_save_is_strong_positive_signal(
        self, trainer, sample_preferences, sample_article
    ):
        """Test that saving an article is a strong positive signal."""
        initial_interest = sample_preferences.topic_interests.get("AI", 0.5)
        
        trainer.update_from_interaction(
            sample_preferences,
            sample_article,
            rating=0,
            read_duration=0,
            saved=True
        )
        
        new_interest = sample_preferences.topic_interests.get("AI", 0.5)
        assert new_interest > initial_interest
    
    def test_interest_bounds_respected(
        self, trainer, sample_preferences, sample_article
    ):
        """Test that interests stay within 0.1-1.0 bounds."""
        # Set to maximum
        sample_preferences.topic_interests = {"AI": 1.0}
        
        trainer.update_from_interaction(
            sample_preferences,
            sample_article,
            rating=1,
            read_duration=120,
            saved=True
        )
        
        assert sample_preferences.topic_interests["AI"] <= 1.0
        
        # Set to minimum and penalize
        sample_preferences.topic_interests = {"AI": 0.1}
        
        trainer.update_from_interaction(
            sample_preferences,
            sample_article,
            rating=-1,
            read_duration=0,
        )
        
        assert sample_preferences.topic_interests["AI"] >= 0.1
    
    def test_decay_old_interests(self, trainer, sample_preferences):
        """Test that old interests decay toward neutral."""
        sample_preferences.topic_interests = {"AI": 0.9, "OldTopic": 0.3}
        
        trainer.decay_old_interests(sample_preferences, days=30, decay_rate=0.95)
        
        # High interest should decrease toward 0.5
        assert sample_preferences.topic_interests["AI"] < 0.9
        # Low interest should increase toward 0.5
        assert sample_preferences.topic_interests["OldTopic"] > 0.3


class TestPydanticModels:
    """Tests for Pydantic validation models."""
    
    def test_user_create_valid(self):
        """Test user creation with valid data."""
        user = UserCreate(email="test@example.com", name="Test User")
        assert user.email == "test@example.com"
        assert user.name == "Test User"
    
    def test_preferences_update_validates_time_format(self):
        """Test that delivery_time must be in HH:MM format."""
        with pytest.raises(ValueError):
            UserPreferencesUpdate(delivery_time="invalid")
        
        # Valid format should work
        update = UserPreferencesUpdate(delivery_time="14:30")
        assert update.delivery_time == "14:30"
    
    def test_preferences_update_validates_summary_length(self):
        """Test that summary_length must be valid."""
        with pytest.raises(ValueError):
            UserPreferencesUpdate(summary_length="invalid")
        
        update = UserPreferencesUpdate(summary_length="short")
        assert update.summary_length == "short"
    
    def test_preferences_update_validates_freshness(self):
        """Test that freshness_preference must be valid."""
        with pytest.raises(ValueError):
            UserPreferencesUpdate(freshness_preference="invalid")
        
        update = UserPreferencesUpdate(freshness_preference="weekly")
        assert update.freshness_preference == "weekly"
    
    def test_preferences_update_validates_bounds(self):
        """Test that numeric fields have bounds."""
        # daily_article_limit bounds
        with pytest.raises(ValueError):
            UserPreferencesUpdate(daily_article_limit=100)
        
        with pytest.raises(ValueError):
            UserPreferencesUpdate(daily_article_limit=0)
        
        # diversity_boost bounds
        with pytest.raises(ValueError):
            UserPreferencesUpdate(diversity_boost=1.5)
        
        with pytest.raises(ValueError):
            UserPreferencesUpdate(diversity_boost=-0.1)
    
    def test_onboarding_data_structure(self):
        """Test onboarding data model."""
        data = OnboardingData(
            name="Test User",
            interests=["AI", "Technology"],
            preferred_sources=["TechCrunch", "Verge"],
            summary_length="medium",
            delivery_time="08:00",
            daily_limit=10
        )
        
        assert data.name == "Test User"
        assert len(data.interests) == 2
        assert data.delivery_time == "08:00"
