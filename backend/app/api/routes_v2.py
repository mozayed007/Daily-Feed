"""
API Routes v2 - Updated for new agent loop architecture
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import (
    get_db, Database, ArticleModel, SourceModel, DigestModel,
    ArticleResponse, ArticleListResponse, SourceResponse, SourceCreate,
    DigestResponse, StatsResponse
)
from app.ai.orchestrator import get_orchestrator
from app.core.scheduler import get_scheduler
from app.core.memory import get_memory_store
from app.core.config_manager import get_config_manager, get_config
from app.api.user_routes import router as user_router
from app.api.deps import get_current_user
from app.models.user import UserModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Include user routes
router.include_router(user_router)


# ========== Pydantic Models ==========

class JobConfig(BaseModel):
    name: str = Field(..., description="Job name")
    type: str = Field(default="fetch", description="Pipeline type: fetch, process, or digest")
    cron: Optional[str] = Field(default=None, description="Cron expression (e.g., '0 8 * * *')")
    interval: Optional[int] = Field(default=None, ge=1, description="Interval in seconds (alias for interval_seconds)")
    interval_seconds: Optional[int] = Field(default=None, ge=1, description="Interval in seconds")
    enabled: bool = Field(default=True, description="Whether job is enabled")


class JobToggle(BaseModel):
    enabled: bool = Field(..., description="Enable or disable the job")


# ========== Health & Status ==========

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    orchestrator = get_orchestrator()
    config = get_config()
    status = await orchestrator.get_llm_status()

    return {
        "status": "healthy",
        "version": config.version,
        "ai_providers": status["providers"],
        "litellm_available": status["litellm_available"],
        "agents": ["summarize", "critique", "cluster", "synthesize", "digest_reason", "trend"],
        "graphs": ["article_processing", "digest_generation", "full_pipeline"],
        "scheduler_running": get_scheduler().is_running,
    }


# ========== Articles ==========

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


# ========== Article Categories ==========

@router.get("/articles/categories")
async def get_article_categories(db: AsyncSession = Depends(get_db)):
    """Get distinct article categories with counts"""
    result = await db.execute(
        select(ArticleModel.category, func.count().label("cnt"))
        .where(ArticleModel.category.isnot(None))
        .group_by(ArticleModel.category)
        .order_by(desc("cnt"))
    )
    return [{"name": row[0], "count": row[1]} for row in result.all()]


@router.get("/articles/search")
async def search_articles(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Search articles by title, summary, or content using SQLite LIKE."""
    search_term = f"%{q}%"

    result = await db.execute(
        select(ArticleModel)
        .where(
            (ArticleModel.title.ilike(search_term))
            | (ArticleModel.summary.ilike(search_term))
            | (ArticleModel.content.ilike(search_term))
        )
        .order_by(desc(ArticleModel.fetched_at))
        .limit(limit)
    )
    articles = result.scalars().all()

    return {
        "query": q,
        "articles": [ArticleResponse.model_validate(a) for a in articles],
        "total": len(articles)
    }


# ========== Sources ==========

