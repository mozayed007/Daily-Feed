import os

# Set environment variables for testing BEFORE importing any app modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["DEBUG"] = "false"

import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Mock before ANY app imports
import app.core.agent_loop
import app.core.scheduler
import app.core.memory

# Create mocks
mock_agent = MagicMock()
mock_agent.get_available_tools.return_value = []
mock_agent.run_pipeline = AsyncMock(return_value={"success": True, "message": "Pipeline completed"})

mock_scheduler = MagicMock()
mock_scheduler._running = False
mock_scheduler.list_jobs.return_value = []

mock_memory = MagicMock()
mock_memory.get_stats.return_value = {"total_units": 0}

# Patch them
app.core.agent_loop.get_agent_loop = lambda: mock_agent
app.core.scheduler.get_scheduler = lambda: mock_scheduler
app.core.memory.get_memory_store = lambda: mock_memory

from app.database import Database, Base, sync_engine

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """Cleanup test database file after all tests finish."""
    yield
    if os.path.exists("test.db"):
        try:
            os.remove("test.db")
        except PermissionError:
            pass # Windows file locking might prevent immediate deletion

@pytest.fixture(autouse=True, scope="function")
def setup_database_sync():
    """Setup test database before each test using sync operations."""
    # We use a separate file test.db, which is handled by setup_database_async
    pass

@pytest.fixture(autouse=True)
async def setup_database_async():
    """Async version of database setup for tests."""
    await Database.create_tables()
    yield
    await Database.drop_tables()

@pytest.fixture
async def db_session() -> AsyncGenerator:
    """Provide a database session for tests"""
    async with Database.get_session() as session:
        yield session

@pytest.fixture
def client():
    """TestClient that uses the mocked app"""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)
