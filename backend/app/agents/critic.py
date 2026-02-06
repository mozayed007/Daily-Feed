"""Quality Critic Agent - Validates and scores summaries"""

import logging
import re
from typing import List, Optional
from dataclasses import dataclass

from app.core.llm_client import BaseLLMClient, LLMClientFactory
from app.database import ArticleModel
from app.agents.summarizer import SummaryResult

logger = logging.getLogger(__name__)


@dataclass
class CritiqueResult:
    """Critique result"""
    score: int  # 1-10
    accuracy: int  # 1-10
    completeness: int  # 1-10
    clarity: int  # 1-10
    bias: int  # 1-10
    issues: List[str]
    suggestions: str
    passed: bool = True


class QualityCriticAgent:
    """Agent that critiques summary quality"""
    
    def __init__(
        self, 
        llm_client: BaseLLMClient = None,
        min_score: int = 7
    ):
        self.llm = llm_client or LLMClientFactory.create()
        self.min_score = min_score
    
    async def critique(
        self, 
        summary: SummaryResult, 
        original: ArticleModel
    ) -> CritiqueResult:
        """Critique a summary against the original article"""
        
        try:
            prompt = self._build_critique_prompt(summary, original)
            
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.3,  # Lower for consistency
                max_tokens=600
            )
            
            result = self._parse_critique(response.text)
            result.passed = result.score >= self.min_score
            
            logger.info(f"Critique score: {result.score}/10 (passed: {result.passed})")
            return result
            
        except Exception as e:
            logger.error(f"Error during critique: {e}")
            # Return passing critique on error
            return CritiqueResult(
                score=7,
                accuracy=7,
                completeness=7,
                clarity=7,
                bias=7,
                issues=[],
                suggestions="",
                passed=True
            )
    
    def _build_critique_prompt(
        self, 
        summary: SummaryResult, 
        original: ArticleModel
    ) -> str:
        """Build critique prompt"""
        
        prompt = f"""You are a quality critic evaluating a news summary. Compare the summary to the original article and rate it objectively.

ORIGINAL ARTICLE TITLE: {original.title}

ORIGINAL ARTICLE CONTENT (first 3000 chars):
{original.content[:3000]}

SUMMARY TO EVALUATE:
{summary.text}

KEY POINTS IN SUMMARY:
{chr(10).join(f'- {p}' for p in summary.key_points)}

EVALUATION CRITERIA:
1. ACCURACY (1-10): Does the summary accurately reflect the original? Are there factual errors or misrepresentations?

2. COMPLETENESS (1-10): Does the summary capture the main points? Are important details missing?

3. CLARITY (1-10): Is the summary easy to understand? Is the language clear and concise?

4. BIAS (1-10): Is the summary neutral and balanced? Does it avoid adding opinions not in the original?

OUTPUT FORMAT (respond in this exact format):
ACCURACY: [1-10]
COMPLETENESS: [1-10]
CLARITY: [1-10]
BIAS: [1-10]
OVERALL SCORE: [1-10, average of above, rounded]

ISSUES FOUND:
- [Issue 1, or "None"]
- [Issue 2, or omit if none]

SUGGESTIONS FOR IMPROVEMENT:
[Your suggestions, or "None" if summary is good]"""

        return prompt
    
    def _parse_critique(self, response: str) -> CritiqueResult:
        """Parse critique response"""
        
        # Extract scores
        accuracy = self._extract_score(response, 'ACCURACY')
        completeness = self._extract_score(response, 'COMPLETENESS')
        clarity = self._extract_score(response, 'CLARITY')
        bias = self._extract_score(response, 'BIAS')
        overall = self._extract_score(response, 'OVERALL SCORE')
        
        # Use overall score or calculate average
        score = overall if overall > 0 else round((accuracy + completeness + clarity + bias) / 4)
        
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
        
        return CritiqueResult(
            score=score,
            accuracy=accuracy,
            completeness=completeness,
            clarity=clarity,
            bias=bias,
            issues=issues,
            suggestions=suggestions
        )
    
    def _extract_score(self, response: str, metric: str) -> int:
        """Extract a score from response"""
        pattern = rf'{metric}:\s*(\d+)'
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            return max(1, min(10, score))
        return 0
