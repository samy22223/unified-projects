"""
Base Auto-Completion Provider

This module contains the base class for all auto-completion providers.
All specialized providers should inherit from this class.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class BaseAutoCompletionProvider(ABC):
    """
    Base class for all auto-completion providers.

    This abstract base class defines the interface that all auto-completion
    providers must implement. It provides common functionality and ensures
    consistent behavior across all providers.
    """

    def __init__(self, name: str, priority: int = 50):
        """
        Initialize the base provider.

        Args:
            name: Unique name for this provider
            priority: Priority for result ranking (0-100, higher is better)
        """
        self.name = name
        self.priority = priority
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.is_enabled = True
        self.last_refresh = datetime.utcnow()

        # Provider-specific configuration
        self.config: Dict[str, Any] = {}

        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "last_used": None
        }

    @abstractmethod
    async def get_completions(self, query: str, context: str = "",
                            context_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get auto-completion suggestions for the given query.

        Args:
            query: The partial input to complete
            context: Additional context information
            context_data: Structured context data

        Returns:
            List of completion suggestions with metadata
        """
        pass

    def is_available(self) -> bool:
        """
        Check if this provider is available for use.

        Returns:
            True if the provider is available, False otherwise
        """
        return self.is_enabled

    def enable(self):
        """Enable this provider."""
        self.is_enabled = True
        self.logger.info(f"Provider {self.name} enabled")

    def disable(self):
        """Disable this provider."""
        self.is_enabled = False
        self.logger.info(f"Provider {self.name} disabled")

    def get_priority(self) -> int:
        """Get the priority of this provider."""
        return self.priority

    def set_priority(self, priority: int):
        """Set the priority of this provider."""
        self.priority = max(0, min(100, priority))
        self.logger.info(f"Provider {self.name} priority set to {self.priority}")

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
        self.logger.debug(f"Provider {self.name} config {key} set to {value}")

    def update_config(self, config: Dict[str, Any]):
        """Update multiple configuration values."""
        self.config.update(config)
        self.logger.info(f"Provider {self.name} config updated")

    def validate_query(self, query: str) -> bool:
        """
        Validate if a query is suitable for this provider.

        Args:
            query: The query to validate

        Returns:
            True if the query is valid for this provider
        """
        if not query or not isinstance(query, str):
            return False

        # Minimum query length check
        min_length = self.get_config("min_query_length", 1)
        if len(query.strip()) < min_length:
            return False

        # Maximum query length check
        max_length = self.get_config("max_query_length", 1000)
        if len(query) > max_length:
            return False

        return True

    def format_completion(self, completion: str, score: float = 0.5,
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format a completion result with standard structure.

        Args:
            completion: The completion text
            score: Relevance score (0.0 to 1.0)
            metadata: Additional metadata

        Returns:
            Formatted completion dictionary
        """
        return {
            "completion": completion,
            "score": max(0.0, min(1.0, score)),
            "provider": self.name,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

    def format_completions(self, completions: List[str],
                          scores: Optional[List[float]] = None,
                          metadata_list: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Format multiple completion results.

        Args:
            completions: List of completion texts
            scores: Optional list of scores
            metadata_list: Optional list of metadata dictionaries

        Returns:
            List of formatted completion dictionaries
        """
        if scores is None:
            scores = [0.5] * len(completions)

        if metadata_list is None:
            metadata_list = [{}] * len(completions)

        formatted = []
        for completion, score, metadata in zip(completions, scores, metadata_list):
            formatted.append(self.format_completion(completion, score, metadata))

        return formatted

    def rank_completions(self, completions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank completions by relevance score.

        Args:
            completions: List of completion dictionaries

        Returns:
            Sorted list of completions by score (descending)
        """
        return sorted(completions, key=lambda x: x.get("score", 0), reverse=True)

    def filter_completions(self, completions: List[Dict[str, Any]],
                          min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Filter completions by minimum score.

        Args:
            completions: List of completion dictionaries
            min_score: Minimum score threshold

        Returns:
            Filtered list of completions
        """
        return [c for c in completions if c.get("score", 0) >= min_score]

    def limit_completions(self, completions: List[Dict[str, Any]],
                         max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Limit the number of completions returned.

        Args:
            completions: List of completion dictionaries
            max_results: Maximum number of results to return

        Returns:
            Limited list of completions
        """
        return completions[:max_results]

    async def refresh(self):
        """
        Refresh provider data or configuration.

        This method should be overridden by subclasses to implement
        provider-specific refresh logic.
        """
        self.last_refresh = datetime.utcnow()
        self.logger.debug(f"Provider {self.name} refreshed")

    async def shutdown(self):
        """
        Shutdown the provider and cleanup resources.

        This method should be overridden by subclasses to implement
        provider-specific shutdown logic.
        """
        self.is_enabled = False
        self.logger.info(f"Provider {self.name} shutdown")

    def get_metrics(self) -> Dict[str, Any]:
        """Get provider performance metrics."""
        return {
            **self.metrics,
            "name": self.name,
            "priority": self.priority,
            "is_enabled": self.is_enabled,
            "last_refresh": self.last_refresh.isoformat(),
            "config": self.config
        }

    def update_metrics(self, success: bool, response_time: float):
        """
        Update provider metrics.

        Args:
            success: Whether the request was successful
            response_time: Time taken to process the request
        """
        self.metrics["total_requests"] += 1
        self.metrics["last_used"] = datetime.utcnow()

        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1

        # Update rolling average response time
        total_requests = self.metrics["total_requests"]
        current_avg = self.metrics["average_response_time"]
        self.metrics["average_response_time"] = (
            (current_avg * (total_requests - 1)) + response_time
        ) / total_requests

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the provider.

        Returns:
            Health check result dictionary
        """
        return {
            "name": self.name,
            "status": "healthy" if self.is_enabled else "disabled",
            "priority": self.priority,
            "metrics": self.get_metrics(),
            "last_refresh": self.last_refresh.isoformat()
        }

    def __str__(self) -> str:
        """String representation of the provider."""
        return f"{self.__class__.__name__}(name={self.name}, priority={self.priority})"

    def __repr__(self) -> str:
        """Detailed string representation of the provider."""
        return f"{self.__class__.__name__}(name={self.name!r}, priority={self.priority!r}, enabled={self.is_enabled!r})"
