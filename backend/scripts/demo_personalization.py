#!/usr/bin/env python3
"""Demo script showing Daily Feed personalization in action.

This script demonstrates:
1. Creating a user
2. Completing onboarding with interests
3. Generating personalized digests
4. Providing feedback
5. Seeing preferences adapt
"""

import asyncio
from datetime import datetime

from app.core.personalization import get_personalization_engine, get_user_model_trainer
from app.models.user import UserPreferencesModel, UserInteractionModel
from app.database import ArticleModel


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_article(article: ArticleModel, score: float = None, breakdown: dict = None):
    """Print article details."""
    print(f"📰 {article.title}")
    print(f"   Source: {article.source} | Category: {article.category}")
    if score is not None:
        print(f"   Score: {score:.3f}")
    if breakdown:
        print(f"   Breakdown: {breakdown}")
    print()


def demo_scenario_1():
    """Scenario: New user with AI interests gets personalized digest."""
    print_header("Scenario 1: New AI Enthusiast")
    
    # Create user preferences
    prefs = UserPreferencesModel(
        user_id="demo-user-1",
        topic_interests={"AI": 0.9, "Technology": 0.7},
        source_preferences={"TechCrunch": 1.0, "The Verge": 0.8, "Hacker News": 0.9},
        summary_length="medium",
        daily_article_limit=5,
        freshness_preference="daily",
        diversity_boost=0.1,
    )
    
    print(f"👤 User Profile:")
    print(f"   Topic Interests: {prefs.topic_interests}")
    print(f"   Source Preferences: {prefs.source_preferences}")
    print()
    
    # Create sample articles
    now = datetime.utcnow()
    articles = [
        ArticleModel(
            id=1,
            title="OpenAI Announces GPT-5",
            url="https://example.com/1",
            content="Breaking AI news...",
            source="TechCrunch",
            category="AI",
            published_at=now,
            is_processed=True,
        ),
        ArticleModel(
            id=2,
            title="New JavaScript Framework Released",
            url="https://example.com/2",
            content="Tech news...",
            source="Hacker News",
            category="Technology",
            published_at=now,
            is_processed=True,
        ),
        ArticleModel(
            id=3,
            title="Stock Market Update",
            url="https://example.com/3",
            content="Finance news...",
            source="Bloomberg",
            category="Finance",
            published_at=now,
            is_processed=True,
        ),
        ArticleModel(
            id=4,
            title="AI Regulation Debate Heats Up",
            url="https://example.com/4",
            content="Policy news...",
            source="The Verge",
            category="AI",
            published_at=now,
            is_processed=True,
        ),
        ArticleModel(
            id=5,
            title="Crypto Market Crash",
            url="https://example.com/5",
            content="Crypto news...",
            source="CoinDesk",
            category="Crypto",
            published_at=now,
            is_processed=True,
        ),
    ]
    
    print("📥 Available Articles:")
    for article in articles:
        print(f"   • {article.title} ({article.category}, {article.source})")
    print()
    
    # Generate personalized ranking
    engine = get_personalization_engine()
    scored = engine.rank_articles(articles, prefs, limit=3)
    
    print("📊 Personalized Digest (Top 3):")
    for i, s in enumerate(scored, 1):
        print(f"\n   #{i}")
        print_article(s.article, s.score, s.score_breakdown)
    
    return prefs, scored


