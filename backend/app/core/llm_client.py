"""LLM Client - Unified interface using LiteLLM"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

from litellm import acompletion
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class LLMResponse:
    """Standardized LLM response"""
    text: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        pass


class LiteLLMClient(BaseLLMClient):
    """Unified LLM client using LiteLLM"""
    
    def __init__(self, model: str = None):
        self.model = model or self._get_default_model()
        
    def _get_default_model(self) -> str:
        provider = settings.LLM_PROVIDER
        if provider == "ollama":
            return f"ollama/{settings.OLLAMA_MODEL}"
        elif provider == "openai":
            return settings.OPENAI_MODEL
        elif provider == "anthropic":
            return settings.ANTHROPIC_MODEL
        elif provider == "gemini":
            # LiteLLM format for Gemini
            return "gemini/gemini-3-flash-preview"
        return "gpt-3.5-turbo"

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """Generate text using LiteLLM"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        return await self.chat(messages, temperature, max_tokens)
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """Chat completion using LiteLLM"""
        try:
            # Map settings keys to environment variables LiteLLM expects if not already set
            # Ideally these should be set in environment variables (e.g. GEMINI_API_KEY)
            # But we can pass them explicitly if needed, or rely on os.environ
            
            # LiteLLM handles environment variables automatically:
            # OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, etc.
            # Our .env file likely sets them, or they are loaded in settings.
            
            # For Gemini specifically, LiteLLM expects GEMINI_API_KEY or GOOGLE_API_KEY
            # Our settings has Gemini_API_KEY.
            import os
            if settings.Gemini_API_KEY and "GEMINI_API_KEY" not in os.environ:
                os.environ["GEMINI_API_KEY"] = settings.Gemini_API_KEY
            if settings.OPENAI_API_KEY and "OPENAI_API_KEY" not in os.environ:
                os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
            if settings.ANTHROPIC_API_KEY and "ANTHROPIC_API_KEY" not in os.environ:
                os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
                
            response = await acompletion(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_base=settings.OLLAMA_URL if "ollama" in self.model else None
            )
            
            return LLMResponse(
                text=response.choices[0].message.content,
                model=self.model,
                tokens_used=response.usage.total_tokens if response.usage else None,
                finish_reason=response.choices[0].finish_reason
            )
        except Exception as e:
            logger.error(f"LiteLLM error: {e}")
            raise


class LLMClientFactory:
    """Factory for creating LLM clients"""
    
    @staticmethod
    def create(provider: str = None) -> BaseLLMClient:
        """Create LLM client based on provider"""
        # We now use LiteLLMClient for everything, just configuring the model
        return LiteLLMClient()
    
    @staticmethod
    async def get_available_providers() -> Dict[str, Any]:
        """Get list of available providers"""
        # Simplified since LiteLLM supports many
        return {
            "ollama": {"available": True},
            "openai": {"available": bool(settings.OPENAI_API_KEY)},
            "anthropic": {"available": bool(settings.ANTHROPIC_API_KEY)},
            "gemini": {"available": bool(settings.Gemini_API_KEY)}
        }


# Convenience function
async def get_llm_client() -> BaseLLMClient:
    """Get configured LLM client"""
    return LLMClientFactory.create()
