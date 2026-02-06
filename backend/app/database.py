"""Database configuration and models"""

import json
from datetime import datetime
from typing import Optional, List, AsyncGenerator, Any
from pydantic import HttpUrl, field_validator
from contextlib import asynccontextmanager

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, 
    Boolean, ForeignKey, JSON, select, desc, func
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta

from app.config import get_settings

settings = get_settings()

# SQLAlchemy setup
Base: DeclarativeMeta = declarative_base()

# Async engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Sync engine for background tasks
sync_database_url = settings.DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://")
sync_engine = create_engine(sync_database_url, echo=settings.DEBUG)
SessionLocal = sessionmaker(bind=sync_engine)


# Database Models
class ArticleModel(Base):
    """Article database model"""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    content = Column(Text)
    summary = Column(Text)
    source = Column(String(200), nullable=False, index=True)
    category = Column(String(100), index=True)
    sentiment = Column(String(50))
    reading_time = Column(Integer, default=1)
    key_points = Column(JSON, default=list)
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    is_processed = Column(Boolean, default=False, index=True)
    critic_score = Column(Integer)
    
    # Relationships
    digest_id = Column(Integer, ForeignKey("digests.id"), nullable=True)
    digest = relationship("DigestModel", back_populates="articles")


class DigestModel(Base):
    """Digest database model"""
    __tablename__ = "digests"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    article_count = Column(Integer, default=0)
    delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime)
    content = Column(Text)
    
    # Relationships
    articles = relationship("ArticleModel", back_populates="digest")


class SourceModel(Base):
    """RSS Source configuration"""
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    url = Column(String(1000), unique=True, nullable=False)
    category = Column(String(100))
    enabled = Column(Boolean, default=True)
    last_fetch = Column(DateTime)
    fetch_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class SettingModel(Base):
    """User settings storage"""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LogModel(Base):
    """System logs"""
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    source = Column(String(100))
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


# Database operations
class Database:
    """Database operations wrapper"""
    
    @staticmethod
    async def create_tables():
        """Create all tables"""
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    @staticmethod
    async def drop_tables():
        """Drop all tables"""
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    @staticmethod
    @asynccontextmanager
    async def get_session() -> AsyncGenerator[AsyncSession, None]:
        """Get async database session"""
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @staticmethod
    def get_sync_session():
        """Get sync database session for background tasks"""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()


# FastAPI dependency
async def get_db():
    """FastAPI dependency for database sessions."""
    async with Database.get_session() as session:
        yield session


# Pydantic models for API
from pydantic import BaseModel, Field
from typing import Dict, Any


class ArticleCreate(BaseModel):
    title: str
    url: str
    content: Optional[str] = None
    source: str
    category: Optional[str] = None
    published_at: Optional[datetime] = None


class ArticleResponse(BaseModel):
    id: int
    title: str
    url: str
    summary: Optional[str] = None
    source: str
    category: Optional[str] = None
    sentiment: Optional[str] = None
    reading_time: int = 1
    key_points: List[str] = []
    published_at: Optional[datetime] = None
    fetched_at: datetime
    is_processed: bool = False
    critic_score: Optional[int] = None
    
    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    articles: List[ArticleResponse]
    total: int
    page: int = 1
    page_size: int = 20


class SourceCreate(BaseModel):
    name: str
    url: str
    category: Optional[str] = "General"
    enabled: bool = True
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format"""
        try:
            # Try to parse as HttpUrl - this validates the format
            HttpUrl(v)
            return v
        except Exception:
            raise ValueError('Invalid URL format')


class SourceResponse(BaseModel):
    id: int
    name: str
    url: str
    category: Optional[str]
    enabled: bool
    last_fetch: Optional[datetime]
    fetch_count: int
    error_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DigestResponse(BaseModel):
    id: int
    created_at: datetime
    article_count: int
    delivered: bool
    delivered_at: Optional[datetime]
    articles: List[ArticleResponse] = []
    
    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_articles: int
    processed_articles: int
    unprocessed_articles: int
    total_digests: int
    total_sources: int
    active_sources: int
    categories: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
    memory_units: Optional[int] = None
