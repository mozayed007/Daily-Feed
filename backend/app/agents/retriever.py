"""Feed Retriever Agent - Fetches articles from RSS feeds"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup

from app.database import ArticleModel, SourceModel, ArticleCreate

logger = logging.getLogger(__name__)


@dataclass
class SourceConfig:
    """RSS source configuration"""
    name: str
    url: str
    category: Optional[str] = None
    enabled: bool = True


@dataclass  
class RawArticle:
    """Raw article data from feed"""
    title: str
    url: str
    content: str
    source: str
    category: Optional[str]
    published_at: Optional[datetime]


class FeedRetrieverAgent:
    """Agent responsible for fetching articles from RSS feeds"""
    
    def __init__(self, max_articles_per_source: int = 15):
        self.max_articles_per_source = max_articles_per_source
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'DailyFeed/1.0 (News Aggregator; Personal Use)'
            }
        )
    
    async def fetch_all_sources(
        self, 
        db_session,
        sources: Optional[List[SourceConfig]] = None
    ) -> List[ArticleModel]:
        """Fetch articles from all enabled sources"""
        from sqlalchemy import select
        
        if sources is None:
            # Get sources from database
            result = await db_session.execute(
                select(SourceModel).where(SourceModel.enabled == True)
            )
            db_sources = result.scalars().all()
            sources = [
                SourceConfig(
                    name=s.name,
                    url=s.url,
                    category=s.category,
                    enabled=s.enabled
                )
                for s in db_sources
            ]
        
        all_articles = []
        
        for source in sources:
            try:
                logger.info(f"Fetching from {source.name}...")
                articles = await self.fetch_source(source)
                
                # Save to database
                for article_data in articles:
                    # Check for duplicates
                    existing = await db_session.execute(
                        select(ArticleModel).where(ArticleModel.url == article_data.url)
                    )
                    if existing.scalar_one_or_none():
                        continue
                    
                    # Create new article
                    article = ArticleModel(
                        title=article_data.title,
                        url=article_data.url,
                        content=article_data.content,
                        source=article_data.source,
                        category=article_data.category,
                        published_at=article_data.published_at,
                        is_processed=False
                    )
                    db_session.add(article)
                    all_articles.append(article)
                
                # Update source stats
                await self._update_source_stats(db_session, source.name, len(articles))
                
                logger.info(f"Saved {len(articles)} articles from {source.name}")
                
            except Exception as e:
                logger.error(f"Error fetching from {source.name}: {e}")
                await self._increment_source_error(db_session, source.name)
        
        await db_session.commit()
        return all_articles
    
    async def fetch_source(self, source: SourceConfig) -> List[RawArticle]:
        """Fetch articles from a single RSS source"""
        
        # Use feedparser in thread pool
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, source.url)
        
        articles = []
        
        for entry in feed.entries[:self.max_articles_per_source]:
            try:
                article = self._parse_entry(entry, source.name, source.category)
                if article:
                    articles.append(article)
            except Exception as e:
                logger.warning(f"Error parsing entry: {e}")
        
        return articles
    
    def _parse_entry(
        self, 
        entry: Any, 
        source_name: str, 
        category: Optional[str]
    ) -> Optional[RawArticle]:
        """Parse a feed entry into a RawArticle"""
        
        title = entry.get('title', '').strip()
        url = entry.get('link', '').strip()
        
        if not title or not url:
            return None
        
        # Parse published date
        published_at = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published_at = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            published_at = datetime(*entry.updated_parsed[:6])
        
        # Extract content
        content = self._extract_content(entry)
        
        return RawArticle(
            title=title,
            url=url,
            content=content,
            source=source_name,
            category=category,
            published_at=published_at
        )
    
    def _extract_content(self, entry: Any) -> str:
        """Extract article content from feed entry"""
        content = ''
        
        # Try different content fields
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value
        elif hasattr(entry, 'summary'):
            content = entry.summary
        elif hasattr(entry, 'description'):
            content = entry.description
        
        # Clean HTML
        content = self._clean_html(content)
        
        # Limit length
        max_length = 10000
        if len(content) > max_length:
            content = content[:max_length] + '...'
        
        return content
    
    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from text"""
        if not html:
            return ''
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    async def fetch_full_content(self, url: str) -> str:
        """Fetch full article content from URL"""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try common content selectors
            for selector in ['article', 'main', '.content', '.post', 
                           '[role="main"]', '.entry-content', '.article-body']:
                content = soup.select_one(selector)
                if content:
                    return self._clean_html(str(content))
            
            # Fallback to body
            body = soup.find('body')
            if body:
                return self._clean_html(str(body))[:5000]
            
            return ''
            
        except Exception as e:
            logger.warning(f"Error fetching full content from {url}: {e}")
            return ''
    
    async def _update_source_stats(self, db_session, source_name: str, count: int):
        """Update source fetch stats"""
        result = await db_session.execute(
            select(SourceModel).where(SourceModel.name == source_name)
        )
        source = result.scalar_one_or_none()
        if source:
            source.last_fetch = datetime.now(timezone.utc)
            source.fetch_count += count
    
    async def _increment_source_error(self, db_session, source_name: str):
        """Increment source error count"""
        result = await db_session.execute(
            select(SourceModel).where(SourceModel.name == source_name)
        )
        source = result.scalar_one_or_none()
        if source:
            source.error_count += 1
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
