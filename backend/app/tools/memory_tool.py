"""
Memory Tool - Interface to SimpleMem memory system
Allows agents to store and retrieve memories
"""

from typing import Any, Dict, List, Optional

from app.core.tool_base import Tool, ToolResult
from app.core.memory import get_memory_store, ArticleMemory
from app.database import Database, ArticleModel


class MemoryTool(Tool):
    """Tool for storing and retrieving memories."""
    
    def __init__(self):
        self.memory: ArticleMemory = get_memory_store()
    
    @property
    def name(self) -> str:
        return "memory"
    
    @property
    def description(self) -> str:
        return "Store or retrieve memories. Can remember articles, find similar content, or get user interests."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["remember_article", "find_similar", "get_interests", "get_stats"],
                    "description": "Memory action to perform"
                },
                "article_id": {
                    "type": "integer",
                    "description": "Article ID (for remember_article)"
                },
                "title": {
                    "type": "string",
                    "description": "Title to search for similarity (for find_similar)"
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 5
                }
            },
            "required": ["action"]
        }
    
    async def execute(
        self,
        action: str,
        article_id: Optional[int] = None,
        title: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 5
    ) -> ToolResult:
        """Execute the memory tool."""
        
        try:
            if action == "remember_article":
                return await self._remember_article(article_id)
            
            elif action == "find_similar":
                return self._find_similar(title, category, limit)
            
            elif action == "get_interests":
                return self._get_interests()
            
            elif action == "get_stats":
                return self._get_stats()
            
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def _remember_article(self, article_id: Optional[int]) -> ToolResult:
        """Store article in memory."""
        if not article_id:
            return ToolResult(
                success=False,
                data=None,
                error="article_id required for remember_article"
            )
        
        async with Database.get_session() as db:
            from sqlalchemy import select
            
            result = await db.execute(
                select(ArticleModel).where(ArticleModel.id == article_id)
            )
            article = result.scalar_one_or_none()
            
            if not article:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Article {article_id} not found"
                )
            
            # Store in memory
            unit = self.memory.remember_article(
                article_id=article.id,
                title=article.title,
                summary=article.summary or "",
                category=article.category or "General",
                source=article.source,
                key_points=article.key_points or []
            )
            
            return ToolResult(
                success=True,
                data={
                    "memory_id": unit.id,
                    "article_id": article_id,
                    "category": unit.category
                },
                message=f"Article '{article.title[:40]}...' remembered in category '{unit.category}'"
            )
    
    def _find_similar(
        self,
        title: Optional[str],
        category: Optional[str],
        limit: int
    ) -> ToolResult:
        """Find similar articles in memory."""
        if not title:
            return ToolResult(
                success=False,
                data=None,
                error="title required for find_similar"
            )
        
        similar = self.memory.find_similar_articles(title, category, limit)
        
        return ToolResult(
            success=True,
            data={
                "query": title,
                "found": len(similar),
                "matches": [
                    {
                        "id": s.id,
                        "content": s.content[:200],
                        "category": s.category,
                        "source": s.source
                    }
                    for s in similar
                ]
            },
            message=f"Found {len(similar)} similar articles in memory"
        )
    
    def _get_interests(self) -> ToolResult:
        """Get user interests from memory analysis."""
        interests = self.memory.get_user_interests()
        
        return ToolResult(
            success=True,
            data={
                "interests": interests,
                "top_categories": list(interests.keys())[:5]
            },
            message=f"Top interests: {', '.join(list(interests.keys())[:3]) or 'None yet'}"
        )
    
    def _get_stats(self) -> ToolResult:
        """Get memory statistics."""
        stats = self.memory.get_stats()
        
        return ToolResult(
            success=True,
            data=stats,
            message=f"Memory contains {stats['total_units']} units, {stats['recent_7d']} from last 7 days"
        )
