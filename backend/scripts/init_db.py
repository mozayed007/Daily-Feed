#!/usr/bin/env python3
"""Initialize database tables.

Run this script to create all database tables:
    python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models to register them with SQLAlchemy
from app.database import Database, Base
from app.models.user import UserModel, UserPreferencesModel, UserInteractionModel, PersonalizedDigestModel
from app.core.logging_config import configure_logging, get_logger

logger = get_logger(__name__)


async def init_database():
    """Create all database tables."""
    configure_logging()
    logger.info("initializing_database")
    
    await Database.create_tables()
    
    logger.info("database_initialized_successfully")
    print("✅ Database tables created successfully!")
    print("   Tables created:")
    for table in Base.metadata.tables.keys():
        print(f"   • {table}")


if __name__ == "__main__":
    asyncio.run(init_database())
