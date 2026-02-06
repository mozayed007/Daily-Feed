"""
API Routes v2 - Updated for new agent loop architecture
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import (
    Database, ArticleModel, SourceModel, DigestModel,
    ArticleResponse, ArticleListResponse, SourceResponse, SourceCreate,
    DigestResponse, StatsResponse
)
from app.core.agent_loop import get_agent_loop
from app.core.scheduler import get_scheduler
from app.core.memory import get_memory_store
from app.core.config_manager import get_config_manager, get_config

logger = logging.getLogger(__name__)
router = APIRouter()
LOCAL_ONLY_CLIENTS = {"127.0.0.1", "::1", "localhost", "testclient"}

# Include user routes
from app.api.user_routes import router as user_router
router.include_router(user_router, prefix="/users")


# Dependency
async def get_db():
    async with Database.get_session() as session:
        yield session


def require_local_request(request: Request) -> None:
    """Restrict sensitive endpoints to local clients."""
    host = request.client.host if request.client else ""
    if host not in LOCAL_ONLY_CLIENTS:
        raise HTTPException(status_code=403, detail="This endpoint is restricted to local clients")


# ========== Health & Status ==========

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    agent = get_agent_loop()
    config = get_config()
    
    return {
        "status": "healthy",
        "version": config.version,
        "tools_available": agent.get_available_tools(),
        "scheduler_running": get_scheduler()._running
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


# ========== Sources ==========

@router.get("/sources", response_model=List[SourceResponse])
async def get_sources(db: AsyncSession = Depends(get_db)):
    """Get all RSS sources"""
    result = await db.execute(select(SourceModel))
    sources = result.scalars().all()
    return [SourceResponse.model_validate(s) for s in sources]


@router.post("/sources", response_model=SourceResponse)
async def create_source(
    source: SourceCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_local_request),
):
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
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_local_request),
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
async def delete_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_local_request),
):
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


# ========== Agent Loop / Pipelines ==========

@router.post("/pipeline/{task_type}")
async def run_pipeline(
    task_type: str,
    background_tasks: BackgroundTasks,
    params: Optional[Dict[str, Any]] = None,
    _: None = Depends(require_local_request),
):
    """
    Run a pipeline task using the agent loop.
    
    Available task types:
    - fetch: Fetch articles from sources
    - process: Process/summarize unprocessed articles
    - digest: Create and deliver digest
    - full: Run complete pipeline (fetch -> process -> digest)
    - memory_sync: Sync articles to memory
    """
    agent = get_agent_loop()
    params = params or {}
    
    try:
        result = await agent.run_pipeline(task_type, **params)
        return {
            "success": result.get("success", False),
            "task_type": task_type,
            "result": result
        }
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools():
    """List available tools in the agent loop"""
    agent = get_agent_loop()
    return {
        "tools": agent.get_available_tools()
    }


@router.post("/tools/{tool_name}")
async def execute_tool(
    tool_name: str,
    params: Dict[str, Any],
    _: None = Depends(require_local_request),
):
    """Execute a specific tool directly"""
    agent = get_agent_loop()
    
    result = await agent.tools.execute(tool_name, **params)
    return {
        "success": result.success,
        "data": result.data,
        "message": result.message,
        "error": result.error
    }


# ========== Scheduler ==========

@router.get("/scheduler/jobs")
async def list_scheduled_jobs():
    """List all scheduled jobs"""
    scheduler = get_scheduler()
    jobs = scheduler.list_jobs()
    
    return {
        "jobs": [
            {
                "id": j.id,
                "name": j.name,
                "enabled": j.enabled,
                "cron": j.cron,
                "interval_seconds": j.interval_seconds,
                "last_run": j.last_run.isoformat() if j.last_run else None,
                "next_run": j.next_run.isoformat() if j.next_run else None,
                "run_count": j.run_count,
                "status": j.status.value
            }
            for j in jobs
        ]
    }


@router.post("/scheduler/jobs")
async def add_scheduled_job(
    job_config: Dict[str, Any],
    _: None = Depends(require_local_request),
):
    """Add a new scheduled job"""
    scheduler = get_scheduler()
    
    if job_config.get("cron"):
        job = scheduler.add_cron_job(
            name=job_config["name"],
            cron=job_config["cron"],
            callback=lambda: None,  # Would need to be configured properly
        )
    elif job_config.get("interval_seconds"):
        job = scheduler.add_interval_job(
            name=job_config["name"],
            seconds=job_config["interval_seconds"],
            callback=lambda: None
        )
    else:
        raise HTTPException(status_code=400, detail="Must specify cron or interval_seconds")
    
    return {"success": True, "job_id": job.id}


@router.post("/scheduler/start")
async def start_scheduler(_: None = Depends(require_local_request)):
    """Start the scheduler"""
    scheduler = get_scheduler()
    await scheduler.start()
    return {"success": True, "message": "Scheduler started"}


@router.post("/scheduler/stop")
async def stop_scheduler(_: None = Depends(require_local_request)):
    """Stop the scheduler"""
    scheduler = get_scheduler()
    await scheduler.stop()
    return {"success": True, "message": "Scheduler stopped"}


@router.delete("/scheduler/jobs/{job_id}")
async def delete_scheduled_job(job_id: str, _: None = Depends(require_local_request)):
    """Remove a scheduled job"""
    scheduler = get_scheduler()
    removed = scheduler.remove_job(job_id)
    
    if not removed:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"success": True, "message": f"Job {job_id} removed"}


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
async def remember_article(article_id: int, _: None = Depends(require_local_request)):
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
async def search_memory(query: Dict[str, Any], _: None = Depends(require_local_request)):
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
async def summarize_article(
    article_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_local_request),
):
    """Trigger summarization for a single article"""
    result = await db.execute(
        select(ArticleModel).where(ArticleModel.id == article_id)
    )
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Run summarization using agent loop
    agent = get_agent_loop()
    tool_result = await agent.tools.execute("summarize_article", article_id=article_id)
    
    if tool_result.success:
        return {
            "success": True,
            "score": tool_result.data.get("critic_score"),
            "summary": tool_result.data.get("summary")
        }
    else:
        raise HTTPException(status_code=500, detail=tool_result.error)


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
async def init_configuration(_: None = Depends(require_local_request)):
    """Initialize default configuration file"""
    manager = get_config_manager()
    manager.create_default_config()
    return {"success": True, "message": f"Config created at {manager.CONFIG_FILE}"}
