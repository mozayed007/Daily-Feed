"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Database, Base, sync_engine


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="function")
def setup_database_sync():
    """Setup test database before each test using sync operations.
    
    This uses sync SQLAlchemy to avoid event loop conflicts with FastAPI's TestClient
    which runs in a sync context but internally manages its own async event loop.
    """
    # Create tables synchronously
    Base.metadata.create_all(bind=sync_engine)
    yield
    # Cleanup after test
    Base.metadata.drop_all(bind=sync_engine)


@pytest.fixture
async def setup_database_async():
    """Async version of database setup for tests that need it explicitly."""
    await Database.create_tables()
    yield
    await Database.drop_tables()


@pytest.fixture
async def db_session() -> AsyncGenerator:
    """Provide a database session for tests"""
    async with Database.get_session() as session:
        yield session
