"""Delivery Agent - Delivers digests to messaging platforms"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote

import httpx
from telegram import Bot
from telegram.constants import ParseMode

from app.database import ArticleModel, DigestModel
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class DigestResult:
    """Digest result"""
    id: Optional[int]
    created_at: datetime
    articles: List[ArticleModel]
    by_category: Dict[str, List[ArticleModel]]
    article_count: int
    content: str = ""
    delivered: bool = False


class DeliveryAgent:
    """Agent responsible for delivering digests"""
    
    def __init__(
        self, 
        telegram_token: str = None,
        telegram_chat_id: str = None
    ):
        self.telegram_token = telegram_token or settings.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = telegram_chat_id or settings.TELEGRAM_CHAT_ID
        self.bot: Optional[Bot] = None
        
        if self.telegram_token:
            self.bot = Bot(token=self.telegram_token)
    
    def create_digest(
        self, 
        articles: List[ArticleModel],
        from_db: bool = False,
        digest_id: Optional[int] = None
    ) -> DigestResult:
        """Create a digest from articles"""
        
        # Group by category
        by_category: Dict[str, List[ArticleModel]] = {}
        for article in articles:
            cat = article.category or "General"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(article)
        
        # Sort categories by article count
        by_category = dict(sorted(
            by_category.items(), 
            key=lambda x: len(x[1]), 
            reverse=True
        ))
        
        # Format content
        content = self._format_digest_content(articles, by_category)
        
        return DigestResult(
            id=digest_id,
            created_at=datetime.utcnow(),
            articles=articles,
            by_category=by_category,
            article_count=len(articles),
            content=content
        )
    
    async def deliver_telegram(self, digest: DigestResult) -> bool:
        """Deliver digest via Telegram"""
        
        if not self.bot or not self.telegram_chat_id:
            logger.warning("Telegram not configured")
            return False
        
        try:
            message = self._format_telegram_message(digest)
            
            # Split if too long
            if len(message) > 4000:
                await self._send_long_message(message)
            else:
                await self.bot.send_message(
                    chat_id=self.telegram_chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
            
            digest.delivered = True
            logger.info(f"Digest delivered to Telegram")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deliver via Telegram: {e}")
            return False
    
    def _format_telegram_message(self, digest: DigestResult) -> str:
        """Format digest for Telegram"""
        
        # Header
        message = f"📰 *Daily News Digest*\n"
        message += f"📅 {digest.created_at.strftime('%A, %B %d, %Y')}\n"
        message += f"📊 {digest.article_count} articles\n"
        message += "═" * 30 + "\n\n"
        
        # Articles by category
        for category, articles in digest.by_category.items():
            message += f"📁 *{self._escape_markdown(category)}*\n"
            message += "─" * 25 + "\n\n"
            
            for i, article in enumerate(articles[:3], 1):  # Max 3 per category
                message += f"{i}. *{self._escape_markdown(article.title)}*\n"
                
                if article.summary:
                    summary = article.summary[:200]
                    if len(article.summary) > 200:
                        summary += "..."
                    message += f"   {self._escape_markdown(summary)}\n"
                
                message += f"   📰 {self._escape_markdown(article.source)}"
                if article.reading_time:
                    message += f" | ⏱️ {article.reading_time} min"
                message += "\n"
                
                message += f"   🔗 [Read more]({article.url})\n\n"
            
            if len(articles) > 3:
                message += f"   _...and {len(articles) - 3} more_\n\n"
        
        # Footer
        message += "═" * 30 + "\n"
        message += "_Powered by Daily Feed 🤖_"
        
        return message
    
    async def _send_long_message(self, text: str):
        """Split and send long messages"""
        parts = text.split("📁 ")
        
        # Send header
        header = parts[0]
        await self.bot.send_message(
            chat_id=self.telegram_chat_id,
            text=header,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        
        # Send each category
        for part in parts[1:]:
            section = "📁 " + part
            if len(section) > 4000:
                chunks = [section[i:i+3500] for i in range(0, len(section), 3500)]
                for chunk in chunks:
                    await self.bot.send_message(
                        chat_id=self.telegram_chat_id,
                        text=chunk,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True
                    )
            else:
                await self.bot.send_message(
                    chat_id=self.telegram_chat_id,
                    text=section,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
    
    def _format_digest_content(
        self, 
        articles: List[ArticleModel],
        by_category: Dict[str, List[ArticleModel]]
    ) -> str:
        """Format digest as plain text for storage"""
        
        lines = [
            "DAILY NEWS DIGEST",
            f"Date: {datetime.utcnow().strftime('%Y-%m-%d')}",
            f"Articles: {len(articles)}",
            "=" * 50,
            ""
        ]
        
        for category, cat_articles in by_category.items():
            lines.append(f"\n{category}")
            lines.append("-" * 40)
            
            for article in cat_articles:
                lines.append(f"\n• {article.title}")
                lines.append(f"  Source: {article.source}")
                if article.summary:
                    lines.append(f"  Summary: {article.summary[:150]}...")
                lines.append(f"  Link: {article.url}")
        
        return "\n".join(lines)
    
    def _escape_markdown(self, text: str) -> str:
        """Escape special Markdown characters for Telegram"""
        if not text:
            return ""
        
        # Characters to escape: _ * [ ] ( ) ~ ` > # + - = | { } . !
        escape_chars = '_*[]()~`>#+-=|{}.!'
        
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    def print_to_console(self, digest: DigestResult):
        """Print digest to console"""
        print("\n" + "=" * 60)
        print(f"📰 DAILY NEWS DIGEST - {digest.created_at.strftime('%Y-%m-%d %H:%M')}")
        print("=" * 60)
        
        for category, articles in digest.by_category.items():
            print(f"\n📁 {category}")
            print("-" * 40)
            
            for article in articles:
                print(f"\n📰 {article.title}")
                print(f"   Source: {article.source}")
                if article.summary:
                    print(f"   Summary: {article.summary[:200]}...")
                print(f"   Link: {article.url}")
        
        print("\n" + "=" * 60)
