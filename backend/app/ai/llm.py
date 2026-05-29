"""LLM factory using pydantic-ai with litellm for unified provider routing."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

try:
    from pydantic_ai_litellm import LiteLLMModel

    HAS_LITELLM = True
except ImportError:  # pragma: no cover
    HAS_LITELLM = False

try:
    from pydantic_ai.capabilities import WebFetch, WebSearch

    HAS_CAPABILITIES = True
except ImportError:  # pragma: no cover
    HAS_CAPABILITIES = False

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Provider registry ───────────────────────────────────────────────────────
# Adding a new provider = one dict entry, no function edits.


@dataclass(frozen=True)
class _ProviderSpec:
    """Static mapping from a Daily Feed provider name to litellm conventions."""

    prefix: str  # litellm model prefix (e.g. "openai", "gemini", "ollama")
    model_attr: str  # Settings attribute holding the model name
    api_key_attr: Optional[str] = None  # Settings attribute holding the API key
    api_base_attr: Optional[str] = None  # Settings attribute holding the base URL


_PROVIDER_REGISTRY: Dict[str, _ProviderSpec] = {
    "ollama": _ProviderSpec("ollama", "OLLAMA_MODEL", api_base_attr="OLLAMA_URL"),
    "openai": _ProviderSpec("openai", "OPENAI_MODEL", api_key_attr="OPENAI_API_KEY"),
    "anthropic": _ProviderSpec("anthropic", "ANTHROPIC_MODEL", api_key_attr="ANTHROPIC_API_KEY"),
    "gemini": _ProviderSpec(
        "gemini", "GEMINI_MODEL", api_key_attr="GEMINI_API_KEY", api_base_attr="GEMINI_BASE_URL"
    ),
    "fireworks": _ProviderSpec(
        "openai",
        "FIREWORKS_MODEL",
        api_key_attr="FIREWORKS_API_KEY",
        api_base_attr="FIREWORKS_BASE_URL",
    ),
    "openai-compatible": _ProviderSpec(
        "openai",
        "COMPAT_MODEL",
        api_key_attr="COMPAT_API_KEY",
        api_base_attr="COMPAT_BASE_URL",
    ),
}


def _get_litellm_model_name() -> str:
    """Map Daily Feed config to litellm model naming convention."""
    provider = settings.LLM_PROVIDER
    spec = _PROVIDER_REGISTRY.get(provider)
    if spec is None:
        raise ValueError(f"Unknown LLM provider: {provider}")
    model_name = getattr(settings, spec.model_attr)
    return f"{spec.prefix}/{model_name}"


def _get_litellm_kwargs() -> Dict[str, Any]:
    """Get provider-specific kwargs for LiteLLMModel."""
    provider = settings.LLM_PROVIDER
    spec = _PROVIDER_REGISTRY.get(provider)
    if spec is None:
        raise ValueError(f"Unknown LLM provider: {provider}")

    kwargs: Dict[str, Any] = {}
    if spec.api_key_attr:
        api_key = getattr(settings, spec.api_key_attr)
        if api_key:
            kwargs["api_key"] = api_key
    if spec.api_base_attr:
        kwargs["api_base"] = getattr(settings, spec.api_base_attr)
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


def _build_search_capabilities() -> Optional[list]:
    """Build provider-adaptive search/fetch capabilities from current settings.

    Reads ENABLE_WEB_SEARCH and ENABLE_URL_FETCH at call time (not import time)
    so env overrides take effect even after module load.

    The capabilities use the provider's native search/fetch when available,
    or gracefully fall back to local implementations (e.g., DuckDuckGo).
    """
    if not HAS_CAPABILITIES:
        return None

    s = get_settings()
    caps: list = []
    if s.ENABLE_WEB_SEARCH:
        caps.append(WebSearch())
    if s.ENABLE_URL_FETCH:
        caps.append(WebFetch())
    return caps or None


def create_agent(
    system_prompt: str = "",
    result_type: Optional[type] = None,
    model_override: Optional[str] = None,
    temperature: float = 0.5,
    max_tokens: int = 2000,
    tools: Optional[list] = None,
    capabilities: Optional[list] = None,
    search_enabled: bool = False,
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
        search_enabled: If True, automatically attach WebSearch + WebFetch
            capabilities based on current settings. Mutually exclusive with
            passing capabilities manually.

    Returns:
        A configured pydantic-ai Agent.
    """
    model = get_model(model_override)
    model_settings = ModelSettings(temperature=temperature, max_tokens=max_tokens)

    if search_enabled and capabilities is None:
        capabilities = _build_search_capabilities()

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
        "openai-compatible": {"available": bool(settings.COMPAT_API_KEY)},
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
