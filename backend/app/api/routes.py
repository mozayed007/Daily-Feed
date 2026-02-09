"""Main API routes"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import (
    Database, ArticleModel, SourceModel, DigestModel, SettingModel,
    ArticleResponse, ArticleListResponse, SourceResponse, SourceCreate,
    DigestResponse, StatsResponse
)
from app.agents.retriever import FeedRetrieverAgent, SourceConfig
from app.agents.summarizer import SummarizerAgent
from app.agents.critic import QualityCriticAgent
from app.agents.delivery import DeliveryAgent
from app.core.llm_client import LLMClientFactory
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


# Dependency
async def get_db():
    async with Database.get_session() as session:
        yield session


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    providers = await LLMClientFactory.get_available_providers()
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "llm_providers": providers
    }


@router.get("/sources", response_model=List[SourceResponse])
async def get_sources(db: AsyncSession = Depends(get_db)):
    """Get all enabled sources"""
    result = await db.execute(
        select(SourceModel).where(SourceModel.enabled == True)
    )
    sources = result.scalars().all()
    return [SourceResponse.model_validate(s) for s in sources]


@router.post("/sources/fetch")
async def fetch_sources(
    source_ids: Optional[List[int]] = None, 
    background_tasks: BackgroundTasks = None
):
    """Trigger fetch for sources (runs in background)"""
    from app.tools.fetch_tool import FetchTool
    
    async def run_fetch(ids):
        tool = FetchTool()
        await tool.execute(source_ids=ids)
    
    if background_tasks is not None:
        background_tasks.add_task(run_fetch, source_ids)
        return {"message": "Fetch started in background"}
    else:
        # Run synchronously if no background tasks available
        await run_fetch(source_ids)
        return {"message": "Fetch completed"}


# Articles
@router.get("/articles", response_model=ArticleListResponse)
async def get_articles(
    processed: Optional[bool] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get articles with filtering and pagination"""
    
    query = select(ArticleModel)
    
    if processed is not None:
        query = query.where(ArticleModel.is_processed == processed)
    if category:
        query = query.where(ArticleModel.category == category)
    if source:
        query = query.where(ArticleModel.source == source)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Get paginated results
    query = query.order_by(desc(ArticleModel.fetched_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    articles = result.scalars().all()
    
    return ArticleListResponse(
        articles=[ArticleResponse.model_validate(a) for a in articles],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single article"""
    result = await db.execute(
        select(ArticleModel).where(ArticleModel.id == article_id)
    )
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return ArticleResponse.model_validate(article)


@router.post("/articles/{article_id}/summarize")
async def summarize_article(
    article_id: int, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger summarization for a single article"""
    result = await db.execute(
        select(ArticleModel).where(ArticleModel.id == article_id)
    )
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Run summarization
    llm_client = LLMClientFactory.create()
    summarizer = SummarizerAgent()
    critic = QualityCriticAgent(llm_client, settings.CRITIC_MIN_SCORE)
    
    summary = await summarizer.summarize_article(article)
    critique = await critic.critique(summary, article)
    
    if critique.passed:
        article.summary = summary.text
        article.category = summary.category
        article.sentiment = summary.sentiment
        article.reading_time = summary.reading_time
        article.key_points = summary.key_points
        article.is_processed = True
        article.critic_score = critique.score
        
        await db.commit()
        
        return {
            "success": True,
            "score": critique.score,
            "summary": summary.text
        }
    else:
        return {
            "success": False,
            "score": critique.score,
            "issues": critique.issues
        }


# Sources


@router.post("/sources", response_model=SourceResponse)
async def create_source(source: SourceCreate, db: AsyncSession = Depends(get_db)):
    """Create a new RSS source"""
    
    # Check if URL already exists
    existing = await db.execute(
        select(SourceModel).where(SourceModel.url == source.url)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Source URL already exists")
    
    new_source = SourceModel(
        name=source.name,
        url=source.url,
        category=source.category,
        enabled=source.enabled
    )
    db.add(new_source)
    await db.commit()
    await db.refresh(new_source)
    
    return SourceResponse.model_validate(new_source)


@router.put("/sources/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int, 
    source_update: SourceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update an RSS source"""
    result = await db.execute(
        select(SourceModel).where(SourceModel.id == source_id)
    )
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    source.name = source_update.name
    source.url = source_update.url
    source.category = source_update.category
    source.enabled = source_update.enabled
    
    await db.commit()
    await db.refresh(source)
    
    return SourceResponse.model_validate(source)


@router.delete("/sources/{source_id}")
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an RSS source"""
    result = await db.execute(
        select(SourceModel).where(SourceModel.id == source_id)
    )
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    await db.delete(source)
    await db.commit()
    
    return {"success": True, "message": "Source deleted"}


@router.post("/sources/{source_id}/fetch")
async def fetch_source(
    source_id: int, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Fetch articles from a specific source"""
    result = await db.execute(
        select(SourceModel).where(SourceModel.id == source_id)
    )
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Fetch in background
    retriever = FeedRetrieverAgent()
    config = SourceConfig(
        name=source.name,
        url=source.url,
        category=source.category,
        enabled=source.enabled
    )
    
    articles = await retriever.fetch_source(config)
    
    # Save articles
    saved_count = 0
    for article_data in articles:
        existing = await db.execute(
            select(ArticleModel).where(ArticleModel.url == article_data.url)
        )
        if not existing.scalar_one_or_none():
            article = ArticleModel(
                title=article_data.title,
                url=article_data.url,
                content=article_data.content,
                source=article_data.source,
                category=article_data.category,
                published_at=article_data.published_at
            )
            db.add(article)
            saved_count += 1
    
    # Update source stats
    source.last_fetch = datetime.now(timezone.utc).replace(tzinfo=None)
    source.fetch_count += saved_count
    await db.commit()
    
    return {
        "success": True,
        "fetched": len(articles),
        "saved": saved_count
    }


# Pipeline operations
@router.post("/pipeline/fetch")
async def run_fetch_pipeline(db: AsyncSession = Depends(get_db)):
    """Run the fetch pipeline for all enabled sources"""
    retriever = FeedRetrieverAgent(settings.MAX_ARTICLES_PER_SOURCE)
    
    try:
        articles = await retriever.fetch_all_sources(db)
        return {
            "success": True,
            "articles_fetched": len(articles)
        }
    except Exception as e:
        logger.error(f"Fetch pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await retriever.close()


@router.post("/pipeline/process")
async def run_process_pipeline(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Run the summarization pipeline for unprocessed articles"""
    
    # Get unprocessed articles
    result = await db.execute(
        select(ArticleModel)
        .where(ArticleModel.is_processed == False)
        .order_by(desc(ArticleModel.fetched_at))
        .limit(limit)
    )
    articles = result.scalars().all()
    
    if not articles:
        return {"success": True, "processed": 0, "message": "No unprocessed articles"}
    
    # Initialize agents
    llm_client = LLMClientFactory.create()
    summarizer = SummarizerAgent()
    critic = QualityCriticAgent(llm_client, settings.CRITIC_MIN_SCORE)
    
    processed = 0
    rejected = 0
    
    for article in articles:
        try:
            async with db.begin_nested():
                summary = await summarizer.summarize_article(article)
                critique = await critic.critique(summary, article)
                
                if critique.passed:
                    article.summary = summary.text
                    article.category = summary.category
                    article.sentiment = summary.sentiment
                    article.reading_time = summary.reading_time
                    article.key_points = summary.key_points
                    article.is_processed = True
                    article.critic_score = critique.score
                    processed += 1
                else:
                    rejected += 1
                    logger.info(f"Article {article.id} rejected by quality critic (score={critique.score})")
                
        except Exception as e:
            logger.error(f"Error processing article {article.id}: {e}")
    
    await db.commit()
    
    return {
        "success": True,
        "processed": processed,
        "rejected": rejected,
        "total": len(articles)
    }


@router.post("/pipeline/digest")
async def create_digest(
    hours: int = Query(24, ge=1, le=168),
    deliver: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Create a digest from recent processed articles"""
    
    # Get recent processed articles
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
    result = await db.execute(
        select(ArticleModel)
        .where(ArticleModel.is_processed == True)
        .where(ArticleModel.fetched_at >= cutoff)
        .order_by(desc(ArticleModel.fetched_at))
        .limit(settings.MAX_ARTICLES_PER_SOURCE)
    )
    articles = result.scalars().all()
    
    if not articles:
        return {"success": True, "message": "No articles for digest"}
    
    # Create digest
    delivery_agent = DeliveryAgent()
    digest = delivery_agent.create_digest(list(articles))
    
    # Save to database
    digest_model = DigestModel(
        article_count=len(articles),
        content=digest.content
    )
    db.add(digest_model)
    await db.flush()  # Get the ID
    
    # Associate articles
    for article in articles:
        article.digest_id = digest_model.id
    
    await db.commit()
    await db.refresh(digest_model)
    
    # Deliver if requested
    if deliver and settings.TELEGRAM_BOT_TOKEN:
        success = await delivery_agent.deliver_telegram(digest)
        if success:
            digest_model.delivered = True
            digest_model.delivered_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await db.commit()
    
    return {
        "success": True,
        "digest_id": digest_model.id,
        "article_count": len(articles),
        "delivered": digest_model.delivered
    }


# Digests
@router.get("/digests", response_model=List[DigestResponse])
async def get_digests(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get recent digests"""
    result = await db.execute(
        select(DigestModel)
        .order_by(desc(DigestModel.created_at))
        .limit(limit)
    )
    digests = result.scalars().all()
    return [DigestResponse.model_validate(d) for d in digests]


@router.get("/digests/{digest_id}", response_model=DigestResponse)
async def get_digest(digest_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific digest with articles"""
    result = await db.execute(
        select(DigestModel).where(DigestModel.id == digest_id)
    )
    digest = result.scalar_one_or_none()
    
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    
    # Load articles
    articles_result = await db.execute(
        select(ArticleModel).where(ArticleModel.digest_id == digest_id)
    )
    digest.articles = articles_result.scalars().all()
    
    return DigestResponse.model_validate(digest)


# Stats
@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get system statistics"""
    
    # Article counts
    total_result = await db.execute(select(func.count()).select_from(ArticleModel))
    total = total_result.scalar()
    
    processed_result = await db.execute(
        select(func.count())
        .select_from(ArticleModel)
        .where(ArticleModel.is_processed == True)
    )
    processed = processed_result.scalar()
    
    # Source counts
    sources_result = await db.execute(select(func.count()).select_from(SourceModel))
    total_sources = sources_result.scalar()
    
    active_result = await db.execute(
        select(func.count())
        .select_from(SourceModel)
        .where(SourceModel.enabled == True)
    )
    active_sources = active_result.scalar()
    
    # Digest count
    digests_result = await db.execute(select(func.count()).select_from(DigestModel))
    total_digests = digests_result.scalar()
    
    # Categories
    cat_result = await db.execute(
        select(ArticleModel.category, func.count())
        .where(ArticleModel.category.isnot(None))
        .group_by(ArticleModel.category)
    )
    categories = {cat: count for cat, count in cat_result.all()}
    
    # Recent activity (last 5 articles)
    recent_result = await db.execute(
        select(ArticleModel)
        .order_by(desc(ArticleModel.fetched_at))
        .limit(5)
    )
    recent = [
        {
            "id": a.id,
            "title": a.title,
            "source": a.source,
            "action": "processed" if a.is_processed else "fetched",
            "time": a.fetched_at.isoformat()
        }
        for a in recent_result.scalars().all()
    ]
    
    return StatsResponse(
        total_articles=total,
        processed_articles=processed,
        unprocessed_articles=total - processed,
        total_digests=total_digests,
        total_sources=total_sources,
        active_sources=active_sources,
        categories=categories,
        recent_activity=recent
    )


# Settings
@router.get("/settings")
async def get_settings_endpoint():
    """Get current settings (safe values only)"""
    return {
        "llm_provider": settings.LLM_PROVIDER,
        "ollama_model": settings.OLLAMA_MODEL,
        "telegram_configured": bool(settings.TELEGRAM_BOT_TOKEN),
        "scheduler_enabled": settings.SCHEDULER_ENABLED,
        "digest_time": f"{settings.DIGEST_HOUR:02d}:{settings.DIGEST_MINUTE:02d}",
        "max_articles": settings.MAX_ARTICLES_PER_SOURCE,
        "critic_min_score": settings.CRITIC_MIN_SCORE
    }
