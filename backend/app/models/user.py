"""User models for personalization and preferences.

This module defines the core user-centric data models:
- User: Basic user account information
- UserPreferences: Personalization settings and interests
- UserInteraction: Engagement tracking and feedback
- PersonalizedDigest: User-specific content curation
"""

import uuid
import json
from datetime import datetime, time, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from sqlalchemy import (
    Column, String, DateTime, Integer, Float, Boolean, 
    ForeignKey, Text, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, field_validator

from app.database import Base


# SQLAlchemy Database Models

class UserModel(Base):
    """User account model."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=True)  # Optional for local/PoC
    
    # Status
    is_active = Column(Boolean, default=True)
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    preferences = relationship("UserPreferencesModel", back_populates="user", uselist=False)
    interactions = relationship("UserInteractionModel", back_populates="user")
    digests = relationship("PersonalizedDigestModel", back_populates="user")


class UserPreferencesModel(Base):
    """User personalization preferences."""
    __tablename__ = "user_preferences"
    
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    
    # Topic interests (JSON: {"AI": 0.9, "Crypto": 0.3})
    topic_interests = Column(JSON, default=dict)
    
    # Source preferences (JSON: {"TechCrunch": 1.0, "Verge": 0.7})
    source_preferences = Column(JSON, default=dict)
    
    # Content preferences
    summary_length = Column(String(20), default="medium")  # short, medium, long
    daily_article_limit = Column(Integer, default=10)
    delivery_time = Column(String(5), default="08:00")  # HH:MM format
    timezone = Column(String(50), default="UTC")
    
    # Filters
    exclude_topics = Column(JSON, default=list)
    exclude_sources = Column(JSON, default=list)
    
    # Advanced
    language_preference = Column(String(10), default="en")
    include_reading_time = Column(Boolean, default=True)
    freshness_preference = Column(String(20), default="daily")  # breaking, daily, weekly
    
    # Learning
    auto_adjust_interests = Column(Boolean, default=True)
    diversity_boost = Column(Float, default=0.1)  # 0-1, higher = more diverse content
    
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("UserModel", back_populates="preferences")


class UserInteractionModel(Base):
    """User engagement tracking for learning."""
    __tablename__ = "user_interactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False, index=True)
    
    # Delivery tracking
    delivered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    digest_id = Column(String(36), ForeignKey("personalized_digests.id"), nullable=True)
    
    # Engagement tracking
    opened_at = Column(DateTime, nullable=True)
    read_duration_seconds = Column(Integer, default=0)
    scroll_depth = Column(Float, default=0.0)  # 0-1 percentage
    
    # Explicit feedback
    rating = Column(Integer, nullable=True)  # -1 (dislike), 0 (neutral), 1 (like)
    saved = Column(Boolean, default=False)
    shared = Column(Boolean, default=False)
    dismissed = Column(Boolean, default=False)
    
    # Derived score (computed field)
    engagement_score = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("UserModel", back_populates="interactions")
    article = relationship("ArticleModel")
    digest = relationship("PersonalizedDigestModel", back_populates="interactions")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'article_id', name='unique_user_article_interaction'),
    )


class PersonalizedDigestModel(Base):
    """User-specific content digest."""
    __tablename__ = "personalized_digests"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Content
    article_ids = Column(JSON, default=list)  # Ordered list of article IDs
    article_scores = Column(JSON, default=dict)  # {article_id: score}
    
    # Personalization metrics
    personalization_score = Column(Float, default=0.0)  # 0-1 how well it matches user
    diversity_score = Column(Float, default=0.0)  # Topic diversity
    freshness_score = Column(Float, default=0.0)  # Recency weighting
    
    # Status
    status = Column(String(20), default="pending")  # pending, sent, opened
    sent_at = Column(DateTime, nullable=True)
    
    # Performance metrics
    opened = Column(Boolean, default=False)
    opened_at = Column(DateTime, nullable=True)
    click_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("UserModel", back_populates="digests")
    interactions = relationship("UserInteractionModel", back_populates="digest")


# Pydantic Models for API

class UserCreate(BaseModel):
    """User registration request."""
    email: str
    name: str
    password: Optional[str] = None  # Optional for PoC


class UserResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    name: str
    onboarding_completed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TopicInterest(BaseModel):
    """Topic with interest weight."""
    topic: str
    weight: float = Field(ge=0.0, le=1.0)


class SourcePreference(BaseModel):
    """Source with preference weight."""
    source: str
    weight: float = Field(ge=0.0, le=1.0)


class UserPreferencesUpdate(BaseModel):
    """Update user preferences."""
    topic_interests: Optional[Dict[str, float]] = None
    source_preferences: Optional[Dict[str, float]] = None
    summary_length: Optional[str] = None
    daily_article_limit: Optional[int] = Field(default=None, ge=1, le=50)
    delivery_time: Optional[str] = None  # HH:MM format
    timezone: Optional[str] = None
    exclude_topics: Optional[List[str]] = None
    exclude_sources: Optional[List[str]] = None
    language_preference: Optional[str] = None
    include_reading_time: Optional[bool] = None
    freshness_preference: Optional[str] = None
    auto_adjust_interests: Optional[bool] = None
    diversity_boost: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    @field_validator('delivery_time')
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate HH:MM format."""
        if v is None:
            return v
        try:
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise ValueError('delivery_time must be in HH:MM format')
    
    @field_validator('summary_length')
    @classmethod
    def validate_summary_length(cls, v: Optional[str]) -> Optional[str]:
        """Validate summary length."""
        if v is None:
            return v
        valid = ["short", "medium", "long"]
        if v not in valid:
            raise ValueError(f'summary_length must be one of {valid}')
        return v
    
    @field_validator('freshness_preference')
    @classmethod
    def validate_freshness(cls, v: Optional[str]) -> Optional[str]:
        """Validate freshness preference."""
        if v is None:
            return v
        valid = ["breaking", "daily", "weekly"]
        if v not in valid:
            raise ValueError(f'freshness_preference must be one of {valid}')
        return v

    @field_validator('topic_interests', 'source_preferences')
    @classmethod
    def validate_weight_maps(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        """Validate preference maps contain safe keys and 0-1 values."""
        if v is None:
            return v

        cleaned: Dict[str, float] = {}
        for key, weight in v.items():
            safe_key = key.strip()
            if not safe_key:
                raise ValueError("Preference keys cannot be empty")
            if len(safe_key) > 100:
                raise ValueError("Preference keys must be <= 100 characters")
            if weight < 0.0 or weight > 1.0:
                raise ValueError("Preference values must be between 0 and 1")
            cleaned[safe_key] = float(weight)
        return cleaned

    @field_validator('exclude_topics', 'exclude_sources')
    @classmethod
    def validate_exclude_lists(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and normalize exclude lists."""
        if v is None:
            return v

        cleaned: List[str] = []
        for item in v:
            value = item.strip()
            if not value:
                continue
            if len(value) > 100:
                raise ValueError("Excluded value must be <= 100 characters")
            if value not in cleaned:
                cleaned.append(value)
        return cleaned


class UserPreferencesResponse(BaseModel):
    """User preferences response."""
    topic_interests: Dict[str, float]
    source_preferences: Dict[str, float]
    summary_length: str
    daily_article_limit: int
    delivery_time: str
    timezone: str
    exclude_topics: List[str]
    exclude_sources: List[str]
    language_preference: str
    include_reading_time: bool
    freshness_preference: str
    auto_adjust_interests: bool
    diversity_boost: float
    
    class Config:
        from_attributes = True


class UserInteractionCreate(BaseModel):
    """Record user interaction."""
    article_id: int
    opened: Optional[bool] = None
    read_duration_seconds: Optional[int] = None
    scroll_depth: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    rating: Optional[int] = Field(default=None, ge=-1, le=1)
    saved: Optional[bool] = None
    shared: Optional[bool] = None
    dismissed: Optional[bool] = None


class UserInteractionResponse(BaseModel):
    """User interaction response."""
    id: str
    article_id: int
    delivered_at: datetime
    opened_at: Optional[datetime]
    read_duration_seconds: int
    scroll_depth: float
    rating: Optional[int]
    saved: bool
    shared: bool
    engagement_score: float
    
    class Config:
        from_attributes = True


class ArticleFeedback(BaseModel):
    """Simple feedback for an article."""
    article_id: int
    feedback: str  # "like", "dislike", "save", "dismiss"


class PersonalizedDigestResponse(BaseModel):
    """Personalized digest response."""
    id: str
    created_at: datetime
    articles: List[dict]  # Article + personalization score
    personalization_score: float
    diversity_score: float
    status: str
    sent_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class OnboardingData(BaseModel):
    """Initial user onboarding data."""
    name: str
    interests: List[str]  # Selected topics
    preferred_sources: List[str]
    summary_length: str = "medium"
    delivery_time: str = "08:00"
    daily_limit: int = Field(default=10, ge=1, le=50)

    @field_validator("summary_length")
    @classmethod
    def validate_onboarding_summary_length(cls, v: str) -> str:
        valid = {"short", "medium", "long"}
        if v not in valid:
            raise ValueError(f"summary_length must be one of {sorted(valid)}")
        return v

    @field_validator("delivery_time")
    @classmethod
    def validate_onboarding_delivery_time(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError as exc:
            raise ValueError("delivery_time must be in HH:MM format") from exc
        return v

    @field_validator("interests", "preferred_sources")
    @classmethod
    def validate_onboarding_lists(cls, v: List[str]) -> List[str]:
        cleaned: List[str] = []
        for item in v:
            value = item.strip()
            if not value:
                continue
            if len(value) > 100:
                raise ValueError("Values must be <= 100 characters")
            if value not in cleaned:
                cleaned.append(value)
        return cleaned


class UserStats(BaseModel):
    """User engagement statistics."""
    total_articles_read: int
    total_articles_saved: int
    average_reading_time: int  # seconds
    favorite_topics: List[dict]  # [{topic, count}]
    favorite_sources: List[dict]  # [{source, count}]
    digest_open_rate: float  # percentage
    last_7_days_activity: List[int]  # Articles read per day
