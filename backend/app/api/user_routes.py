"""User management and personalization API routes."""

import math
from collections import Counter
from typing import List
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, ArticleModel
from app.models.user import (
    UserModel, UserPreferencesModel, UserInteractionModel, PersonalizedDigestModel,
    UserCreate, UserResponse, UserPreferencesUpdate, UserPreferencesResponse,
    UserInteractionCreate, UserInteractionResponse, ArticleFeedback,
    PersonalizedDigestResponse, OnboardingData, UserStats
)
from app.core.auth import get_password_hash, verify_password
from app.core.personalization import (
    get_personalization_engine, get_user_model_trainer, ScoredArticle
)
from app.api.deps import get_current_user
from app.core.logging_config import get_logger

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger(__name__)


# ========== User Management ==========

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Create a new user account."""
    result = await db.execute(
        select(UserModel).where(UserModel.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = UserModel(
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
    )
    db.add(user)
    await db.flush()
    
    prefs = UserPreferencesModel(user_id=user.id)
    db.add(prefs)
    
    await db.commit()
    
    logger.info("user_created", user_id=user.id, email=user_data.email)
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserModel = Depends(get_current_user)
):
    """Get current user profile."""
    return current_user


@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get user engagement statistics."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(func.count()).where(
            UserInteractionModel.user_id == current_user.id,
            UserInteractionModel.read_duration_seconds > 30,
            UserInteractionModel.created_at >= cutoff
        )
    )
    total_read = result.scalar() or 0
    
    result = await db.execute(
        select(func.count()).where(
            UserInteractionModel.user_id == current_user.id,
            UserInteractionModel.saved == True,
            UserInteractionModel.created_at >= cutoff
        )
    )
    total_saved = result.scalar() or 0
    
    result = await db.execute(
        select(func.avg(UserInteractionModel.read_duration_seconds)).where(
            UserInteractionModel.user_id == current_user.id,
            UserInteractionModel.created_at >= cutoff
        )
    )
    avg_reading_time = int(result.scalar() or 0)
    
    result = await db.execute(
        select(ArticleModel.category, func.count().label("cnt"))
        .join(UserInteractionModel, UserInteractionModel.article_id == ArticleModel.id)
        .where(
            UserInteractionModel.user_id == current_user.id,
            UserInteractionModel.read_duration_seconds > 30,
            UserInteractionModel.created_at >= cutoff,
            ArticleModel.category.isnot(None)
        )
        .group_by(ArticleModel.category)
        .order_by(desc("cnt"))
        .limit(5)
    )
    favorite_topics = [{"topic": row[0], "count": row[1]} for row in result.all()]

    result = await db.execute(
        select(ArticleModel.source, func.count().label("cnt"))
        .join(UserInteractionModel, UserInteractionModel.article_id == ArticleModel.id)
        .where(
            UserInteractionModel.user_id == current_user.id,
            UserInteractionModel.read_duration_seconds > 30,
            UserInteractionModel.created_at >= cutoff,
            ArticleModel.source.isnot(None)
        )
        .group_by(ArticleModel.source)
        .order_by(desc("cnt"))
        .limit(5)
    )
    favorite_sources = [{"source": row[0], "count": row[1]} for row in result.all()]

    result = await db.execute(
        select(func.count()).where(
            PersonalizedDigestModel.user_id == current_user.id,
            PersonalizedDigestModel.created_at >= cutoff
        )
    )
    total_digests = result.scalar() or 0
    
    result = await db.execute(
        select(func.count()).where(
            PersonalizedDigestModel.user_id == current_user.id,
            PersonalizedDigestModel.opened == True,
            PersonalizedDigestModel.created_at >= cutoff
        )
    )
    opened_digests = result.scalar() or 0
    
    open_rate = (opened_digests / total_digests * 100) if total_digests > 0 else 0
    
    result = await db.execute(
        select(func.date(UserInteractionModel.created_at), func.count())
        .where(
            UserInteractionModel.user_id == current_user.id,
            UserInteractionModel.created_at >= cutoff,
            UserInteractionModel.read_duration_seconds > 30
        )
        .group_by(func.date(UserInteractionModel.created_at))
    )
    activity_by_day = {row[0]: row[1] for row in result.all()}
    
    last_n_days = []
    for i in range(days):
        day = (datetime.now(timezone.utc) - timedelta(days=i)).date()
        last_n_days.insert(0, activity_by_day.get(day, 0))
    
    return UserStats(
        total_articles_read=total_read,
        total_articles_saved=total_saved,
        average_reading_time=avg_reading_time,
        favorite_topics=favorite_topics,
        favorite_sources=favorite_sources,
        digest_open_rate=round(open_rate, 1),
        last_7_days_activity=last_n_days
    )


# ========== Onboarding ==========

@router.post("/onboarding", response_model=UserResponse)
async def complete_onboarding(
    data: OnboardingData,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Complete user onboarding and set initial preferences."""
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    if not data.interests:
        raise HTTPException(status_code=400, detail="At least one interest is required")
    if not data.preferred_sources:
        raise HTTPException(status_code=400, detail="At least one preferred source is required")

    prefs_result = await db.execute(
        select(UserPreferencesModel).where(
            UserPreferencesModel.user_id == current_user.id
        )
    )
    prefs = prefs_result.scalar_one_or_none()
    if not prefs:
        prefs = UserPreferencesModel(user_id=current_user.id)
        db.add(prefs)
    
    # Set initial topic interests
    topic_interests = {}
    for interest in data.interests:
        topic_interests[interest] = 0.8  # High initial interest
    prefs.topic_interests = topic_interests
    
    # Set source preferences
    source_prefs = {}
    for source in data.preferred_sources:
        source_prefs[source] = 0.9
    prefs.source_preferences = source_prefs
    
    # Other preferences
    prefs.summary_length = data.summary_length
    prefs.delivery_time = data.delivery_time
    prefs.daily_article_limit = data.daily_limit
    
    # Mark onboarding complete
    current_user.name = data.name.strip()
    current_user.onboarding_completed = True
    
    await db.commit()
    
    logger.info(
        "onboarding_completed",
        user_id=current_user.id,
        interests=data.interests,
        sources=data.preferred_sources
    )
    
    return current_user


