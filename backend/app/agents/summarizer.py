"""Summarizer Agent - Summarizes articles using Pydantic AI"""

import logging
from typing import List, Optional, Literal
from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import KnownModelName

from app.database import ArticleModel
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SummaryResult(BaseModel):
    """Structured summary result"""
    text: str = Field(description="The actual summary text")
    key_points: List[str] = Field(description="List of 3-5 key points")
    category: Literal[
        "Technology", "Business", "Science", "Politics", 
        "Health", "Entertainment", "Sports", "AI/ML", 
        "Finance", "General"
    ] = Field(description="The primary category of the article")
    sentiment: Literal["Positive", "Negative", "Neutral"] = Field(description="The overall sentiment")
    reading_time: int = Field(description="Estimated reading time in minutes")


@dataclass
class SummarizerDependencies:
    article: ArticleModel
    style: str


# Define the agent
# We use a dynamic model based on settings, or default to a reasonable one
def get_model_name() -> str:
    provider = settings.LLM_PROVIDER
    if provider == "ollama":
        return f"ollama:{settings.OLLAMA_MODEL}"
    elif provider == "openai":
        return settings.OPENAI_MODEL
    elif provider == "anthropic":
        return settings.ANTHROPIC_MODEL
    elif provider == "gemini":
        return "google-gla:gemini-3-flash-preview"
    return "gpt-3.5-turbo"

agent = Agent(
    model=get_model_name(),
    result_type=SummaryResult,
    system_prompt=(
        "You are a professional news summarizer. "
        "Create a clear, accurate summary of the provided article. "
        "Focus on key facts, maintain neutrality, and be accurate."
    ),
)


class SummarizerAgent:
    """Agent responsible for summarizing articles using Pydantic AI"""
    
    def __init__(self):
        # We can initialize different agents here if needed
        pass
    
    async def summarize_article(
        self, 
        article: ArticleModel,
        style: str = "concise"
    ) -> SummaryResult:
        """Summarize a single article"""
        
        style_instructions = {
            'short': 'Provide a 1-2 sentence summary.',
            'concise': 'Provide a 2-3 sentence summary.',
            'medium': 'Provide a 3-4 sentence summary.',
            'long': 'Provide a paragraph summary (5-6 sentences).'
        }
        
        instruction = style_instructions.get(style, style_instructions['concise'])
        
        prompt = f"""
        ARTICLE TITLE: {article.title}
        
        ARTICLE CONTENT:
        {article.content[:4000]}
        
        INSTRUCTIONS:
        {instruction}
        """
        
        try:
            # Run the agent
            # We might need to set API keys in env vars for pydantic-ai to pick them up
            # (which we did in the LiteLLM client, but here we are using pydantic-ai directly)
            # Pydantic AI uses similar env vars (OPENAI_API_KEY, etc.) or allows passing client.
            
            # Ensure env vars are set
            import os
            if settings.Gemini_API_KEY and "GEMINI_API_KEY" not in os.environ:
                os.environ["GEMINI_API_KEY"] = settings.Gemini_API_KEY
            
            result = await agent.run(prompt)
            
            logger.info(f"Summarized: {article.title[:50]}...")
            return result.data
            
        except Exception as e:
            logger.error(f"Error summarizing article {article.id}: {e}")
            # Fallback
            return SummaryResult(
                text=article.content[:300] + "..." if len(article.content) > 300 else article.content,
                key_points=[],
                category="General",
                sentiment="Neutral",
                reading_time=max(1, len(article.content.split()) // 200)
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
