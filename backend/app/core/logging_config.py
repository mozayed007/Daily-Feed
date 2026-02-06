"""Structured logging configuration using structlog.

Provides JSON-formatted logs for production and colored console logs for development.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from app.core.config_manager import get_config


def configure_logging() -> None:
    """Configure structured logging for the application.
    
    Sets up:
    - structlog for application logging
    - Standard library logging integration
    - JSON formatting for production, colored console for development
    """
    config = get_config()
    is_development = config.debug
    
    # Shared processors for both structlog and stdlib logging
    shared_processors: list[Processor] = [
        # Add timestamp in ISO format
        structlog.processors.TimeStamper(fmt="iso"),
        # Add log level
        structlog.processors.add_log_level,
        # Replace exception info with a formatted traceback
        structlog.processors.format_exc_info,
        # Add caller info (file, line, function)
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]
    
    if is_development:
        # Development: colored console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
            foreign_pre_chain=shared_processors,
        )
    else:
        # Production: JSON formatting
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,
        )
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging to use structlog processors
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)
    
    # Set specific log levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Get a logger for this module
    logger = structlog.get_logger()
    logger.info(
        "logging_configured",
        debug=config.debug,
        log_level="INFO",
        json_format=not is_development,
    )


def get_logger(name: str | None = None, **context: Any) -> structlog.BoundLogger:
    """Get a structured logger with optional context.
    
    Args:
        name: Logger name (typically __name__)
        **context: Additional context to bind to all log messages
        
    Returns:
        A configured structlog logger
        
    Example:
        >>> logger = get_logger(__name__, component="fetch_tool")
        >>> logger.info("fetching_feed", url="https://example.com/feed")
        {"event": "fetching_feed", "url": "https://example.com/feed", 
         "component": "fetch_tool", "timestamp": "2026-01-04T..."}
    """
    logger = structlog.get_logger(name)
    if context:
        logger = logger.bind(**context)
    return logger
