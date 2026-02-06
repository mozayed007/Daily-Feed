"""User management and personalization API routes."""

from typing import List, Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import (
    UserModel, UserPreferencesModel, UserInteractionModel, PersonalizedDigestModel,
    UserCreate, UserResponse, UserPreferencesUpdate, UserPreferencesResponse,
    UserInteractionCreate, UserInteractionResponse, ArticleFeedback,
    PersonalizedDigestResponse, OnboardingData, UserStats
)
from app.core.personalization import (
    get_personalization_engine, get_user_model_trainer, ScoredArticle
)
from app.core.logging_config import get_logger

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger(__name__)


# ========== User Management ==========

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user account."""
    # Check if email exists
    result = await db.execute(
        select(UserModel).where(UserModel.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = UserModel(
        email=user_data.email,
        name=user_data.name,
        # Password handling would go here for real auth
    )
    db.add(user)
    await db.flush()  # Get user.id
    
    # Create default preferences
    prefs = UserPreferencesModel(user_id=user.id)
    db.add(prefs)
    
    await db.commit()
    
    logger.info("user_created", user_id=user.id, email=user_data.email)
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user(db: AsyncSession = Depends(get_db)):
    """Get current user profile.
    
    For PoC, returns the first user. In production, use auth.
    """
    result = await db.execute(select(UserModel).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="No user found")
    
    return user


@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(db: AsyncSession = Depends(get_db)):
    """Get user engagement statistics."""
    # Get user
    result = await db.execute(select(UserModel).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="No user found")
    
    # Total articles read (read_duration > 30s)
    result = await db.execute(
        select(func.count()).where(
            UserInteractionModel.user_id == user.id,
            UserInteractionModel.read_duration_seconds > 30
        )
    )
    total_read = result.scalar() or 0
    
    # Total saved
    result = await db.execute(
        select(func.count()).where(
            UserInteractionModel.user_id == user.id,
            UserInteractionModel.saved == True
        )
    )
    total_saved = result.scalar() or 0
    
    # Average reading time
    result = await db.execute(
        select(func.avg(UserInteractionModel.read_duration_seconds)).where(
            UserInteractionModel.user_id == user.id
        )
    )
    avg_reading_time = int(result.scalar() or 0)
    
    # Favorite topics
    result = await db.execute(
        select(UserInteractionModel.article_id)
        .where(
            UserInteractionModel.user_id == user.id,
            UserInteractionModel.read_duration_seconds > 30
        )
    )
    # This would need a join with articles table
    # Simplified for now
    favorite_topics = []
    
    # Digest open rate
    result = await db.execute(
        select(func.count()).where(PersonalizedDigestModel.user_id == user.id)
    )
    total_digests = result.scalar() or 0
    
    result = await db.execute(
        select(func.count()).where(
            PersonalizedDigestModel.user_id == user.id,
            PersonalizedDigestModel.opened == True
        )
    )
    opened_digests = result.scalar() or 0
    
    open_rate = (opened_digests / total_digests * 100) if total_digests > 0 else 0
    
    # Last 7 days activity
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    result = await db.execute(
        select(func.date(UserInteractionModel.created_at), func.count())
        .where(
            UserInteractionModel.user_id == user.id,
            UserInteractionModel.created_at >= seven_days_ago,
            UserInteractionModel.read_duration_seconds > 30
        )
        .group_by(func.date(UserInteractionModel.created_at))
    )
    activity_by_day = {row[0]: row[1] for row in result.all()}
    
    last_7_days = []
    for i in range(7):
        day = (datetime.now(timezone.utc) - timedelta(days=i)).date()
        last_7_days.insert(0, activity_by_day.get(day, 0))
    
    return UserStats(
        total_articles_read=total_read,
        total_articles_saved=total_saved,
        average_reading_time=avg_reading_time,
        favorite_topics=favorite_topics,
        favorite_sources=[],
        digest_open_rate=round(open_rate, 1),
        last_7_days_activity=last_7_days
    )


# ========== Onboarding ==========

@router.post("/onboarding", response_model=UserResponse)
async def complete_onboarding(data: OnboardingData, db: AsyncSession = Depends(get_db)):
    """Complete user onboarding and set initial preferences."""
    # Get or create user
    result = await db.execute(select(UserModel).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = UserModel(
            email=f"user_{datetime.now(timezone.utc).timestamp()}@local",
            name=data.name
        )
        db.add(user)
        await db.flush()
        
        prefs = UserPreferencesModel(user_id=user.id)
        db.add(prefs)
    else:
        # Update existing user
        prefs_result = await db.execute(
            select(UserPreferencesModel).where(
                UserPreferencesModel.user_id == user.id
            )
        )
        prefs = prefs_result.scalar_one_or_none()
        if not prefs:
            prefs = UserPreferencesModel(user_id=user.id)
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
    user.name = data.name
    user.onboarding_completed = True
    
    await db.commit()
    
    logger.info(
        "onboarding_completed",
        user_id=user.id,
        interests=data.interests,
        sources=data.preferred_sources
    )
    
    return user


# ========== Preferences ==========

@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_preferences(db: AsyncSession = Depends(get_db)):
    """Get user preferences."""
    result = await db.execute(select(UserModel).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="No user found")
    
    prefs_result = await db.execute(
        select(UserPreferencesModel).where(UserPreferencesModel.user_id == user.id)
    )
    prefs = prefs_result.scalar_one_or_none()
    
    if not prefs:
        # Create default preferences
        prefs = UserPreferencesModel(user_id=user.id)
        db.add(prefs)
        await db.commit()
    
    return prefs


@router.patch("/me/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    update: UserPreferencesUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update user preferences."""
    result = await db.execute(select(UserModel).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="No user found")
    
    prefs_result = await db.execute(
        select(UserPreferencesModel).where(UserPreferencesModel.user_id == user.id)
    )
    prefs = prefs_result.scalar_one_or_none()
    
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    # Update fields
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prefs, field, value)
    
    await db.commit()
    await db.refresh(prefs)
    
    logger.info("preferences_updated", user_id=user.id, changes=list(update_data.keys()))
    
    return prefs


