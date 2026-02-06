"""
Built-in cron scheduler - no need for external cron
Inspired by nanobot's scheduling approach
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import re

from app.core.config_manager import get_config

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScheduledJob:
    """A scheduled job."""
    id: str
    name: str
    cron: Optional[str] = None  # Cron expression (e.g., "0 8 * * *")
    interval_seconds: Optional[int] = None  # Or interval-based
    callback: Callable = field(default=lambda: None, repr=False)
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    status: JobStatus = JobStatus.PENDING
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for APIs/tests."""
        return {
            "id": self.id,
            "name": self.name,
            "cron": self.cron,
            "interval_seconds": self.interval_seconds,
            "enabled": self.enabled,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "run_count": self.run_count,
            "status": self.status,
            "error_count": self.error_count,
        }

    def __getitem__(self, key: str) -> Any:
        """Dict-like access for backward compatibility."""
        return self.to_dict()[key]


class CronParser:
    """Parse and evaluate cron expressions."""
    
    @staticmethod
    def parse(cron_expr: str) -> Dict[str, Set[int]]:
        """
        Parse a cron expression into field values.
        
        Format: minute hour day month day_of_week
        Example: "0 8 * * *" = 8:00 AM daily
        """
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expr}")
        
        minute, hour, day, month, dow = parts
        
        return {
            "minute": set(CronParser._parse_field(minute, 0, 59)),
            "hour": set(CronParser._parse_field(hour, 0, 23)),
            "day": set(CronParser._parse_field(day, 1, 31)),
            "month": set(CronParser._parse_field(month, 1, 12)),
            "dow": set(CronParser._parse_field(dow, 0, 6)),  # 0 = Sunday
        }
    
    @staticmethod
    def _parse_field(field: str, min_val: int, max_val: int) -> List[int]:
        """Parse a single cron field."""
        if field == "*":
            return list(range(min_val, max_val + 1))
        
        if "/" in field:
            # Step value: */5
            base, step = field.split("/")
            if base == "*":
                return list(range(min_val, max_val + 1, int(step)))
        
        if "-" in field:
            # Range: 1-5
            start, end = map(int, field.split("-"))
            return list(range(start, end + 1))
        
        if "," in field:
            # List: 1,3,5
            return [int(x) for x in field.split(",")]
        
        # Single value
        return [int(field)]
    
    @staticmethod
    def get_next_run(cron_expr: str, after: Optional[datetime] = None) -> datetime:
        """Calculate the next run time for a cron expression."""
        fields = CronParser.parse(cron_expr)
        after = after or datetime.now(timezone.utc)
        
        # Start from next minute
        candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # Search for next matching time (max 1 year ahead)
        for _ in range(365 * 24 * 60):
            # Convert Python weekday (0=Monday) to cron weekday (0=Sunday)
            cron_weekday = (candidate.weekday() + 1) % 7
            if (candidate.minute in fields["minute"] and
                candidate.hour in fields["hour"] and
                candidate.day in fields["day"] and
                candidate.month in fields["month"] and
                cron_weekday in fields["dow"]):
                return candidate
            
            candidate += timedelta(minutes=1)
        
        raise ValueError(f"Could not find next run time for cron: {cron_expr}")


