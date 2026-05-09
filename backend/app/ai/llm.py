"""LLM factory using pydantic-ai with litellm for unified provider routing."""

import logging
from typing import Any, Dict, Optional

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

try:
    from pydantic_ai_litellm import LiteLLMModel

    HAS_LITELLM = True
except ImportError:  # pragma: no cover
    HAS_LITELLM = False

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_litellm_model_name() -> str:
    """Map Daily Feed config to litellm model naming convention."""
    provider = settings.LLM_PROVIDER

    if provider == "ollama":
        return f"ollama/{settings.OLLAMA_MODEL}"
    elif provider == "openai":
        return f"openai/{settings.OPENAI_MODEL}"
    elif provider == "anthropic":
        return f"anthropic/{settings.ANTHROPIC_MODEL}"
    elif provider == "gemini":
        return f"gemini/{settings.GEMINI_MODEL}"
    elif provider == "fireworks":
        return f"openai/{settings.FIREWORKS_MODEL}"
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def _get_litellm_kwargs() -> Dict[str, Any]:
    """Get provider-specific kwargs for LiteLLMModel."""
    provider = settings.LLM_PROVIDER
    kwargs: Dict[str, Any] = {}

    if provider == "ollama":
        kwargs["api_base"] = settings.OLLAMA_URL
    elif provider == "openai":
        if settings.OPENAI_API_KEY:
            kwargs["api_key"] = settings.OPENAI_API_KEY
    elif provider == "anthropic":
        if settings.ANTHROPIC_API_KEY:
            kwargs["api_key"] = settings.ANTHROPIC_API_KEY
    elif provider == "gemini":
        if settings.GEMINI_API_KEY:
            kwargs["api_key"] = settings.GEMINI_API_KEY
        kwargs["api_base"] = settings.GEMINI_BASE_URL
    elif provider == "fireworks":
        if settings.FIREWORKS_API_KEY:
            kwargs["api_key"] = settings.FIREWORKS_API_KEY
        kwargs["api_base"] = settings.FIREWORKS_BASE_URL

    return kwargs


def get_model(model_override: Optional[str] = None) -> Any:
    """Create a LiteLLMModel for pydantic-ai based on configuration.

    Args:
        model_override: Optional model string override (e.g., "openai/gpt-4o").

    Returns:
        A LiteLLMModel instance wired to the configured provider.
    """
    if not HAS_LITELLM:
        raise ImportError(
            "pydantic-ai-litellm is not installed. " "Run: pip install pydantic-ai-litellm"
        )

    model_name = model_override or _get_litellm_model_name()
    kwargs = _get_litellm_kwargs()

    logger.info(
        "Creating LiteLLMModel", extra={"model": model_name, "provider": settings.LLM_PROVIDER}
    )
    return LiteLLMModel(model_name=model_name, **kwargs)


def create_agent(
    system_prompt: str = "",
    result_type: Optional[type] = None,
    model_override: Optional[str] = None,
    temperature: float = 0.5,
    max_tokens: int = 2000,
    tools: Optional[list] = None,
    capabilities: Optional[list] = None,
) -> Agent:
    """Create a pydantic-ai Agent backed by litellm.

    Args:
        system_prompt: System instructions for the agent.
        result_type: Optional Pydantic BaseModel for structured outputs.
        model_override: Override the model (e.g., "openai/gpt-4o").
        temperature: Sampling temperature.
        max_tokens: Maximum tokens to generate.
        tools: Optional list of pydantic-ai tools to register.
        capabilities: Optional list of provider-adaptive capabilities
            (e.g., WebSearch(), WebFetch()). These gracefully fall back to
            local implementations when the provider does not support them.

    Returns:
        A configured pydantic-ai Agent.
    """
    model = get_model(model_override)
    model_settings = ModelSettings(temperature=temperature, max_tokens=max_tokens)

    agent = Agent(
        model=model,
        instructions=system_prompt,
        output_type=result_type or str,
        model_settings=model_settings,
        capabilities=capabilities,
    )
    if tools:
        for tool in tools:
            agent.tool(tool)
    return agent


async def get_available_providers() -> Dict[str, Any]:
    """Check which LLM providers are available (mirrors old LLMClientFactory)."""
    providers = {
        "ollama": {"available": False, "models": []},
        "openai": {"available": bool(settings.OPENAI_API_KEY)},
        "anthropic": {"available": bool(settings.ANTHROPIC_API_KEY)},
        "gemini": {"available": bool(settings.GEMINI_API_KEY)},
        "fireworks": {"available": bool(settings.FIREWORKS_API_KEY)},
        "litellm": {"available": HAS_LITELLM},
    }

    if HAS_LITELLM:
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.OLLAMA_URL}/api/tags",
                    timeout=5,
                )
                if response.status_code == 200:
                    data = response.json()
                    providers["ollama"]["available"] = True
                    providers["ollama"]["models"] = [
                        m.get("name", m.get("model", "")) for m in data.get("models", [])
                    ]
        except Exception:
            pass

    return providers
