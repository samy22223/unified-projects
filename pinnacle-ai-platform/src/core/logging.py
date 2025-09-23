"""
Logging configuration for Pinnacle AI Platform.

This module provides centralized logging configuration with structured logging,
multiple output formats, and configurable log levels.
"""

import logging
import logging.config
import sys
from typing import Dict, Any
from pathlib import Path

from src.core.config.settings import settings


def setup_logging(log_level: str = None, log_format: str = None) -> logging.Logger:
    """
    Setup logging configuration for the application.

    Args:
        log_level: Override default log level
        log_format: Override default log format

    Returns:
        Configured logger instance
    """
    if log_level is None:
        log_level = settings.LOG_LEVEL
    if log_format is None:
        log_format = settings.LOG_FORMAT

    # Base logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "json": {
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
            },
            "simple": {
                "format": "%(levelname)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": log_format,
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.FileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": "logs/pinnacle.log",
                "encoding": "utf-8"
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file"]
        },
        "loggers": {
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }

    # Apply configuration
    logging.config.dictConfig(config)

    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Get logger for the application
    logger = logging.getLogger("pinnacle")

    # Add startup message
    logger.info("🚀 Pinnacle AI Platform logging initialized")
    logger.info(f"📊 Log level: {log_level}")
    logger.info(f"📝 Log format: {log_format}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"pinnacle.{name}")


class LogContext:
    """Context manager for adding contextual information to logs."""

    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context

    def __enter__(self):
        # Add context to logger
        for key, value in self.context.items():
            self.logger = logging.LoggerAdapter(self.logger, {key: value})
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def log_function_call(logger: logging.Logger):
    """Decorator to log function calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__}")
            result = func(*args, **kwargs)
            logger.debug(f"Finished {func.__name__}")
            return result
        return wrapper
    return decorator


def log_performance(logger: logging.Logger, threshold_ms: int = 1000):
    """Decorator to log function performance."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000

            if execution_time > threshold_ms:
                logger.warning(f"Slow function {func.__name__}: {execution_time".2f"}ms")
            else:
                logger.debug(f"Function {func.__name__}: {execution_time".2f"}ms")

            return result

        def sync_wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000

            if execution_time > threshold_ms:
                logger.warning(f"Slow function {func.__name__}: {execution_time".2f"}ms")
            else:
                logger.debug(f"Function {func.__name__}: {execution_time".2f"}ms")

            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator</code></edit>
</environment_details>