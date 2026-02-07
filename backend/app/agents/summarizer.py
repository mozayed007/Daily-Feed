"""Summarizer Agent - Summarizes articles using LLM"""

import json
import logging
import re
from typing import List, Optional
from dataclasses import dataclass

from app.core.llm_client import BaseLLMClient, LLMClientFactory
from app.database import ArticleModel

logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    """Summary result"""
    text: str
    key_points: List[str]
    category: str
    sentiment: str
    reading_time: int
    success: bool = True
    error: Optional[str] = None


class SummarizerAgent:
    """Agent responsible for summarizing articles"""
    
    def __init__(self, llm_client: BaseLLMClient = None):
        self.llm = llm_client or LLMClientFactory.create()
    
    async def summarize_article(
        self, 
        article: ArticleModel,
        style: str = "concise"
    ) -> SummaryResult:
        """Summarize a single article"""
        
        try:
            prompt = self._build_prompt(article, style)
            
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=800
            )
            
            result = self._parse_response(response.text)
            logger.info(f"Summarized: {article.title[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error summarizing article {article.id}: {e}")
            content = article.content or ""
            return SummaryResult(
                text=content[:300] + "..." if len(content) > 300 else content,
                key_points=[],
                category=article.category or "General",
                sentiment="Neutral",
                reading_time=self._estimate_reading_time(content),
                success=False,
                error=str(e)
            )
    
    async def summarize_batch(
        self, 
        articles: List[ArticleModel],
        style: str = "concise"
    ) -> List[SummaryResult]:
        """Summarize multiple articles"""
        results = []
        for article in articles:
            result = await self.summarize_article(article, style)
            results.append(result)
        return results
    
    def _build_prompt(self, article: ArticleModel, style: str) -> str:
        """Build the summarization prompt"""
        
        style_instructions = {
            'short': 'Provide a 1-2 sentence summary.',
            'concise': 'Provide a 2-3 sentence summary.',
            'medium': 'Provide a 3-4 sentence summary.',
            'long': 'Provide a paragraph summary (5-6 sentences).'
        }
        
        length_instruction = style_instructions.get(style, style_instructions['concise'])
        
        prompt = f"""You are a professional news summarizer. Create a clear, accurate summary of this article.

ARTICLE TITLE: {article.title}

ARTICLE CONTENT:
{(article.content or "")[:4000]}

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

        return prompt
    
    def _parse_response(self, response: str) -> SummaryResult:
        """Parse LLM response into SummaryResult"""
        
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
        
        return SummaryResult(
            text=summary_text,
            key_points=key_points[:5],  # Limit to 5 points
            category=category,
            sentiment=sentiment,
            reading_time=max(1, reading_time)
        )
    
    def _estimate_reading_time(self, content: str) -> int:
        """Estimate reading time in minutes"""
        words = len(content.split())
        minutes = max(1, round(words / 200))  # 200 words per minute
        return minutes
