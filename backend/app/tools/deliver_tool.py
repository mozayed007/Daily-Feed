"""
Deliver Tool - Converted from Delivery Agent
Delivers digests to messaging platforms as a tool
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.core.tool_base import Tool, ToolResult
from app.database import Database, ArticleModel, DigestModel
from app.core.config_manager import get_config


class DeliverTool(Tool):
    """Tool for delivering digests to messaging platforms."""
    
    def __init__(self):
        self.config = get_config()
        self.telegram_token = self.config.channels.telegram.token
        self.telegram_chat_id = self.config.channels.telegram.chat_id
    
    @property
    def name(self) -> str:
        return "deliver_digest"
    
    @property
    def description(self) -> str:
        return "Create and deliver a digest of recent articles via Telegram."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "hours": {
                    "type": "integer",
                    "description": "Include articles from last N hours",
                    "default": 24,
                    "minimum": 1,
                    "maximum": 168
                },
                "via_telegram": {
                    "type": "boolean",
                    "description": "Whether to send via Telegram",
                    "default": True
                },
                "max_articles": {
                    "type": "integer",
                    "description": "Maximum articles in digest",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50
                }
            },
            "required": []
        }
    
    async def execute(
        self,
        hours: int = 24,
        via_telegram: bool = True,
        max_articles: int = 10
    ) -> ToolResult:
        """Execute the deliver tool."""
        try:
            # Get recent processed articles
            from sqlalchemy import select
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            async with Database.get_session() as db:
                result = await db.execute(
                    select(ArticleModel)
                    .where(ArticleModel.is_processed == True)
                    .where(ArticleModel.fetched_at >= cutoff)
                    .order_by(ArticleModel.fetched_at.desc())
                    .limit(max_articles)
                )
                articles = result.scalars().all()
                
                if not articles:
                    return ToolResult(
                        success=True,
                        data={"delivered": False, "reason": "No articles to include"},
                        message="No processed articles found in time range"
                    )
                
                # Create digest content
                digest_content = self._format_digest(list(articles))
                
                # Save digest to database
                digest = DigestModel(
                    article_count=len(articles),
                    content=digest_content,
                    delivered=False
                )
                db.add(digest)
                await db.flush()
                
                # Associate articles
                for article in articles:
                    article.digest_id = digest.id
                
                # Deliver via Telegram if configured
                telegram_sent = False
                if via_telegram and self.telegram_token and self.telegram_chat_id:
                    telegram_sent = await self._send_telegram(digest_content)
                    if telegram_sent:
                        digest.delivered = True
                        digest.delivered_at = datetime.now(timezone.utc)
                
                await db.commit()
                
                return ToolResult(
                    success=True,
                    data={
                        "digest_id": digest.id,
                        "article_count": len(articles),
                        "telegram_sent": telegram_sent,
                        "content": digest_content[:500] + "..."
                    },
                    message=f"Digest created with {len(articles)} articles" + 
                            (" and sent via Telegram" if telegram_sent else "")
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def _format_digest(self, articles: List[ArticleModel]) -> str:
        """Format articles into digest text."""
        # Group by category
        by_category: Dict[str, List[ArticleModel]] = {}
        for article in articles:
            cat = article.category or "General"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(article)
        
        lines = [
            "📰 DAILY NEWS DIGEST",
            f"📅 {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
            f"📊 {len(articles)} articles",
            "═" * 40,
            ""
        ]
        
        for category, cat_articles in by_category.items():
            lines.append(f"\n📁 {category}")
            lines.append("─" * 30)
            
            for article in cat_articles:
                lines.append(f"\n• {article.title}")
                lines.append(f"  📰 {article.source}")
                if article.summary:
                    lines.append(f"  📝 {article.summary[:150]}...")
                lines.append(f"  🔗 {article.url}")
        
        lines.append("\n" + "═" * 40)
        lines.append("Powered by Daily Feed 🤖")
        
        return "\n".join(lines)
    
    async def _send_telegram(self, content: str) -> bool:
        """Send digest via Telegram."""
        try:
            import aiohttp
            
            # Split if too long
            max_length = 4000
            if len(content) > max_length:
                parts = [content[i:i+max_length] for i in range(0, len(content), max_length)]
            else:
                parts = [content]
            
            async with aiohttp.ClientSession() as session:
                for part in parts:
                    url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
                    payload = {
                        "chat_id": self.telegram_chat_id,
                        "text": part,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True
                    }
                    
                    async with session.post(url, json=payload) as resp:
                        if resp.status != 200:
                            return False
            
            return True
            
        except Exception as e:
            print(f"Telegram delivery error: {e}")
            return False
