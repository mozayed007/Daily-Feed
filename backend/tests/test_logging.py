"""Tests for structured logging configuration"""

import logging
import json
from io import StringIO

import pytest
import structlog

from app.core.logging_config import get_logger, configure_logging


class TestStructuredLogging:
    """Tests for structured logging"""
    
    def test_get_logger_returns_bound_logger(self):
        """Test that get_logger returns a structlog BoundLogger"""
        logger = get_logger("test")
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
    
    def test_logger_with_context(self):
        """Test logger with bound context"""
        logger = get_logger("test", component="test_component", request_id="123")
        
        # Verify context is bound
        assert logger._context.get("component") == "test_component"
        assert logger._context.get("request_id") == "123"
    
    def test_log_output_contains_expected_fields(self, caplog):
        """Test that log output contains expected structured fields"""
        # Configure structlog for testing
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            logger_factory=structlog.PrintLoggerFactory(),
        )
        
        # Create a string buffer to capture output
        import io
        import sys
        
        captured = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured
        
        try:
            logger = structlog.get_logger("test")
            logger.info("test_event", key="value", number=42)
            
            output = captured.getvalue()
            # Should be valid JSON
            log_entry = json.loads(output.strip())
            
            assert log_entry["event"] == "test_event"
            assert log_entry["key"] == "value"
            assert log_entry["number"] == 42
            assert "timestamp" in log_entry
            assert log_entry["level"] == "info"
        finally:
            sys.stdout = original_stdout


class TestLoggingConfiguration:
    """Tests for logging configuration"""
    
    def test_configure_logging_runs_without_error(self):
        """Test that configure_logging doesn't raise exceptions"""
        # Should not raise
        try:
            configure_logging()
        except Exception as e:
            pytest.fail(f"configure_logging raised an exception: {e}")
    
    def test_noisy_loggers_set_to_warning(self):
        """Test that noisy third-party loggers are set to WARNING"""
        configure_logging()
        
        assert logging.getLogger("urllib3").level == logging.WARNING
        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("httpcore").level == logging.WARNING