# ========== Preferences ==========

@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get user preferences."""
    prefs_result = await db.execute(
        select(UserPreferencesModel).where(UserPreferencesModel.user_id == current_user.id)
    )
    prefs = prefs_result.scalar_one_or_none()
    
    if not prefs:
        prefs = UserPreferencesModel(user_id=current_user.id)
        db.add(prefs)
        await db.commit()
    
    return prefs


@router.patch("/me/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    update: UserPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Update user preferences."""
    prefs_result = await db.execute(
        select(UserPreferencesModel).where(UserPreferencesModel.user_id == current_user.id)
    )
    prefs = prefs_result.scalar_one_or_none()
    
    if not prefs:
        prefs = UserPreferencesModel(user_id=current_user.id)
        db.add(prefs)
    
    update_data = update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No preference fields provided")

    allowed_fields = {
        "topic_interests", "source_preferences", "summary_length",
        "daily_article_limit", "delivery_time", "timezone",
        "exclude_topics", "exclude_sources", "language_preference",
        "include_reading_time", "freshness_preference",
        "auto_adjust_interests", "diversity_boost"
    }
    for field, value in update_data.items():
        if field not in allowed_fields:
            raise HTTPException(status_code=400, detail=f"Unsupported preference field: {field}")
        if field in {"topic_interests", "source_preferences"} and value is not None and len(value) > 200:
            raise HTTPException(status_code=400, detail=f"{field} exceeds maximum supported size")
        if field in {"exclude_topics", "exclude_sources"} and value is not None and len(value) > 200:
            raise HTTPException(status_code=400, detail=f"{field} exceeds maximum supported size")
        setattr(prefs, field, value)
    
    await db.commit()
    await db.refresh(prefs)
    
    logger.info("preferences_updated", user_id=current_user.id, changes=list(update_data.keys()))
    
    return prefs


