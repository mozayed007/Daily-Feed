"""
Fetch Tool - Converted from Feed Retriever Agent
Fetches articles from RSS feeds as a tool
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse
import socket

import httpx
import feedparser
from bs4 import BeautifulSoup

from app.core.tool_base import Tool, ToolResult
from app.database import Database, ArticleModel, SourceModel
from app.core.config_manager import get_config


# Blocked hosts for SSRF protection
BLOCKED_HOSTS = {
    'localhost', '127.0.0.1', '0.0.0.0', '::1',
    '169.254.169.254',  # AWS metadata
    '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16',  # Private ranges
}

MAX_FEED_SIZE = 10 * 1024 * 1024  # 10MB
FETCH_TIMEOUT = 30  # seconds


class FetchTool(Tool):
    """Tool for fetching articles from RSS feeds."""
    
    def __init__(self):
        self._max_articles = get_config().pipeline.max_articles_per_source
    
    @property
    def name(self) -> str:
        return "fetch_articles"
    
    @property
    def description(self) -> str:
        return "Fetch new articles from configured RSS sources. Returns count of fetched articles."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "source_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Optional list of specific source IDs to fetch from. If empty, fetches from all enabled sources."
                },
                "max_per_source": {
                    "type": "integer",
                    "description": "Maximum articles to fetch per source",
                    "default": 15,
                    "minimum": 1,
                    "maximum": 50
                }
            },
            "required": []
        }
    
    async def execute(
        self,
        source_ids: Optional[List[int]] = None,
        max_per_source: int = 15
    ) -> ToolResult:
        """Execute the fetch tool."""
        try:
            # Use provided max or default
            max_articles = min(max_per_source, self._max_articles)
            
            # Get sources
            async with Database.get_session() as db:
                from sqlalchemy import select
                
                query = select(SourceModel)
                if source_ids:
                    query = query.where(SourceModel.id.in_(source_ids))
                else:
                    query = query.where(SourceModel.enabled == True)
                
                result = await db.execute(query)
                sources = result.scalars().all()
            
            if not sources:
                return ToolResult(
                    success=True,
                    data={"fetched": 0, "sources_checked": 0},
                    message="No sources to fetch from"
                )
            
            # Fetch from each source
            total_fetched = 0
            source_results = []
            
            for source in sources:
                try:
                    count = await self._fetch_source(source, max_articles)
                    total_fetched += count
                    source_results.append({"source": source.name, "fetched": count})
                except Exception as e:
                    source_results.append({"source": source.name, "error": str(e)})
            
            return ToolResult(
                success=True,
                data={
                    "fetched": total_fetched,
                    "sources_checked": len(sources),
                    "details": source_results
                },
                message=f"Fetched {total_fetched} articles from {len(sources)} sources"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL for security (SSRF protection)."""
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ('http', 'https'):
                return False
            
            # Check hostname
            hostname = parsed.hostname
            if not hostname:
                return False
            
            # Check blocked hosts
            if hostname.lower() in BLOCKED_HOSTS:
                return False
            
            # Check IP-based URLs
            try:
                ip = socket.getaddrinfo(hostname, None)[0][4][0]
                # Block private IP ranges
                if ip.startswith(('10.', '172.16.', '172.17.', '172.18.', 
                                  '172.19.', '172.20.', '172.21.', '172.22.',
                                  '172.23.', '172.24.', '172.25.', '172.26.',
                                  '172.27.', '172.28.', '172.29.', '172.30.',
                                  '172.31.', '192.168.', '127.')):
                    return False
            except socket.gaierror:
                pass  # DNS resolution failed, will fail on fetch anyway
            
            return True
        except Exception:
            return False
    
    async def _fetch_feed(self, url: str) -> str:
        """Fetch feed content with timeout and size limit."""
        if not self._validate_url(url):
            raise ValueError(f"Invalid or blocked URL: {url}")
        
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(url, headers={
                'User-Agent': 'DailyFeed/1.1 (RSS Aggregator)'
            })
            response.raise_for_status()
            
            # Check content length
            content_length = len(response.content)
            if content_length > MAX_FEED_SIZE:
                raise ValueError(f"Feed too large: {content_length} bytes (max {MAX_FEED_SIZE})")
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'xml' not in content_type and 'rss' not in content_type and 'atom' not in content_type:
                # Allow if response looks like XML
                if not response.text.strip().startswith('<?xml'):
                    raise ValueError(f"Invalid content type: {content_type}")
            
            return response.text
    
    async def _fetch_source(self, source: SourceModel, max_articles: int) -> int:
        """Fetch articles from a single source."""
        # Fetch with timeout
        content = await self._fetch_feed(source.url)
        
        # Parse feed
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, content)
        
        fetched = 0
        async with Database.get_session() as db:
            from sqlalchemy import select
            
            for entry in feed.entries[:max_articles]:
                try:
                    # Check for duplicate
                    url = entry.get('link', '').strip()
                    if not url:
                        continue
                    
                    existing = await db.execute(
                        select(ArticleModel).where(ArticleModel.url == url)
                    )
                    if existing.scalar_one_or_none():
                        continue
                    
                    # Parse article
                    article = self._parse_entry(entry, source)
                    if article:
                        db.add(article)
                        fetched += 1
                
                except Exception:
                    continue
            
            # Update source stats
            source.last_fetch = datetime.now(timezone.utc)
            source.fetch_count += fetched
            
            await db.commit()
        
        return fetched
    
    def _parse_entry(self, entry: Any, source: SourceModel) -> Optional[ArticleModel]:
        """Parse feed entry into ArticleModel."""
        title = entry.get('title', '').strip()
        url = entry.get('link', '').strip()
        
        if not title or not url:
            return None
        
        # Parse date
        published_at = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published_at = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            published_at = datetime(*entry.updated_parsed[:6])
        
        # Extract content
        content = self._extract_content(entry)
        
        return ArticleModel(
            title=title,
            url=url,
            content=content,
            source=source.name,
            category=source.category,
            published_at=published_at,
            fetched_at=datetime.now(timezone.utc),
            is_processed=False
        )
    
    def _extract_content(self, entry: Any) -> str:
        """Extract content from entry."""
        content = ''
        
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value
        elif hasattr(entry, 'summary'):
            content = entry.summary
        elif hasattr(entry, 'description'):
            content = entry.description
        
        # Clean HTML
        content = self._clean_html(content)
        
        # Limit length
        if len(content) > 10000:
            content = content[:10000] + '...'
        
        return content
    
    def _clean_html(self, html: str) -> str:
        """Remove HTML tags."""
        if not html:
            return ''
        
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return ' '.join(chunk for chunk in chunks if chunk)