def demo_scenario_2(prefs: UserPreferencesModel, articles: list):
    """Scenario: User provides feedback, model adapts."""
    print_header("Scenario 2: Learning from Feedback")
    
    trainer = get_user_model_trainer()
    
    # User reads and likes the first AI article
    ai_article = ArticleModel(
        id=1,
        title="OpenAI Announces GPT-5",
        url="https://example.com/1",
        content="Breaking AI news...",
        source="TechCrunch",
        category="AI",
        is_processed=True,
    )
    
    print("👤 User Action: Read AI article for 3 minutes and LIKED it")
    print(f"   Before: AI topic interest = {prefs.topic_interests.get('AI', 0.5)}")
    print(f"   Before: TechCrunch preference = {prefs.source_preferences.get('TechCrunch', 0.5)}")
    
    # Update model
    changes = trainer.update_from_interaction(
        prefs,
        ai_article,
        rating=1,  # Like
        read_duration=180,  # 3 minutes
        saved=False
    )
    
    print(f"\n   After: AI topic interest = {prefs.topic_interests.get('AI', 0.5)}")
    print(f"   After: TechCrunch preference = {prefs.source_preferences.get('TechCrunch', 0.5)}")
    print(f"\n   Changes: {changes}")
    
    # User dismisses Crypto article quickly
    crypto_article = ArticleModel(
        id=5,
        title="Crypto Market Crash",
        url="https://example.com/5",
        content="Crypto news...",
        source="CoinDesk",
        category="Crypto",
        is_processed=True,
    )
    
    print("\n👤 User Action: Dismissed Crypto article after 2 seconds")
    print(f"   Before: Crypto topic interest = {prefs.topic_interests.get('Crypto', 0.5)}")
    
    # Update model
    changes = trainer.update_from_interaction(
        prefs,
        crypto_article,
        rating=-1,  # Dislike
        read_duration=2,
        dismissed=True
    )
    
    print(f"   After: Crypto topic interest = {prefs.topic_interests.get('Crypto', 0.5)}")
    print(f"\n   Changes: {changes}")


def demo_scenario_3():
    """Scenario: Freshness modes comparison."""
    print_header("Scenario 3: Freshness Modes")
    
    from datetime import timedelta
    
    now = datetime.utcnow()
    articles = [
        ArticleModel(
            id=1,
            title="Breaking: Major Tech Announcement",
            url="https://example.com/1",
            content="Just happened...",
            source="TechCrunch",
            category="Technology",
            published_at=now - timedelta(hours=1),
            is_processed=True,
        ),
        ArticleModel(
            id=2,
            title="Yesterday's Tech News",
            url="https://example.com/2",
            content="Yesterday...",
            source="TechCrunch",
            category="Technology",
            published_at=now - timedelta(hours=20),
            is_processed=True,
        ),
        ArticleModel(
            id=3,
            title="Last Week's Analysis",
            url="https://example.com/3",
            content="Deep analysis...",
            source="TechCrunch",
            category="Technology",
            published_at=now - timedelta(days=5),
            is_processed=True,
        ),
    ]
    
    prefs = UserPreferencesModel(
        user_id="demo-user-3",
        topic_interests={"Technology": 0.8},
        source_preferences={"TechCrunch": 1.0},
        diversity_boost=0.1,
    )
    
    engine = get_personalization_engine()
    
    for mode in ["breaking", "daily", "weekly"]:
        prefs.freshness_preference = mode
        scored = engine.rank_articles(articles, prefs)
        
        print(f"📰 {mode.upper()} Mode:")
        for s in scored:
            age = (now - s.article.published_at)
            age_str = f"{age.days}d {age.seconds//3600}h ago"
            print(f"   Score {s.score:.3f} - {s.article.title} ({age_str})")
        print()


def main():
    """Run all demo scenarios."""
    print("\n" + "🚀"*30)
    print("   Daily Feed - Personalization Demo")
    print("🚀"*30)
    
    # Scenario 1: New user gets personalized digest
    prefs, scored_articles = demo_scenario_1()
    
    # Recreate articles for scenario 2
    articles = [
        ArticleModel(
            id=1,
            title="OpenAI Announces GPT-5",
            url="https://example.com/1",
            content="Breaking AI news...",
            source="TechCrunch",
            category="AI",
            is_processed=True,
        ),
        ArticleModel(
            id=5,
            title="Crypto Market Crash",
            url="https://example.com/5",
            content="Crypto news...",
            source="CoinDesk",
            category="Crypto",
            is_processed=True,
        ),
    ]
    
    # Scenario 2: User provides feedback
    demo_scenario_2(prefs, articles)
    
    # Scenario 3: Freshness modes
    demo_scenario_3()
    
    print_header("Demo Complete!")
    print("""
Next Steps:
1. Run the backend: python main.py
2. Create a user via API: POST /api/v1/users
3. Complete onboarding: POST /api/v1/users/onboarding
4. Generate digests: POST /api/v1/users/me/digest/generate
5. Provide feedback: POST /api/v1/users/me/feedback

See PERSONALIZATION_GUIDE.md for full API documentation.
""")


if __name__ == "__main__":
    main()
