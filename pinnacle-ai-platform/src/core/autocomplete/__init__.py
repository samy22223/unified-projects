"""
Auto-Completion System for Pinnacle AI Platform

This package provides a comprehensive auto-completion system with multiple providers,
caching, context management, and API endpoints for intelligent code and text completion.
"""

from .service import AutoCompletionService
from .cache import AutoCompletionCache
from .context import AutoCompletionContext
from .providers.base import BaseAutoCompletionProvider
from .providers.ai_agent import AIAgentProvider
from .providers.api_endpoint import APIEndpointProvider
from .providers.database import DatabaseProvider
from .providers.ui import UIProvider
from .providers.cli import CLIProvider
from .providers.config import ConfigProvider
from .providers.search import SearchProvider

__version__ = "1.0.0"
__all__ = [
    "AutoCompletionService",
    "AutoCompletionCache",
    "AutoCompletionContext",
    "BaseAutoCompletionProvider",
    "AIAgentProvider",
    "APIEndpointProvider",
    "DatabaseProvider",
    "UIProvider",
    "CLIProvider",
    "ConfigProvider",
    "SearchProvider"
]