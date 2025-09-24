"""
Logging configuration for OmniCore AI Platform
"""

import logging
import sys
from loguru import logger
from app.core.config import settings

def setup_logging():
    """Setup logging configuration"""
    
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stdout,
        format=settings.log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file logger for errors
    logger.add(
        "logs/error.log",
        format=settings.log_format,
        level="ERROR",
        rotation="10 MB",
        retention="1 week",
        compression="zip"
    )
    
    # Add file logger for all logs
    logger.add(
        "logs/omnicore.log",
        format=settings.log_format,
        level="INFO",
        rotation="100 MB",
        retention="30 days",
        compression="zip"
    )
    
    # Intercept standard library logging
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_name == 'emit':
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    # Intercept standard library logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Suppress some noisy loggers
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('motor').setLevel(logging.WARNING)
    
    logger.info("🚀 Logging system initialized")