@router.post("/me/preferences/reset")
async def reset_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Reset user preferences to defaults."""
    prefs_result = await db.execute(
        select(UserPreferencesModel).where(UserPreferencesModel.user_id == current_user.id)
    )
    prefs = prefs_result.scalar_one_or_none()

    if not prefs:
        prefs = UserPreferencesModel(user_id=current_user.id)
        db.add(prefs)

    prefs.topic_interests = {}
    prefs.source_preferences = {}
    prefs.summary_length = "medium"
    prefs.daily_article_limit = 10
    prefs.delivery_time = "08:00"
    prefs.exclude_topics = []
    prefs.exclude_sources = []
    prefs.auto_adjust_interests = True
    prefs.diversity_boost = 0.1

    await db.commit()

    logger.info("preferences_reset", user_id=current_user.id)
    return {"success": True}


# ========== Interactions & Feedback ==========

@router.post("/me/interactions", response_model=UserInteractionResponse)
async def record_interaction(
    interaction: UserInteractionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Record user interaction with an article."""
    result = await db.execute(
        select(UserInteractionModel).where(
            UserInteractionModel.user_id == current_user.id,
            UserInteractionModel.article_id == interaction.article_id
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        for field, value in interaction.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        
        if interaction.opened and not existing.opened_at:
            existing.opened_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(existing)
        
        await _update_user_model(db, current_user.id, existing)
        
        return existing
    else:
        new_interaction = UserInteractionModel(
            user_id=current_user.id,
            article_id=interaction.article_id,
            **interaction.model_dump(exclude_unset=True)
        )
        
        if interaction.opened:
            new_interaction.opened_at = datetime.now(timezone.utc)
        
        db.add(new_interaction)
        await db.commit()
        await db.refresh(new_interaction)
        
        await _update_user_model(db, current_user.id, new_interaction)
        
        return new_interaction


@router.post("/me/feedback")
async def submit_feedback(
    feedback: ArticleFeedback,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Submit simple feedback for an article."""
    feedback_map = {
        "like": {"rating": 1},
        "dislike": {"rating": -1},
        "save": {"saved": True},
        "dismiss": {"dismissed": True},
    }
    
    if feedback.feedback not in feedback_map:
        raise HTTPException(status_code=400, detail="Invalid feedback type")
    
    updates = feedback_map[feedback.feedback]
    
    result = await db.execute(
        select(UserInteractionModel).where(
            UserInteractionModel.user_id == current_user.id,
            UserInteractionModel.article_id == feedback.article_id
        )
    )
    interaction = result.scalar_one_or_none()
    
    if interaction:
        for field, value in updates.items():
            setattr(interaction, field, value)
    else:
        interaction = UserInteractionModel(
            user_id=current_user.id,
            article_id=feedback.article_id,
            **updates
        )
        db.add(interaction)
    
    await db.commit()
    
    await _update_user_model(db, current_user.id, interaction)
    
    logger.info(
        "feedback_submitted",
        user_id=current_user.id,
        article_id=feedback.article_id,
        feedback=feedback.feedback
    )
    
    return {"success": True}


@router.get("/me/history", response_model=List[dict])
async def get_reading_history(
    limit: int = 20,
    saved_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get user's reading history."""
    query = select(UserInteractionModel).where(
        UserInteractionModel.user_id == current_user.id
    ).order_by(desc(UserInteractionModel.created_at)).limit(limit)
    
    if saved_only:
        query = query.where(UserInteractionModel.saved == True)
    
    result = await db.execute(query)
    interactions = result.scalars().all()
    
    return [
        {
            "id": i.id,
            "article_id": i.article_id,
            "read_duration_seconds": i.read_duration_seconds,
            "read_duration": i.read_duration_seconds,
            "rating": i.rating,
            "saved": i.saved,
            "created_at": i.created_at
        }
        for i in interactions
    ]


async def _update_user_model(
    db: AsyncSession,
    user_id: str,
    interaction: UserInteractionModel
):
    """Update user model based on interaction."""
    # Get user preferences
    result = await db.execute(
        select(UserPreferencesModel).where(UserPreferencesModel.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()
    
    if not prefs or not prefs.auto_adjust_interests:
        return
    
    result = await db.execute(
        select(ArticleModel).where(ArticleModel.id == interaction.article_id)
    )
    article = result.scalar_one_or_none()
    
    if not article:
        return
    
    # Update preferences
    trainer = get_user_model_trainer()
    trainer.update_from_interaction(
        prefs,
        article,
        rating=interaction.rating or 0,
        read_duration=interaction.read_duration_seconds,
        saved=interaction.saved,
        dismissed=interaction.dismissed
    )
    
    await db.commit()


# ========== Personalized Digests ==========

@router.post("/me/digest/generate", response_model=PersonalizedDigestResponse)
async def generate_personalized_digest(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Generate a personalized digest for the current user."""
    prefs_result = await db.execute(
        select(UserPreferencesModel).where(UserPreferencesModel.user_id == current_user.id)
    )
    prefs = prefs_result.scalar_one_or_none()
    
    if not prefs:
        prefs = UserPreferencesModel(user_id=current_user.id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    
    result = await db.execute(
        select(ArticleModel)
        .where(ArticleModel.published_at >= cutoff)
        .where(ArticleModel.is_processed == True)
        .order_by(desc(ArticleModel.published_at))
        .limit(100)
    )
    articles = result.scalars().all()
    
    result = await db.execute(
        select(UserInteractionModel.article_id).where(
            UserInteractionModel.user_id == current_user.id
        )
    )
    sent_ids = {row[0] for row in result.all()}
    
    new_articles = [a for a in articles if a.id not in sent_ids]
    
    engine = get_personalization_engine()
    
    filtered = engine.filter_articles(new_articles, prefs)
    
    limit = prefs.daily_article_limit or 10
    scored = engine.rank_articles(filtered, prefs, limit=limit)
    
    article_ids = [s.article.id for s in scored]
    article_scores = {str(s.article.id): s.score for s in scored}

    now = datetime.now(timezone.utc)
    categories = [s.article.category for s in scored if s.article.category]
    if categories:
        counts = Counter(categories)
        total = sum(counts.values())
        probs = [c / total for c in counts.values()]
        max_entropy = math.log(len(probs)) if len(probs) > 1 else 1.0
        entropy = -sum(p * math.log(p) for p in probs if p > 0)
        diversity_score = entropy / max_entropy if max_entropy > 0 else 0.0
    else:
        diversity_score = 0.0

    ages = []
    for s in scored:
        if s.article.published_at:
            age_hours = (now - s.article.published_at).total_seconds() / 3600
            ages.append(age_hours)
    if ages:
        max_age = 7 * 24
        freshness_score = 1.0 - min(sum(ages) / len(ages) / max_age, 1.0)
    else:
        freshness_score = 0.0

    digest = PersonalizedDigestModel(
        user_id=current_user.id,
        article_ids=article_ids,
        article_scores=article_scores,
        personalization_score=sum(s.score for s in scored) / len(scored) if scored else 0,
        diversity_score=round(diversity_score, 4),
        freshness_score=round(freshness_score, 4),
    )
    
    db.add(digest)
    await db.commit()
    await db.refresh(digest)
    
    for article_id in article_ids:
        interaction = UserInteractionModel(
            user_id=current_user.id,
            article_id=article_id,
            digest_id=digest.id,
            delivered_at=datetime.now(timezone.utc)
        )
        db.add(interaction)
    
    await db.commit()
    
    logger.info(
        "personalized_digest_generated",
        user_id=current_user.id,
        digest_id=digest.id,
        article_count=len(article_ids),
        avg_score=round(digest.personalization_score, 3)
    )
    
    response_articles = []
    for s in scored:
        response_articles.append({
            "id": s.article.id,
            "title": s.article.title,
            "source": s.article.source,
            "category": s.article.category,
            "published_at": s.article.published_at.isoformat() if s.article.published_at else None,
            "score": s.score,
            "score_breakdown": s.score_breakdown
        })
    
    return {
        "id": digest.id,
        "created_at": digest.created_at,
        "articles": response_articles,
        "personalization_score": digest.personalization_score,
        "diversity_score": digest.diversity_score,
        "status": digest.status,
        "sent_at": digest.sent_at
    }


@router.get("/me/digests", response_model=List[PersonalizedDigestResponse])
async def get_user_digests(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get user's personalized digests."""
    result = await db.execute(
        select(PersonalizedDigestModel)
        .where(PersonalizedDigestModel.user_id == current_user.id)
        .order_by(desc(PersonalizedDigestModel.created_at))
        .limit(limit)
    )
    digests = result.scalars().all()
    
    return [
        {
            "id": d.id,
            "created_at": d.created_at,
            "articles": d.article_ids,
            "personalization_score": d.personalization_score,
            "diversity_score": d.diversity_score,
            "status": d.status,
            "sent_at": d.sent_at
        }
        for d in digests
    ]


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/me/password")
async def change_password(
    request: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Change the current user's password."""
    if not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth users cannot change password"
        )
    
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    current_user.password_hash = get_password_hash(request.new_password)
    await db.commit()
    
    logger.info("password_changed", user_id=current_user.id)
    return {"message": "Password changed successfully"}
