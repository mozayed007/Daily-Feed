"""
Critique Tool - Converted from Quality Critic Agent
Validates summary quality as a tool
"""

import re
from typing import Any, Dict

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.tool_base import Tool, ToolResult
from app.core.llm_client import LLMClientFactory
from app.database import Database, ArticleModel
from app.core.config_manager import get_config


class CritiqueTool(Tool):
    """Tool for critiquing and validating summary quality."""
    
    def __init__(self):
        self.llm = LLMClientFactory.create()
        self.min_score = get_config().pipeline.critic_min_score
    
    @property
    def name(self) -> str:
        return "critique_summary"
    
    @property
    def description(self) -> str:
        return "Critique a summary for accuracy, completeness, clarity, and bias. Returns quality score."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "article_id": {
                    "type": "integer",
                    "description": "ID of the article to critique"
                }
            },
            "required": ["article_id"]
        }
    
    async def execute(self, article_id: int) -> ToolResult:
        """Execute the critique tool."""
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
                
                if not article.summary:
                    return ToolResult(
                        success=False,
                        data=None,
                        error="Article has no summary to critique"
                    )
                
                # Generate critique
                critique = await self._critique(article)
                
                # Update article with score
                article.critic_score = critique["overall_score"]
                await db.commit()
                
                passed = critique["overall_score"] >= self.min_score
                
                return ToolResult(
                    success=passed,
                    data=critique,
                    message=f"Critique complete. Score: {critique['overall_score']}/10 (threshold: {self.min_score})"
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
    async def _critique_with_retry(self, article: ArticleModel) -> Dict[str, Any]:
        """Generate critique using LLM with retry logic."""
        
        key_points_text = '\n'.join(f'- {p}' for p in (article.key_points or []))
        
        prompt = f"""You are a quality critic evaluating a news summary. Compare the summary to the original article and rate it objectively.

ORIGINAL ARTICLE TITLE: {article.title}

ORIGINAL ARTICLE CONTENT (first 3000 chars):
{article.content[:3000]}

SUMMARY TO EVALUATE:
{article.summary}

KEY POINTS IN SUMMARY:
{key_points_text}

EVALUATION CRITERIA:
1. ACCURACY (1-10): Does the summary accurately reflect the original? Are there factual errors?
2. COMPLETENESS (1-10): Does the summary capture the main points? Are important details missing?
3. CLARITY (1-10): Is the summary easy to understand? Is the language clear?
4. BIAS (1-10): Is the summary neutral and balanced?

OUTPUT FORMAT (respond in this exact format):
ACCURACY: [1-10]
COMPLETENESS: [1-10]
CLARITY: [1-10]
BIAS: [1-10]
OVERALL SCORE: [1-10, average of above, rounded]

ISSUES FOUND:
- [Issue 1, or "None"]

SUGGESTIONS FOR IMPROVEMENT:
[Your suggestions, or "None" if summary is good]"""
        
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=600
        )
        
        return self._parse_critique(response.text)
    
    async def _critique(self, article: ArticleModel) -> Dict[str, Any]:
        """Generate critique using LLM."""
        return await self._critique_with_retry(article)
    
    def _parse_critique(self, response: str) -> Dict[str, Any]:
        """Parse critique response."""
        
        def extract_score(metric: str) -> int:
            pattern = rf'{metric}:\s*(\d+)'
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return max(1, min(10, int(match.group(1))))
            return 0
        
        accuracy = extract_score('ACCURACY')
        completeness = extract_score('COMPLETENESS')
        clarity = extract_score('CLARITY')
        bias = extract_score('BIAS')
        overall = extract_score('OVERALL SCORE')
        
        # Use overall or calculate average
        overall_score = overall if overall > 0 else round((accuracy + completeness + clarity + bias) / 4)
        
        # Extract issues
        issues = []
        issues_match = re.search(
            r'ISSUES FOUND:(.+?)(?=SUGGESTIONS|$)',
            response,
            re.DOTALL | re.IGNORECASE
        )
        if issues_match:
            issues_text = issues_match.group(1)
            issues = [
                i.strip('- ').strip()
                for i in issues_text.split('\n')
                if i.strip().startswith('-')
            ]
            issues = [i for i in issues if i.lower() not in ('none', '', 'n/a')]
        
        # Extract suggestions
        suggestions_match = re.search(
            r'SUGGESTIONS FOR IMPROVEMENT:(.+?)$',
            response,
            re.DOTALL | re.IGNORECASE
        )
        suggestions = suggestions_match.group(1).strip() if suggestions_match else ""
        if suggestions.lower() in ('none', 'n/a'):
            suggestions = ""
        
        return {
            "accuracy": accuracy,
            "completeness": completeness,
            "clarity": clarity,
            "bias": bias,
            "overall_score": overall_score,
            "issues": issues,
            "suggestions": suggestions,
            "passed": overall_score >= self.min_score
        }
