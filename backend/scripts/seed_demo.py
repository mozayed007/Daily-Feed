#!/usr/bin/env python3
"""Seed database with demo data.

Run this script to populate the database with sample data:
    python scripts/seed_demo.py
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Database, ArticleModel, SourceModel
from app.models.user import UserModel, UserPreferencesModel
from app.core.config_manager import get_config_manager
from app.core.logging_config import configure_logging, get_logger

logger = get_logger(__name__)


async def seed_demo_data():
    """Seed database with demo data."""
    configure_logging()
    logger.info("seeding_demo_data")
    
    async with Database.get_session() as db:
        # Check if already seeded
        from sqlalchemy import select, func
        result = await db.execute(select(func.count()).select_from(ArticleModel))
        count = result.scalar()
        
        if count > 0:
            print(f"⚠️  Database already has {count} articles. Skipping seed.")
            print("   Use `python scripts/init_db.py` to reset if needed.")
            return
        
        # Create sources
        sources = [
            SourceModel(
                name="TechCrunch",
                url="https://techcrunch.com/feed",
                category="Technology",
                enabled=True
            ),
            SourceModel(
                name="Hacker News",
                url="https://news.ycombinator.com/rss",
                category="Technology",
                enabled=True
            ),
            SourceModel(
                name="The Verge",
                url="https://www.theverge.com/rss/index.xml",
                category="Technology",
                enabled=True
            ),
            SourceModel(
                name="Smol AI",
                url="https://news.smol.ai/rss",
                category="AI",
                enabled=True
            ),
        ]
        
        for source in sources:
            db.add(source)
        
        await db.flush()
        print(f"✅ Created {len(sources)} sources")
        
        # Create demo user
        user = UserModel(
            email="demo@dailyfeed.local",
            name="Demo User",
            onboarding_completed=True
        )
        db.add(user)
        await db.flush()
        
        # Create preferences
        prefs = UserPreferencesModel(
            user_id=user.id,
            topic_interests={
                "AI": 0.9,
                "Technology": 0.8,
                "Business": 0.6,
                "Science": 0.5
            },
            source_preferences={
                "TechCrunch": 1.0,
                "Hacker News": 0.9,
                "The Verge": 0.8
            },
            summary_length="medium",
            daily_article_limit=10,
            delivery_time="08:00",
            freshness_preference="daily",
            diversity_boost=0.1
        )
        db.add(prefs)
        
        print(f"✅ Created demo user: {user.email}")
        
        # Create sample articles
        now = datetime.utcnow()
        articles = [
            ArticleModel(
                title="OpenAI Announces GPT-5 with Revolutionary Capabilities",
                url="https://example.com/ai-1",
                content="OpenAI has unveiled GPT-5, featuring unprecedented reasoning abilities and multimodal understanding...",
                source="TechCrunch",
                category="AI",
                summary="OpenAI's GPT-5 features revolutionary reasoning and multimodal capabilities, setting new benchmarks.",
                is_processed=True,
                published_at=now - timedelta(hours=2),
                fetched_at=now
            ),
            ArticleModel(
                title="Google DeepMind's New Protein Folding Breakthrough",
                url="https://example.com/ai-2",
                content="Scientists at DeepMind have achieved a major breakthrough in protein structure prediction...",
                source="TechCrunch",
                category="AI",
                summary="DeepMind's latest model predicts protein structures with 99% accuracy.",
                is_processed=True,
                published_at=now - timedelta(hours=4),
                fetched_at=now
            ),
            ArticleModel(
                title="Apple's Vision Pro: First Week Sales Exceed Expectations",
                url="https://example.com/tech-1",
                content="Apple's Vision Pro headset has sold over 200,000 units in its first week...",
                source="The Verge",
                category="Technology",
                summary="Vision Pro sales exceed expectations with 200K units sold in week one.",
                is_processed=True,
                published_at=now - timedelta(hours=6),
                fetched_at=now
            ),
            ArticleModel(
                title="Rust vs Go: Which Language for Your Next Project?",
                url="https://example.com/tech-2",
                content="A comprehensive comparison of Rust and Go for backend development...",
                source="Hacker News",
                category="Technology",
                summary="Comparing Rust's safety features with Go's simplicity for backend systems.",
                is_processed=True,
                published_at=now - timedelta(hours=8),
                fetched_at=now
            ),
            ArticleModel(
                title="Fed Signals Potential Rate Cuts in Coming Months",
                url="https://example.com/business-1",
                content="The Federal Reserve has indicated that interest rate cuts may be on the horizon...",
                source="TechCrunch",
                category="Business",
                summary="Federal Reserve hints at upcoming interest rate cuts amid cooling inflation.",
                is_processed=True,
                published_at=now - timedelta(hours=3),
                fetched_at=now
            ),
            ArticleModel(
                title="Tesla's Full Self-Driving v12 Rollout Begins",
                url="https://example.com/tech-3",
                content="Tesla has started rolling out FSD v12 to select customers...",
                source="The Verge",
                category="Technology",
                summary="Tesla begins FSD v12 rollout with end-to-end neural networks.",
                is_processed=True,
                published_at=now - timedelta(hours=5),
                fetched_at=now
            ),
            ArticleModel(
                title="Quantum Computing Breakthrough: 1000 Qubit Milestone Reached",
                url="https://example.com/science-1",
                content="IBM has announced a new quantum processor with over 1000 qubits...",
                source="TechCrunch",
                category="Science",
                summary="IBM achieves 1000 qubit quantum processor milestone.",
                is_processed=True,
                published_at=now - timedelta(hours=10),
                fetched_at=now
            ),
            ArticleModel(
                title="Startup Raises $100M for AI-Powered Healthcare",
                url="https://example.com/business-2",
                content="MediAI has raised $100M Series B to expand their diagnostic AI platform...",
                source="TechCrunch",
                category="Business",
                summary="MediAI secures $100M funding for AI healthcare diagnostics.",
                is_processed=True,
                published_at=now - timedelta(hours=7),
                fetched_at=now
            ),
        ]
        
        for article in articles:
            db.add(article)
        
        print(f"✅ Created {len(articles)} sample articles")
        
        await db.commit()
        
        print("\n" + "="*50)
        print("🎉 Demo data seeded successfully!")
        print("="*50)
        print(f"""
Demo User:
  Email: demo@dailyfeed.local
  Interests: AI, Technology, Business, Science

Next Steps:
  1. Start the server: python main.py
  2. Open: http://localhost:8000/docs
  3. Try the personalized digest endpoint!
""")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
