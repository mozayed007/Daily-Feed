"""LLM Client - Unified interface for multiple LLM providers"""

import json
import re
import logging
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass
from abc import ABC, abstractmethod

import httpx
import ollama
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

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


class OllamaClient(BaseLLMClient):
    """Ollama LLM client for local models"""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.OLLAMA_URL
        self.model = model or settings.OLLAMA_MODEL
        self.client = ollama.AsyncClient(host=self.base_url)
        
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """Generate text using Ollama"""
        try:
            options = {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
            
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                system=system or "",
                options=options
            )
            
            return LLMResponse(
                text=response['response'],
                model=self.model,
                tokens_used=response.get('eval_count', 0)
            )
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """Chat completion using Ollama"""
        try:
            options = {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
            
            response = await self.client.chat(
                model=self.model,
                messages=messages,
                options=options
            )
            
            return LLMResponse(
                text=response['message']['content'],
                model=self.model
            )
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise
    
    async def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = await self.client.list()
            return [m['name'] for m in response.get('models', [])]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    async def is_available(self) -> bool:
        """Check if Ollama server is available"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5
                )
                return response.status_code == 200
        except Exception:
            return False


class OpenAIClient(BaseLLMClient):
    """OpenAI client"""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """Generate text using OpenAI"""
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
        """Chat completion using OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return LLMResponse(
                text=response.choices[0].message.content,
                model=self.model,
                tokens_used=response.usage.total_tokens if response.usage else None,
                finish_reason=response.choices[0].finish_reason
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client"""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_MODEL
        self.client = AsyncAnthropic(api_key=self.api_key)
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """Generate text using Claude"""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, temperature, max_tokens, system)
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system: Optional[str] = None
    ) -> LLMResponse:
        """Chat completion using Claude"""
        try:
            response = await self.client.messages.create(
                model=self.model,
                messages=messages,
                system=system or "",
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return LLMResponse(
                text=response.content[0].text,
                model=self.model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens if response.usage else None
            )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


class LLMClientFactory:
    """Factory for creating LLM clients"""
    
    @staticmethod
    def create(provider: str = None) -> BaseLLMClient:
        """Create LLM client based on provider"""
        provider = provider or settings.LLM_PROVIDER
        
        if provider == "ollama":
            return OllamaClient()
        elif provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set")
            return OpenAIClient()
        elif provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not set")
            return AnthropicClient()
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    @staticmethod
    async def get_available_providers() -> Dict[str, Any]:
        """Get list of available providers"""
        providers = {
            "ollama": {"available": False, "models": []},
            "openai": {"available": bool(settings.OPENAI_API_KEY)},
            "anthropic": {"available": bool(settings.ANTHROPIC_API_KEY)}
        }
        
        # Check Ollama
        try:
            ollama = OllamaClient()
            if await ollama.is_available():
                providers["ollama"]["available"] = True
                providers["ollama"]["models"] = await ollama.list_models()
        except Exception:
            pass
        
        return providers


# Convenience function
async def get_llm_client() -> BaseLLMClient:
    """Get configured LLM client"""
    return LLMClientFactory.create()