@router.get("/sources", response_model=List[SourceResponse])
async def get_sources(
    enabled_only: bool = Query(True, description="Filter to enabled sources only"),
    db: AsyncSession = Depends(get_db)
):
    """Get RSS sources"""
    query = select(SourceModel)
    if enabled_only:
        query = query.where(SourceModel.enabled == True)
    result = await db.execute(query)
    sources = result.scalars().all()
    return [SourceResponse.model_validate(s) for s in sources]


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
    
    # Check if new URL conflicts with another source
    if source_update.url != source.url:
        existing = await db.execute(
            select(SourceModel).where(SourceModel.url == source_update.url)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Source URL already exists")
    
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


@router.post("/sources/fetch")
async def fetch_all_sources(
    source_ids: Optional[List[int]] = None,
    background_tasks: BackgroundTasks = None
):
    """Trigger fetch for all or specified sources"""
    from app.tools.fetch_tool import FetchTool
    
    async def run_fetch(ids):
        tool = FetchTool()
        await tool.execute(source_ids=ids)
    
    if background_tasks is not None:
        background_tasks.add_task(run_fetch, source_ids)
        return {"message": "Fetch started in background"}
    else:
        await run_fetch(source_ids)
        return {"message": "Fetch completed"}


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
    
    from app.tools.fetch_tool import FetchTool
    
    async def run_fetch():
        tool = FetchTool()
        await tool.execute(source_ids=[source_id])
    
    background_tasks.add_task(run_fetch)
    return {"message": f"Fetch started for source {source_id}"}


# ========== Agent Loop / Pipelines ==========

@router.post("/pipeline/{task_type}")
async def run_pipeline(
    task_type: str,
    background_tasks: BackgroundTasks,
    params: Optional[Dict[str, Any]] = None
):
    """
    Run a pipeline task using the AI orchestrator.

    Available task types:
    - fetch: Fetch articles from sources
    - process: Process/summarize unprocessed articles via graph
    - digest: Create and deliver digest via graph
    - full: Run complete pipeline (fetch -> process -> digest) via graph
    - memory_sync: Sync articles to memory
    - trends: Detect emerging trends
    - cluster: Cluster articles by topic
    - synthesize: Synthesize multiple sources on a topic
    """
    orchestrator = get_orchestrator()
    params = params or {}

    try:
        result = await orchestrator.run_pipeline(task_type, **params)
        return {
            "success": result.get("success", False),
            "task_type": task_type,
            "result": result
        }
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail="Pipeline execution failed")


@router.get("/tools")
async def list_tools():
    """List available AI capabilities"""
    return {
        "agents": [
            {"name": "summarize", "description": "Summarize articles with structured output"},
            {"name": "critique", "description": "Critique summary quality"},
            {"name": "cluster", "description": "Group articles by topic"},
            {"name": "synthesize", "description": "Merge multi-source coverage"},
            {"name": "digest_reason", "description": "Explain why article is relevant"},
            {"name": "trend", "description": "Detect emerging trends"},
        ],
        "graphs": [
            {"name": "article_processing", "description": "Parallel summarize -> critique -> memory"},
            {"name": "digest_generation", "description": "Cluster -> synthesize -> deliver"},
            {"name": "full_pipeline", "description": "fetch -> process -> digest"},
        ],
    }


@router.post("/agents/{agent_name}")
async def run_agent(
    agent_name: str,
    params: Dict[str, Any],
    current_user: UserModel = Depends(get_current_user)
):
    """Execute a specific AI agent directly (requires authentication)"""
    orchestrator = get_orchestrator()

    allowed = {"summarize", "critique", "cluster", "synthesize", "trends"}
    if agent_name not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Agent '{agent_name}' is not allowed via API"
        )

    if agent_name == "summarize":
        result = await orchestrator.summarize(
            article_id=params.get("article_id", 0),
            style=params.get("style", "concise"),
        )
    elif agent_name == "critique":
        result = await orchestrator.critique(params.get("article_id", 0))
    elif agent_name == "cluster":
        result = await orchestrator.cluster(params.get("article_ids", []))
    elif agent_name == "synthesize":
        result = await orchestrator.synthesize(
            topic=params.get("topic", ""),
            article_ids=params.get("article_ids", []),
        )
    elif agent_name == "trends":
        result = await orchestrator.detect_trends(params.get("article_ids"))
    else:
        raise HTTPException(status_code=400, detail="Unknown agent")

    return result


# ========== Scheduler ==========

@router.get("/scheduler/jobs")
async def list_scheduled_jobs():
    """List all scheduled jobs"""
    scheduler = get_scheduler()
    jobs = scheduler.list_jobs()

    return {"jobs": jobs}


