"""
Search Auto-Completion Provider

This module provides auto-completion suggestions for search queries,
filtering options, and search-related commands.
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import BaseAutoCompletionProvider


class SearchProvider(BaseAutoCompletionProvider):
    """
    Auto-completion provider for search-related suggestions.

    This provider offers completions for:
    - Search keywords and terms
    - Filter operators and syntax
    - Search commands and options
    - Sorting and pagination parameters
    """

    def __init__(self):
        """Initialize the Search provider."""
        super().__init__("search", priority=45)

        self.set_config("min_query_length", 1)
        self.set_config("max_results", 15)
        self.set_config("include_search_terms", True)
        self.set_config("include_filters", True)
        self.set_config("include_operators", True)

        # Search terms
        self._search_terms = [
            "search", "find", "query", "filter", "sort", "order",
            "limit", "offset", "page", "results", "match", "contains"
        ]

        # Filter operators
        self._filter_operators = [
            "AND", "OR", "NOT", "IN", "NOT IN", "LIKE", "ILIKE",
            "BETWEEN", "IS NULL", "IS NOT NULL", "EXISTS", "ANY", "ALL"
        ]

        # Search commands
        self._search_commands = [
            "search products", "search agents", "search tasks", "search users",
            "search logs", "search files", "search documentation", "search config"
        ]

    async def get_completions(self, query: str, context: str = "",
                            context_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get search-related auto-completion suggestions."""
        if not self.validate_query(query):
            return []

        start_time = time.time()
        completions = []

        try:
            if self.get_config("include_search_terms"):
                completions.extend(await self._get_search_term_completions(query, context))

            if self.get_config("include_filters"):
                completions.extend(await self._get_filter_completions(query, context))

            if self.get_config("include_operators"):
                completions.extend(await self._get_operator_completions(query, context))

            completions = self.filter_completions(completions, min_score=0.1)
            completions = self.rank_completions(completions)
            completions = self.limit_completions(completions, self.get_config("max_results"))

            self.update_metrics(True, time.time() - start_time)
            return completions

        except Exception as e:
            self.logger.error(f"Error getting search completions: {e}")
            self.update_metrics(False, time.time() - start_time)
            return []

    async def _get_search_term_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for search terms."""
        completions = []

        for term in self._search_terms:
            if query.lower() in term.lower():
                score = self._calculate_similarity(query, term)
                completions.append(self.format_completion(
                    term,
                    score=score,
                    metadata={
                        "type": "search_term",
                        "category": "search",
                        "description": f"Search term: {term}"
                    }
                ))

        return completions

    async def _get_filter_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for filter operators."""
        completions = []

        for operator in self._filter_operators:
            if query.upper() in operator:
                score = self._calculate_similarity(query.upper(), operator)
                completions.append(self.format_completion(
                    operator,
                    score=score,
                    metadata={
                        "type": "filter_operator",
                        "category": "search_filter",
                        "description": f"Filter operator: {operator}"
                    }
                ))

        return completions

    async def _get_operator_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for search commands."""
        completions = []

        for command in self._search_commands:
            if query.lower() in command.lower():
                score = self._calculate_similarity(query, command)
                completions.append(self.format_completion(
                    command,
                    score=score,
                    metadata={
                        "type": "search_command",
                        "category": "search_operation",
                        "description": f"Search command: {command}"
                    }
                ))

        return completions

    def _calculate_similarity(self, query: str, target: str) -> float:
        """Calculate similarity score between query and target string."""
        if not query or not target:
            return 0.0

        query_lower = query.lower()
        target_lower = target.lower()

        if target_lower.startswith(query_lower):
            return 0.9

        if query_lower in target_lower:
            return 0.7

        query_chars = set(query_lower)
        target_chars = set(target_lower)
        overlap = len(query_chars.intersection(target_chars))
        total_chars = len(query_chars.union(target_chars))

        if total_chars > 0:
            char_similarity = overlap / total_chars
            return 0.2 + (char_similarity * 0.3)

        return 0.1

    async def refresh(self):
        """Refresh provider data."""
        await super().refresh()

    async def shutdown(self):
        """Shutdown the provider."""
        await super().shutdown()

    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = super().health_check()
        health["search_terms_count"] = len(self._search_terms)
        health["filter_operators_count"] = len(self._filter_operators)
        health["search_commands_count"] = len(self._search_commands)
        return health</code></edit>
</edit_file>