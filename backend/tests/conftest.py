"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator

from app.database import Database


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """Setup test database before each test"""
    await Database.create_tables()
    yield
    # Cleanup after test
    await Database.drop_tables()


@pytest.fixture
async def db_session() -> AsyncGenerator:
    """Provide a database session for tests"""
    async with Database.get_session() as session:
        yield session