@router.post("/scheduler/jobs")
async def add_scheduled_job(job_config: JobConfig):
    """Add a new scheduled job with AI orchestrator pipeline callback"""
    scheduler = get_scheduler()
    orchestrator = get_orchestrator()

    job_type = job_config.type

    async def run_pipeline():
        return await orchestrator.run_pipeline(job_type)

    try:
        # Use interval if interval_seconds is None
        interval = job_config.interval_seconds or job_config.interval

        if job_config.cron:
            job = scheduler.add_cron_job(
                name=job_config.name,
                cron=job_config.cron,
                callback=run_pipeline,
            )
        elif interval:
            job = scheduler.add_interval_job(
                name=job_config.name,
                seconds=interval,
                callback=run_pipeline,
            )
        else:
            raise HTTPException(status_code=400, detail="Must specify cron or interval/interval_seconds")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"success": True, "job_id": job.id}


@router.patch("/scheduler/jobs/{job_id}")
async def toggle_scheduled_job(job_id: str, job_toggle: JobToggle):
    """Enable or disable a scheduled job"""
    scheduler = get_scheduler()

    if job_toggle.enabled:
        success = scheduler.enable_job(job_id)
    else:
        success = scheduler.disable_job(job_id)

    if not success:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"success": True, "job_id": job_id, "enabled": job_toggle.enabled}


