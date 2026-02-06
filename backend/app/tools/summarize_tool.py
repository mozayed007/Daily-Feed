"""
Summarize Tool - Converted from Summarizer Agent
Summarizes articles using LLM as a tool
"""

import re
import asyncio
from typing import Any, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.tool_base import Tool, ToolResult
from app.core.llm_client import LLMClientFactory
from app.database import Database, ArticleModel
from app.core.config_manager import get_config


# Max concurrent LLM calls to prevent resource exhaustion
LLM_SEMAPHORE = asyncio.Semaphore(3)


class SummarizeTool(Tool):
    """Tool for summarizing articles using LLM."""
    
    def __init__(self):
        self.llm = LLMClientFactory.create()
    
    @property
    def name(self) -> str:
        return "summarize_article"
    
    @property
    def description(self) -> str:
        return "Summarize an article using AI. Extracts key points, category, and sentiment."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "article_id": {
                    "type": "integer",
                    "description": "ID of the article to summarize"
                },
                "style": {
                    "type": "string",
                    "enum": ["short", "concise", "medium", "long"],
                    "description": "Summary style/length",
                    "default": "concise"
                }
            },
            "required": ["article_id"]
        }
    
    async def execute(
        self,
        article_id: int,
        style: str = "concise"
    ) -> ToolResult:
        """Execute the summarize tool."""
        try:
            # Get article
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
                
                # Generate summary
                summary_data = await self._summarize(article, style)
                
                # Update article
                article.summary = summary_data["summary"]
                article.category = summary_data["category"]
                article.sentiment = summary_data["sentiment"]
                article.reading_time = summary_data["reading_time"]
                article.key_points = summary_data["key_points"]
                article.is_processed = True
                
                await db.commit()
                
                return ToolResult(
                    success=True,
                    data=summary_data,
                    message=f"Successfully summarized article '{article.title[:50]}...'"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    async def _summarize_with_retry(self, article: ArticleModel, style: str) -> Dict[str, Any]:
        """Generate summary using LLM with retry logic."""
        
        style_instructions = {
            'short': 'Provide a 1-2 sentence summary.',
            'concise': 'Provide a 2-3 sentence summary.',
            'medium': 'Provide a 3-4 sentence summary.',
            'long': 'Provide a paragraph summary (5-6 sentences).'
        }
        
        length_instruction = style_instructions.get(style, style_instructions['concise'])
        
        # Truncate content to avoid token limits
        max_content_length = 4000
        content = article.content[:max_content_length] if article.content else ""
        
        prompt = f"""You are a professional news summarizer. Create a clear, accurate summary of this article.

ARTICLE TITLE: {article.title}

ARTICLE CONTENT:
{content}

INSTRUCTIONS:
{length_instruction}
- Focus on key facts and main points
- Maintain a neutral, objective tone
- Do not include your own opinions
- Be accurate and faithful to the original

OUTPUT FORMAT (respond in this exact format):
SUMMARY: [Your summary here]

CATEGORY: [Choose one: Technology, Business, Science, Politics, Health, Entertainment, Sports, AI/ML, Finance, or General]

SENTIMENT: [Positive, Negative, or Neutral]

KEY POINTS:
- [Point 1]
- [Point 2]
- [Point 3]

READING TIME: [Estimated minutes to read the original article, just the number]"""
        
        # Use semaphore to limit concurrent LLM calls
        async with LLM_SEMAPHORE:
            response = await self.llm.generate(prompt=prompt, temperature=0.5, max_tokens=800)
        
        # Parse response
        return self._parse_response(response.text)
    
    async def _summarize(self, article: ArticleModel, style: str) -> Dict[str, Any]:
        """Generate summary using LLM."""
        return await self._summarize_with_retry(article, style)
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response."""
        
        # Extract summary
        summary_match = re.search(
            r'SUMMARY:\s*(.+?)(?=\n\n|\n[A-Z]|$)',
            response,
            re.DOTALL | re.IGNORECASE
        )
        summary_text = summary_match.group(1).strip() if summary_match else response[:500]
        
        # Extract category
        category_match = re.search(r'CATEGORY:\s*(\w+)', response, re.IGNORECASE)
        category = category_match.group(1).strip() if category_match else "General"
        
        # Extract sentiment
        sentiment_match = re.search(r'SENTIMENT:\s*(\w+)', response, re.IGNORECASE)
        sentiment = sentiment_match.group(1).strip() if sentiment_match else "Neutral"
        
        # Extract key points
        key_points = []
        points_section = re.search(
            r'KEY POINTS:(.+?)(?=READING TIME|$)',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if points_section:
            points_text = points_section.group(1)
            key_points = [
                p.strip('- ').strip()
                for p in points_text.split('\n')
                if p.strip().startswith('-')
            ]
        
        # Extract reading time
        time_match = re.search(r'READING TIME:\s*(\d+)', response, re.IGNORECASE)
        reading_time = int(time_match.group(1)) if time_match else 1
        
        return {
            "summary": summary_text,
            "category": category,
            "sentiment": sentiment,
            "key_points": key_points[:5],
            "reading_time": max(1, reading_time)
        }
