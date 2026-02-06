"""
Agent Loop - Core processing engine inspired by nanobot
Coordinates tools to perform news aggregation tasks
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from app.core.tool_base import ToolRegistry
from app.core.memory import get_memory_store
from app.tools import FetchTool, SummarizeTool, CritiqueTool, DeliverTool, MemoryTool

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """A task to be executed by the agent loop."""
    id: str
    name: str
    tool_name: str
    params: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict] = None
    error: Optional[str] = None
    depends_on: Optional[str] = None  # Task ID dependency


@dataclass
class Workflow:
    """A workflow consisting of multiple tasks."""
    id: str
    name: str
    tasks: List[Task] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = ""
    completed_at: Optional[str] = None


class AgentLoop:
    """
    The Agent Loop is the core processing engine.
    
    Inspired by nanobot's architecture, it:
    1. Receives workflow requests
    2. Executes tasks using registered tools
    3. Manages dependencies between tasks
    4. Returns results
    
    Unlike the old linear pipeline, this allows:
    - Dynamic task selection
    - Conditional execution
    - Tool reuse and composition
    - Better error handling
    """
    
    def __init__(self):
        self.tools = ToolRegistry()
        self.memory = get_memory_store()
        self._register_default_tools()
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    def _register_default_tools(self):
        """Register the default set of tools."""
        self.tools.register(FetchTool())
        self.tools.register(SummarizeTool())
        self.tools.register(CritiqueTool())
        self.tools.register(DeliverTool())
        self.tools.register(MemoryTool())
        
        logger.info(f"Registered {len(self.tools.list_tools())} tools: {self.tools.list_tools()}")
    
    async def execute_task(self, task: Task) -> Task:
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        
        try:
            logger.info(f"Executing task '{task.name}' with tool '{task.tool_name}'")
            
            # Execute the tool
            result = await self.tools.execute(task.tool_name, **task.params)
            
            task.result = {
                "success": result.success,
                "data": result.data,
                "message": result.message
            }
            
            if result.success:
                task.status = TaskStatus.COMPLETED
                logger.info(f"Task '{task.name}' completed: {result.message}")
            else:
                task.status = TaskStatus.FAILED
                task.error = result.error
                logger.warning(f"Task '{task.name}' failed: {result.error}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Task '{task.name}' error: {e}")
        
        return task
    
    async def run_workflow(self, workflow: Workflow) -> Workflow:
        """Execute a complete workflow with dependency resolution."""
        workflow.status = TaskStatus.RUNNING
        logger.info(f"Starting workflow '{workflow.name}' with {len(workflow.tasks)} tasks")
        
        # Build dependency graph
        completed_tasks: Dict[str, Task] = {}
        pending_tasks = {t.id: t for t in workflow.tasks}
        
        while pending_tasks:
            # Find tasks that are ready (no dependencies or dependencies completed)
            ready_tasks = []
            for t in pending_tasks.values():
                if t.depends_on is None:
                    ready_tasks.append(t)
                    continue
                dependency = completed_tasks.get(t.depends_on)
                if dependency and dependency.status == TaskStatus.COMPLETED:
                    ready_tasks.append(t)
            
            if not ready_tasks:
                # Deadlock - remaining tasks have unmet dependencies
                logger.error("Workflow deadlock - unmet dependencies")
                for t in pending_tasks.values():
                    t.status = TaskStatus.FAILED
                    t.error = "Dependency not met"
                break
            
            # Execute ready tasks concurrently
            results = await asyncio.gather(
                *[self.execute_task(t) for t in ready_tasks],
                return_exceptions=True
            )
            
            # Move completed tasks
            for task in ready_tasks:
                completed_tasks[task.id] = task
                del pending_tasks[task.id]
        
        # Check if all tasks completed successfully
        all_completed = all(t.status == TaskStatus.COMPLETED for t in completed_tasks.values())
        workflow.status = TaskStatus.COMPLETED if all_completed else TaskStatus.FAILED
        
        logger.info(f"Workflow '{workflow.name}' completed with status: {workflow.status.value}")
        return workflow
    
    async def run_pipeline(self, task_type: Optional[str] = None, **params) -> Dict[str, Any]:
        """
        Run a predefined pipeline workflow.
        
        Available pipelines:
        - fetch: Fetch articles from sources
        - process: Process/summarize unprocessed articles
        - digest: Create and deliver digest
        - full: Fetch -> Process -> Digest
        """
        
        task_type = task_type or params.pop("task", None)
        if not task_type:
            return {"success": False, "error": "task_type is required"}

        if task_type == "fetch":
            return await self._run_fetch_pipeline(**params)
        
        elif task_type == "process":
            return await self._run_process_pipeline(**params)
        
        elif task_type == "digest":
            return await self._run_digest_pipeline(**params)
        
        elif task_type == "full":
            return await self._run_full_pipeline(**params)
        
        elif task_type == "memory_sync":
            return await self._run_memory_sync(**params)
        
        else:
            return {"success": False, "error": f"Unknown pipeline type: {task_type}"}
    
    async def _run_fetch_pipeline(self, **params) -> Dict[str, Any]:
        """Run fetch pipeline."""
        workflow = Workflow(
            id=f"fetch_{asyncio.get_event_loop().time()}",
            name="Fetch Articles",
            tasks=[
                Task(
                    id="fetch",
                    name="Fetch from RSS sources",
                    tool_name="fetch_articles",
                    params=params
                )
            ]
        )
        
        result = await self.run_workflow(workflow)
        return {
            "success": result.status == TaskStatus.COMPLETED,
            "tasks_completed": len([t for t in result.tasks if t.status == TaskStatus.COMPLETED]),
            "results": {t.name: t.result for t in result.tasks}
        }
    
    async def _run_process_pipeline(self, limit: int = 10, **params) -> Dict[str, Any]:
        """Run processing pipeline for unprocessed articles."""
        from app.database import Database, ArticleModel
        from sqlalchemy import select
        
        # Get unprocessed articles
        async with Database.get_session() as db:
            result = await db.execute(
                select(ArticleModel)
                .where(ArticleModel.is_processed == False)
                .limit(limit)
            )
            articles = result.scalars().all()
            article_ids = [a.id for a in articles]
        
        if not article_ids:
            return {"success": True, "message": "No unprocessed articles", "processed": 0}
        
        # Create workflow for each article
        tasks = []
        for i, article_id in enumerate(article_ids):
            summarize_task = Task(
                id=f"summarize_{article_id}",
                name=f"Summarize article {article_id}",
                tool_name="summarize_article",
                params={"article_id": article_id}
            )
            tasks.append(summarize_task)
            
            critique_task = Task(
                id=f"critique_{article_id}",
                name=f"Critique article {article_id}",
                tool_name="critique_summary",
                params={"article_id": article_id},
                depends_on=summarize_task.id
            )
            tasks.append(critique_task)
            
            # Remember in memory if critique passes
            memory_task = Task(
                id=f"remember_{article_id}",
                name=f"Remember article {article_id}",
                tool_name="memory",
                params={"action": "remember_article", "article_id": article_id},
                depends_on=critique_task.id
            )
            tasks.append(memory_task)
        
        workflow = Workflow(
            id=f"process_{asyncio.get_event_loop().time()}",
            name="Process Articles",
            tasks=tasks
        )
        
        result = await self.run_workflow(workflow)
        
        # Count successful processes
        summarize_tasks = [t for t in result.tasks if t.tool_name == "summarize_article"]
        successful = len([t for t in summarize_tasks if t.status == TaskStatus.COMPLETED])
        
        return {
            "success": result.status == TaskStatus.COMPLETED,
            "processed": successful,
            "total": len(article_ids),
            "tasks_completed": len([t for t in result.tasks if t.status == TaskStatus.COMPLETED])
        }
    
    async def _run_digest_pipeline(self, **params) -> Dict[str, Any]:
        """Run digest creation and delivery pipeline."""
        workflow = Workflow(
            id=f"digest_{asyncio.get_event_loop().time()}",
            name="Create Digest",
            tasks=[
                Task(
                    id="deliver",
                    name="Create and deliver digest",
                    tool_name="deliver_digest",
                    params=params
                )
            ]
        )
        
        result = await self.run_workflow(workflow)
        return {
            "success": result.status == TaskStatus.COMPLETED,
            "results": {t.name: t.result for t in result.tasks}
        }
    
    async def _run_full_pipeline(self, **params) -> Dict[str, Any]:
        """Run full pipeline: fetch -> process -> digest."""
        # Step 1: Fetch
        fetch_result = await self._run_fetch_pipeline(**params.get("fetch", {}))
        
        # Step 2: Process
        process_result = await self._run_process_pipeline(**params.get("process", {}))
        
        # Step 3: Digest
        digest_result = await self._run_digest_pipeline(**params.get("digest", {}))
        
        success = all(
            result.get("success", False)
            for result in (fetch_result, process_result, digest_result)
        )

        return {
            "success": success,
            "fetch": fetch_result,
            "process": process_result,
            "digest": digest_result
        }
    
    async def _run_memory_sync(self, **params) -> Dict[str, Any]:
        """Sync recent articles to memory."""
        from app.database import Database, ArticleModel
        from sqlalchemy import select
        from datetime import timedelta
        
        # Get recent processed articles not yet in memory
        async with Database.get_session() as db:
            cutoff = datetime.utcnow() - timedelta(days=7)
            result = await db.execute(
                select(ArticleModel)
                .where(ArticleModel.is_processed == True)
                .where(ArticleModel.fetched_at >= cutoff)
                .limit(50)
            )
            articles = result.scalars().all()
        
        tasks = []
        for article in articles:
            tasks.append(Task(
                id=f"mem_{article.id}",
                name=f"Remember article {article.id}",
                tool_name="memory",
                params={"action": "remember_article", "article_id": article.id}
            ))
        
        workflow = Workflow(
            id=f"memory_sync_{asyncio.get_event_loop().time()}",
            name="Memory Sync",
            tasks=tasks
        )
        
        result = await self.run_workflow(workflow)
        
        return {
            "success": result.status == TaskStatus.COMPLETED,
            "synced": len([t for t in result.tasks if t.status == TaskStatus.COMPLETED]),
            "total": len(tasks)
        }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return [self.tools.get(name).to_dict() for name in self.tools.list_tools()]


# Global agent loop instance
_agent_loop: Optional[AgentLoop] = None


def get_agent_loop() -> AgentLoop:
    """Get global agent loop instance."""
    global _agent_loop
    if _agent_loop is None:
        _agent_loop = AgentLoop()
    return _agent_loop