@router.post("/scheduler/start")
async def start_scheduler():
    """Start the scheduler"""
    scheduler = get_scheduler()
    await scheduler.start()
    return {"success": True, "message": "Scheduler started"}


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the scheduler"""
    scheduler = get_scheduler()
    await scheduler.stop()
    return {"success": True, "message": "Scheduler stopped"}


@router.delete("/scheduler/jobs/{job_id}")
async def delete_scheduled_job(job_id: str):
    """Remove a scheduled job"""
    scheduler = get_scheduler()
    removed = scheduler.remove_job(job_id)
    
    if not removed:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"success": True, "message": f"Job {job_id} removed"}


@router.post("/scheduler/jobs/{job_id}/run")
async def run_scheduled_job(job_id: str):
    """Manually trigger a scheduled job to run immediately"""
    scheduler = get_scheduler()
    job = scheduler.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status.value == "running":
        raise HTTPException(status_code=409, detail="Job is already running")
    
    # Run the job in the background
    asyncio.create_task(scheduler._execute_job(job))
    
    return {"success": True, "message": f"Job {job_id} triggered"}


# ========== Memory ==========

@router.get("/memory/stats")
async def get_memory_stats():
    """Get memory system statistics"""
    memory = get_memory_store()
    return memory.get_stats()


@router.get("/memory/interests")
async def get_memory_interests():
    """Get user interests from memory analysis"""
    memory = get_memory_store()
    return memory.get_user_interests()


@router.post("/memory/remember/{article_id}")
async def remember_article(article_id: int):
    """Store an article in memory"""
    memory = get_memory_store()
    
    from app.database import Database
    async with Database.get_session() as db:
        result = await db.execute(
            select(ArticleModel).where(ArticleModel.id == article_id)
        )
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        unit = memory.remember_article(
            article_id=article.id,
            title=article.title,
            summary=article.summary or "",
            category=article.category or "General",
            source=article.source,
            key_points=article.key_points or []
        )
        
        return {
            "success": True,
            "memory_id": unit.id,
            "category": unit.category
        }


@router.post("/memory/search")
async def search_memory(query: Dict[str, Any]):
    """Search memory for similar content"""
    memory = get_memory_store()
    
    results = memory.retrieve(
        category=query.get("category"),
        entities=query.get("entities"),
        limit=query.get("limit", 10)
    )
    
    return {
        "results": [r.to_dict() for r in results]
    }


# ========== Articles Single Operations ==========

@router.post("/articles/{article_id}/summarize")
async def summarize_single_article(
    article_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger summarization for a single article via pydantic-ai"""
    result = await db.execute(
        select(ArticleModel).where(ArticleModel.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Run summarization using AI orchestrator
    orchestrator = get_orchestrator()
    result = await orchestrator.summarize(article_id=article_id)

    if result.get("success"):
        data = result.get("data", {})
        return {
            "success": True,
            "score": data.get("critic_score"),
            "summary": data.get("summary"),
            "category": data.get("category"),
            "key_points": data.get("key_points"),
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Summarization failed"))


# ========== Digests ==========

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
    """Get a specific digest with its articles"""
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


# ========== AI Features ==========

class ClusterRequest(BaseModel):
    article_ids: List[int] = Field(..., description="Article IDs to cluster")


@router.post("/articles/cluster")
async def cluster_articles_endpoint(
    request: ClusterRequest,
    current_user: UserModel = Depends(get_current_user)
):
    """Cluster articles by topic using AI"""
    orchestrator = get_orchestrator()
    result = await orchestrator.cluster(request.article_ids)
    return result


class SynthesizeRequest(BaseModel):
    topic: str = Field(..., description="Topic to synthesize")
    article_ids: List[int] = Field(..., description="Article IDs covering the topic")


@router.post("/articles/synthesize")
async def synthesize_articles_endpoint(
    request: SynthesizeRequest,
    current_user: UserModel = Depends(get_current_user)
):
    """Synthesize multiple sources on a shared topic"""
    orchestrator = get_orchestrator()
    result = await orchestrator.synthesize(request.topic, request.article_ids)
    return result


@router.get("/articles/trends")
async def detect_trends_endpoint(
    article_ids: Optional[List[int]] = Query(None),
    current_user: UserModel = Depends(get_current_user)
):
    """Detect emerging trends from articles"""
    orchestrator = get_orchestrator()
    result = await orchestrator.detect_trends(article_ids)
    return result


@router.post("/articles/{article_id}/reason")
async def reason_article_inclusion(
    article_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Explain why an article is relevant to the current user"""
    from app.models.user import UserPreferencesModel

    # Get user preferences
    pref_result = await db.execute(
        select(UserPreferencesModel).where(UserPreferencesModel.user_id == current_user.id)
    )
    preferences = pref_result.scalar_one_or_none()

    if not preferences:
        raise HTTPException(status_code=400, detail="User has no preferences set")

    orchestrator = get_orchestrator()
    result = await orchestrator.reason_inclusion(article_id, preferences)
    return result


# ========== Stats ==========

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
        select(func.count()).select_from(SourceModel).where(SourceModel.enabled == True)
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
    
    # Recent activity
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
    
    # Memory stats
    memory = get_memory_store()
    mem_stats = memory.get_stats()
    
    return StatsResponse(
        total_articles=total,
        processed_articles=processed,
        unprocessed_articles=total - processed,
        total_digests=total_digests,
        total_sources=total_sources,
        active_sources=active_sources,
        categories=categories,
        recent_activity=recent,
        memory_units=mem_stats.get("total_units", 0)
    )


# ========== Config ==========

@router.get("/config")
async def get_configuration():
    """Get current configuration (safe values only)"""
    config = get_config()
    
    return {
        "name": config.name,
        "version": config.version,
        "llm_provider": config.llm.provider.value,
        "llm_model": config.llm.model,
        "scheduler_enabled": config.schedule.enabled,
        "digest_time": f"{config.schedule.digest_hour:02d}:{config.schedule.digest_minute:02d}",
        "telegram_configured": bool(config.channels.telegram.token),
        "memory_enabled": config.memory.enabled,
        "pipeline": {
            "max_articles": config.pipeline.max_articles_per_source,
            "critic_min_score": config.pipeline.critic_min_score,
            "auto_process": config.pipeline.auto_process_enabled
        }
    }


@router.post("/config/init")
async def init_configuration():
    """Initialize default configuration file"""
    manager = get_config_manager()
    manager.create_default_config()
    return {"success": True, "message": f"Config created at {manager.CONFIG_FILE}"}