class Scheduler:
    """
    Built-in task scheduler.
    
    Supports:
    - Cron expressions (e.g., "0 8 * * *" for 8 AM daily)
    - Interval-based scheduling (e.g., every 3600 seconds)
    - One-time scheduled tasks
    """
    
    def __init__(self):
        self.jobs: Dict[str, ScheduledJob] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._check_interval = 30  # Check for jobs every 30 seconds
    
    def add_cron_job(
        self,
        name: str,
        cron: str,
        callback: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        job_id: Optional[str] = None
    ) -> ScheduledJob:
        """
        Add a cron-based scheduled job.
        
        Args:
            name: Human-readable job name
            cron: Cron expression (e.g., "0 8 * * *" for 8 AM daily)
            callback: Function to call
            args: Positional arguments for callback
            kwargs: Keyword arguments for callback
            job_id: Optional job ID (generated if not provided)
        
        Returns:
            The created ScheduledJob
        """
        job_id = job_id or f"{name.lower().replace(' ', '_')}_{id(callback)}"
        
        try:
            next_run = CronParser.get_next_run(cron)
        except ValueError as e:
            raise ValueError(f"Invalid cron expression: {e}")
        
        job = ScheduledJob(
            id=job_id,
            name=name,
            cron=cron,
            callback=callback,
            args=args,
            kwargs=kwargs or {},
            next_run=next_run
        )
        
        self.jobs[job_id] = job
        logger.info(f"Added cron job '{name}' ({cron}), next run: {next_run}")
        return job
    
    def add_interval_job(
        self,
        name: str,
        seconds: int,
        callback: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        job_id: Optional[str] = None
    ) -> ScheduledJob:
        """Add an interval-based job."""
        job_id = job_id or f"{name.lower().replace(' ', '_')}_{id(callback)}"
        
        job = ScheduledJob(
            id=job_id,
            name=name,
            interval_seconds=seconds,
            callback=callback,
            args=args,
            kwargs=kwargs or {},
            next_run=datetime.now(timezone.utc) + timedelta(seconds=seconds)
        )
        
        self.jobs[job_id] = job
        logger.info(f"Added interval job '{name}' (every {seconds}s)")
        return job
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job."""
        if job_id in self.jobs:
            del self.jobs[job_id]
            logger.info(f"Removed job {job_id}")
            return True
        return False
    
    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Get a job by ID."""
        return self.jobs.get(job_id)
    
    def list_jobs(self) -> List[ScheduledJob]:
        """List all scheduled jobs."""
        return list(self.jobs.values())
    
    def enable_job(self, job_id: str) -> bool:
        """Enable a job."""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = True
            return True
        return False
    
    def disable_job(self, job_id: str) -> bool:
        """Disable a job."""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = False
            return True
        return False
    
    async def start(self):
        """Start the scheduler."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Scheduler started")
    
    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler stopped")
    
    async def _run_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_run_jobs()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(self._check_interval)
    
    async def _check_and_run_jobs(self):
        """Check for due jobs and execute them."""
        now = datetime.now(timezone.utc)
        
        for job in self.jobs.values():
            if not job.enabled:
                continue
            
            if job.status == JobStatus.RUNNING:
                continue
            
            if job.next_run and now >= job.next_run:
                # Execute job
                asyncio.create_task(self._execute_job(job))
    
    async def _execute_job(self, job: ScheduledJob):
        """Execute a scheduled job."""
        job.status = JobStatus.RUNNING
        job.last_run = datetime.now(timezone.utc)
        
        try:
            logger.info(f"Executing job '{job.name}'")
            
            # Run callback
            if asyncio.iscoroutinefunction(job.callback):
                await job.callback(*job.args, **job.kwargs)
            else:
                await asyncio.to_thread(job.callback, *job.args, **job.kwargs)
            
            job.run_count += 1
            job.status = JobStatus.COMPLETED
            logger.info(f"Job '{job.name}' completed successfully")
            
        except Exception as e:
            job.error_count += 1
            job.status = JobStatus.FAILED
            logger.error(f"Job '{job.name}' failed: {e}")
        
        # Calculate next run time
        if job.cron:
            job.next_run = CronParser.get_next_run(job.cron, after=datetime.now(timezone.utc))
        elif job.interval_seconds:
            job.next_run = datetime.now(timezone.utc) + timedelta(seconds=job.interval_seconds)
        
        job.status = JobStatus.PENDING
    
    def setup_default_jobs(self, pipeline_callback: Callable):
        """Setup default scheduled jobs for Daily Feed."""
        config = get_config()
        
        if not config.schedule.enabled:
            logger.info("Scheduler disabled in config")
            return
        
        # Daily digest job
        cron_expr = f"{config.schedule.digest_minute} {config.schedule.digest_hour} * * *"
        self.add_cron_job(
            name="Daily Digest",
            cron=cron_expr,
            callback=pipeline_callback,
            kwargs={"task_type": "digest"},
            job_id="daily_digest"
        )
        
        # Auto-fetch job (if enabled)
        if config.pipeline.auto_fetch_interval_minutes > 0:
            self.add_interval_job(
                name="Auto Fetch",
                seconds=config.pipeline.auto_fetch_interval_minutes * 60,
                callback=pipeline_callback,
                kwargs={"task_type": "fetch"},
                job_id="auto_fetch"
            )
        
        logger.info(f"Setup {len(self.jobs)} default scheduled jobs")


# Global scheduler instance
_scheduler: Optional[Scheduler] = None


def get_scheduler() -> Scheduler:
    """Get global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler


# Convenience decorators
def cron(cron_expr: str, name: Optional[str] = None):
    """Decorator to schedule a function with cron expression."""
    def decorator(func: Callable):
        job_name = name or func.__name__
        get_scheduler().add_cron_job(
            name=job_name,
            cron=cron_expr,
            callback=func
        )
        return func
    return decorator


def interval(seconds: int, name: Optional[str] = None):
    """Decorator to schedule a function with interval."""
    def decorator(func: Callable):
        job_name = name or func.__name__
        get_scheduler().add_interval_job(
            name=job_name,
            seconds=seconds,
            callback=func
        )
        return func
    return decorator
