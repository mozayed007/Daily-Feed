"""
Daily Feed - News Aggregator API v2
FastAPI-based backend with nanobot-inspired agent loop architecture
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config_manager import get_config, get_config_manager
from app.core.logging_config import configure_logging, get_logger
from app.database import Database
from app.api.routes_v2 import router
from app.core.scheduler import get_scheduler
from app.core.agent_loop import get_agent_loop

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

# Load configuration
config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(
        "application_starting",
        app_name=config.name,
        version=config.version,
        config_file=str(get_config_manager().CONFIG_FILE),
        debug=config.debug,
    )
    
    # Create database tables
    await Database.create_tables()
    logger.info("database_initialized")
    
    # Initialize agent loop
    agent = get_agent_loop()
    tool_count = len(agent.get_available_tools())
    logger.info(
        "agent_loop_ready",
        tool_count=tool_count,
        tools=agent.get_available_tools(),
    )
    
    # Start scheduler if enabled
    if config.schedule.enabled:
        scheduler = get_scheduler()
        scheduler.setup_default_jobs(agent.run_pipeline)
        await scheduler.start()
        job_count = len(scheduler.list_jobs())
        logger.info(
            "scheduler_started",
            job_count=job_count,
            jobs=[j["name"] for j in scheduler.list_jobs()],
        )
    else:
        logger.info("scheduler_disabled")
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")
    if config.schedule.enabled:
        await get_scheduler().stop()
        logger.info("scheduler_stopped")


# Create FastAPI app
app = FastAPI(
    title=config.name,
    version=config.version,
    description="AI-powered news aggregator with multi-agent architecture",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["api"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": config.name,
        "version": config.version,
        "architecture": "agent-loop",
        "docs": "/docs",
        "api": "/api/v1"
    }


@app.get("/api")
async def api_info():
    """API info"""
    return {
        "version": "v1",
        "features": [
            "agent-loop",
            "tool-system",
            "memory",
            "scheduler"
        ],
        "endpoints": [
            "/api/v1/health",
            "/api/v1/articles",
            "/api/v1/sources",
            "/api/v1/pipeline/{task_type}",
            "/api/v1/tools",
            "/api/v1/scheduler/jobs",
            "/api/v1/memory/stats"
        ]
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with structured logging"""
    logger.error(
        "unhandled_exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=str(request.url.path),
        method=request.method,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info"
    )
