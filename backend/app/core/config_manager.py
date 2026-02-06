"""
Hybrid configuration system - JSON config + Environment variables
Inspired by nanobot's clean config approach
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """LLM configuration."""
    provider: LLMProvider = LLMProvider.OLLAMA
    model: str = "llama3.2"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 120


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = "sqlite+aiosqlite:///data/dailyfeed.db"
    echo: bool = False


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    enabled: bool = False
    token: Optional[str] = None
    chat_id: Optional[str] = None
    allow_from: List[str] = field(default_factory=list)


@dataclass
class ChannelConfig:
    """Channel/messaging configuration."""
    telegram: TelegramConfig = field(default_factory=TelegramConfig)


@dataclass
class FeedSource:
    """RSS feed source configuration."""
    name: str
    url: str
    category: str = "General"
    enabled: bool = True


@dataclass
class PipelineConfig:
    """Pipeline processing configuration."""
    max_articles_per_source: int = 15
    summary_max_length: int = 500
    critic_min_score: int = 7
    max_retries: int = 2
    auto_fetch_interval_minutes: int = 60
    auto_process_enabled: bool = True


@dataclass
class ScheduleConfig:
    """Scheduling configuration."""
    enabled: bool = True
    digest_hour: int = 8
    digest_minute: int = 0
    timezone: str = "UTC"


@dataclass
class MemoryConfig:
    """Memory system configuration."""
    enabled: bool = True
    db_path: str = "data/memory.db"
    synthesis_enabled: bool = True
    retention_days: int = 90
    min_importance_threshold: float = 0.3


@dataclass
class AppConfig:
    """Main application configuration."""
    # App info
    name: str = "Daily Feed"
    version: str = "1.1.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    cors_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:5173"
    ])
    
    # Sub-configs
    llm: LLMConfig = field(default_factory=LLMConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    channels: ChannelConfig = field(default_factory=ChannelConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    
    # Feed sources
    sources: List[FeedSource] = field(default_factory=lambda: [
        FeedSource(name="TechCrunch", url="https://techcrunch.com/feed/", category="Tech"),
        FeedSource(name="The Verge", url="https://www.theverge.com/rss/index.xml", category="Tech"),
        FeedSource(name="Hacker News", url="https://news.ycombinator.com/rss", category="Tech"),
        FeedSource(name="Smol AI", url="https://news.smol.ai/rss", category="AI")
    ])


class ConfigManager:
    """
    Hybrid configuration manager.
    
    Loads configuration from:
    1. Default values
    2. Config file (~/.dailyfeed/config.json)
    3. Environment variables (highest priority)
    """
    
    CONFIG_DIR = Path.home() / ".dailyfeed"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    ENV_PREFIX = "DAILYFEED_"
    
    def __init__(self):
        self._config: Optional[AppConfig] = None
    
    def _ensure_config_dir(self):
        """Ensure config directory exists."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> AppConfig:
        """Load configuration from all sources."""
        # Start with defaults
        config = AppConfig()
        
        # Load from file if exists
        file_config = self._load_from_file()
        if file_config:
            config = self._merge_config(config, file_config)
        
        # Override with environment variables
        config = self._load_from_env(config)
        
        self._config = config
        return config
    
    def _load_from_file(self) -> Optional[Dict[str, Any]]:
        """Load configuration from JSON file."""
        if not self.CONFIG_FILE.exists():
            return None
        
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config file: {e}")
            return None
    
    def _load_from_env(self, config: AppConfig) -> AppConfig:
        """Override config with environment variables."""
        # App settings
        if os.getenv(f"{self.ENV_PREFIX}DEBUG"):
            config.debug = os.getenv(f"{self.ENV_PREFIX}DEBUG").lower() in ("true", "1", "yes")
        
        if os.getenv(f"{self.ENV_PREFIX}PORT"):
            config.port = int(os.getenv(f"{self.ENV_PREFIX}PORT"))
        
        # LLM settings
        llm_provider = os.getenv(f"{self.ENV_PREFIX}LLM_PROVIDER")
        if llm_provider:
            config.llm.provider = LLMProvider(llm_provider.lower())
        
        if os.getenv(f"{self.ENV_PREFIX}OLLAMA_MODEL"):
            config.llm.model = os.getenv(f"{self.ENV_PREFIX}OLLAMA_MODEL")
        
        if os.getenv(f"{self.ENV_PREFIX}OLLAMA_URL"):
            config.llm.api_base = os.getenv(f"{self.ENV_PREFIX}OLLAMA_URL")
        
        if os.getenv("OPENAI_API_KEY"):
            config.llm.api_key = os.getenv("OPENAI_API_KEY")
            if config.llm.provider == LLMProvider.OLLAMA:
                config.llm.provider = LLMProvider.OPENAI
        
        if os.getenv("ANTHROPIC_API_KEY"):
            config.llm.api_key = os.getenv("ANTHROPIC_API_KEY")
            if config.llm.provider == LLMProvider.OLLAMA:
                config.llm.provider = LLMProvider.ANTHROPIC
        
        # Database
        if os.getenv(f"{self.ENV_PREFIX}DATABASE_URL"):
            config.database.url = os.getenv(f"{self.ENV_PREFIX}DATABASE_URL")
        
        # Telegram
        if os.getenv(f"{self.ENV_PREFIX}TELEGRAM_BOT_TOKEN"):
            config.channels.telegram.enabled = True
            config.channels.telegram.token = os.getenv(f"{self.ENV_PREFIX}TELEGRAM_BOT_TOKEN")
        
        if os.getenv(f"{self.ENV_PREFIX}TELEGRAM_CHAT_ID"):
            config.channels.telegram.chat_id = os.getenv(f"{self.ENV_PREFIX}TELEGRAM_CHAT_ID")
        
        # Pipeline
        if os.getenv(f"{self.ENV_PREFIX}MAX_ARTICLES"):
            config.pipeline.max_articles_per_source = int(os.getenv(f"{self.ENV_PREFIX}MAX_ARTICLES"))
        
        if os.getenv(f"{self.ENV_PREFIX}CRITIC_MIN_SCORE"):
            config.pipeline.critic_min_score = int(os.getenv(f"{self.ENV_PREFIX}CRITIC_MIN_SCORE"))
        
        # Schedule
        if os.getenv(f"{self.ENV_PREFIX}SCHEDULER_ENABLED"):
            config.schedule.enabled = os.getenv(f"{self.ENV_PREFIX}SCHEDULER_ENABLED").lower() in ("true", "1", "yes")
        
        return config
    
    def _merge_config(self, base: AppConfig, override: Dict[str, Any]) -> AppConfig:
        """Merge file config into base config."""
        # Simple recursive merge
        base_dict = asdict(base)
        merged = self._deep_merge(base_dict, override)
        
        # Convert back to dataclass
        return self._dict_to_config(merged)
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _dict_to_config(self, data: Dict[str, Any]) -> AppConfig:
        """Convert dictionary to AppConfig."""
        # Handle LLM config
        llm_data = data.get("llm", {})
        llm_config = LLMConfig(**{
            k: v for k, v in llm_data.items()
            if k in LLMConfig.__dataclass_fields__
        })
        if isinstance(llm_data.get("provider"), str):
            llm_config.provider = LLMProvider(llm_data["provider"].lower())
        
        # Handle sources
        sources_data = data.get("sources", [])
        sources = [
            FeedSource(**{
                k: v for k, v in s.items()
                if k in FeedSource.__dataclass_fields__
            })
            for s in sources_data
        ]
        
        # Build config
        return AppConfig(
            name=data.get("name", "Daily Feed"),
            version=data.get("version", "1.1.0"),
            debug=data.get("debug", False),
            host=data.get("host", "0.0.0.0"),
            port=data.get("port", 8000),
            cors_origins=data.get("cors_origins", ["http://localhost:3000"]),
            llm=llm_config,
            database=DatabaseConfig(**{
                k: v for k, v in data.get("database", {}).items()
                if k in DatabaseConfig.__dataclass_fields__
            }),
            channels=ChannelConfig(
                telegram=TelegramConfig(**{
                    k: v for k, v in data.get("channels", {}).get("telegram", {}).items()
                    if k in TelegramConfig.__dataclass_fields__
                })
            ),
            pipeline=PipelineConfig(**{
                k: v for k, v in data.get("pipeline", {}).items()
                if k in PipelineConfig.__dataclass_fields__
            }),
            schedule=ScheduleConfig(**{
                k: v for k, v in data.get("schedule", {}).items()
                if k in ScheduleConfig.__dataclass_fields__
            }),
            memory=MemoryConfig(**{
                k: v for k, v in data.get("memory", {}).items()
                if k in MemoryConfig.__dataclass_fields__
            }),
            sources=sources
        )
    
    def save(self, config: AppConfig):
        """Save configuration to file."""
        self._ensure_config_dir()
        
        data = asdict(config)
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_default_config(self):
        """Create default configuration file."""
        self._ensure_config_dir()
        
        default_config = {
            "name": "Daily Feed",
            "debug": False,
            "llm": {
                "provider": "ollama",
                "model": "llama3.2",
                "api_base": "http://localhost:11434",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "channels": {
                "telegram": {
                    "enabled": False,
                    "token": None,
                    "chat_id": None
                }
            },
            "pipeline": {
                "max_articles_per_source": 15,
                "critic_min_score": 7,
                "auto_process_enabled": True
            },
            "schedule": {
                "enabled": True,
                "digest_hour": 8,
                "digest_minute": 0
            },
            "memory": {
                "enabled": True,
                "retention_days": 90,
                "synthesis_enabled": True
            },
            "sources": [
                {
                    "name": "Hacker News",
                    "url": "https://news.ycombinator.com/rss",
                    "category": "Technology",
                    "enabled": True
                },
                {
                    "name": "TechCrunch",
                    "url": "https://techcrunch.com/feed/",
                    "category": "Technology",
                    "enabled": True
                },
                {
                    "name": "The Verge",
                    "url": "https://www.theverge.com/rss/index.xml",
                    "category": "Technology",
                    "enabled": True
                },
                {
                    "name": "WSJ Business",
                    "url": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
                    "category": "Business",
                    "enabled": True
                },
                {
                    "name": "WSJ Tech",
                    "url": "https://feeds.a.dj.com/rss/RSSWSJD.xml",
                    "category": "Technology",
                    "enabled": True
                },
                {
                    "name": "The Global Economics",
                    "url": "https://theglobaleconomics.com/feed/",
                    "category": "Economics",
                    "enabled": True
                },
                {
                    "name": "Smol AI News",
                    "url": "https://news.smol.ai/rss",
                    "category": "AI/ML",
                    "enabled": True
                },
                {
                    "name": "Ars Technica",
                    "url": "https://feeds.arstechnica.com/arstechnica/index",
                    "category": "Technology",
                    "enabled": False
                },
                {
                    "name": "GitHub Blog",
                    "url": "https://github.blog/feed/",
                    "category": "Programming",
                    "enabled": False
                },
                {
                    "name": "MIT Technology Review",
                    "url": "https://www.technologyreview.com/feed/",
                    "category": "Science",
                    "enabled": False
                },
                {
                    "name": "Wired",
                    "url": "https://www.wired.com/feed/rss",
                    "category": "Technology",
                    "enabled": False
                }
            ]
        }
        
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"Created default config at {self.CONFIG_FILE}")
    
    def get(self) -> AppConfig:
        """Get current config, loading if necessary."""
        if self._config is None:
            return self.load()
        return self._config


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global config manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """Get current application configuration."""
    return get_config_manager().get()