# ========== Interactions & Feedback ==========

@router.post("/me/interactions", response_model=UserInteractionResponse)
async def record_interaction(
    interaction: UserInteractionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Record user interaction with an article."""
    result = await db.execute(select(UserModel).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="No user found")
    
    # Check if interaction exists
    result = await db.execute(
        select(UserInteractionModel).where(
            UserInteractionModel.user_id == user.id,
            UserInteractionModel.article_id == interaction.article_id
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing
        for field, value in interaction.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        
        # Update opened_at if opened
        if interaction.opened and not existing.opened_at:
            existing.opened_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(existing)
        
        # Update user model
        await _update_user_model(db, user.id, existing)
        
        return existing
    else:
        # Create new
        new_interaction = UserInteractionModel(
            user_id=user.id,
            article_id=interaction.article_id,
            **interaction.model_dump(exclude_unset=True)
        )
        
        if interaction.opened:
            new_interaction.opened_at = datetime.now(timezone.utc)
        
        db.add(new_interaction)
        await db.commit()
        await db.refresh(new_interaction)
        
        # Update user model
        await _update_user_model(db, user.id, new_interaction)
        
        return new_interaction


@router.post("/me/feedback")
async def submit_feedback(
    feedback: ArticleFeedback,
    db: AsyncSession = Depends(get_db)
):
    """Submit simple feedback for an article."""
    result = await db.execute(select(UserModel).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="No user found")
    
    # Map feedback strings to interaction fields
    feedback_map = {
        "like": {"rating": 1},
        "dislike": {"rating": -1},
        "save": {"saved": True},
        "dismiss": {"dismissed": True},
    }
    
    if feedback.feedback not in feedback_map:
        raise HTTPException(status_code=400, detail="Invalid feedback type")
    
    updates = feedback_map[feedback.feedback]
    
    # Get or create interaction
    result = await db.execute(
        select(UserInteractionModel).where(
            UserInteractionModel.user_id == user.id,
            UserInteractionModel.article_id == feedback.article_id
        )
    )
    interaction = result.scalar_one_or_none()
    
    if interaction:
        for field, value in updates.items():
            setattr(interaction, field, value)
    else:
        interaction = UserInteractionModel(
            user_id=user.id,
            article_id=feedback.article_id,
            **updates
        )
        db.add(interaction)
    
    await db.commit()
    
    # Update user model
    await _update_user_model(db, user.id, interaction)
    
    logger.info(
        "feedback_submitted",
        user_id=user.id,
        article_id=feedback.article_id,
        feedback=feedback.feedback
    )
    
    return {"success": True}


@router.get("/me/history", response_model=List[dict])
async def get_reading_history(
    limit: int = 20,
    saved_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get user's reading history."""
    result = await db.execute(select(UserModel).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="No user found")
    
    query = select(UserInteractionModel).where(
        UserInteractionModel.user_id == user.id
    ).order_by(desc(UserInteractionModel.created_at)).limit(limit)
    
    if saved_only:
        query = query.where(UserInteractionModel.saved == True)
    
    result = await db.execute(query)
    interactions = result.scalars().all()
    
    return [
        {
            "id": i.id,
            "article_id": i.article_id,
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
    
    # Get article
    from app.database import ArticleModel
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
async def generate_personalized_digest(db: AsyncSession = Depends(get_db)):
    """Generate a personalized digest for the current user."""
    result = await db.execute(select(UserModel).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="No user found")
    
    # Get user preferences
    prefs_result = await db.execute(
        select(UserPreferencesModel).where(UserPreferencesModel.user_id == user.id)
    )
    prefs = prefs_result.scalar_one_or_none()
    
    if not prefs:
        raise HTTPException(status_code=404, detail="User preferences not found")
    
    # Get recent unprocessed articles
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    
    result = await db.execute(
        select(ArticleModel)
        .where(ArticleModel.published_at >= cutoff)
        .where(ArticleModel.is_processed == True)
        .order_by(desc(ArticleModel.published_at))
        .limit(100)
    )
    articles = result.scalars().all()
    
    # Filter already sent articles
    result = await db.execute(
        select(UserInteractionModel.article_id).where(
            UserInteractionModel.user_id == user.id
        )
    )
    sent_ids = {row[0] for row in result.all()}
    
    new_articles = [a for a in articles if a.id not in sent_ids]
    
    # Personalize
    engine = get_personalization_engine()
    
    # First filter
    filtered = engine.filter_articles(new_articles, prefs)
    
    # Then rank
    limit = prefs.daily_article_limit or 10
    scored = engine.rank_articles(filtered, prefs, limit=limit)
    
    # Create digest
    article_ids = [s.article.id for s in scored]
    article_scores = {str(s.article.id): s.score for s in scored}
    
    digest = PersonalizedDigestModel(
        user_id=user.id,
        article_ids=article_ids,
        article_scores=article_scores,
        personalization_score=sum(s.score for s in scored) / len(scored) if scored else 0,
        diversity_score=0.0,  # Would calculate from topic distribution
        freshness_score=0.0,  # Would calculate from age distribution
    )
    
    db.add(digest)
    await db.commit()
    await db.refresh(digest)
    
    # Create interaction records for tracking
    for article_id in article_ids:
        interaction = UserInteractionModel(
            user_id=user.id,
            article_id=article_id,
            digest_id=digest.id,
            delivered_at=datetime.now(timezone.utc)
        )
        db.add(interaction)
    
    await db.commit()
    
    logger.info(
        "personalized_digest_generated",
        user_id=user.id,
        digest_id=digest.id,
        article_count=len(article_ids),
        avg_score=round(digest.personalization_score, 3)
    )
    
    # Build response with article details
    response_articles = []
    for s in scored:
        response_articles.append({
            "id": s.article.id,
            "title": s.article.title,
            "source": s.article.source_name,
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
    db: AsyncSession = Depends(get_db)
):
    """Get user's personalized digests."""
    result = await db.execute(select(UserModel).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="No user found")
    
    result = await db.execute(
        select(PersonalizedDigestModel)
        .where(PersonalizedDigestModel.user_id == user.id)
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
