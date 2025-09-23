"""
API Endpoint Auto-Completion Provider

This module provides auto-completion suggestions for API endpoints,
HTTP methods, parameters, and API-related commands.
"""

import re
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import BaseAutoCompletionProvider


class APIEndpointProvider(BaseAutoCompletionProvider):
    """
    Auto-completion provider for API endpoint-related suggestions.

    This provider offers completions for:
    - HTTP methods (GET, POST, PUT, DELETE, etc.)
    - API endpoints and routes
    - API parameters and query strings
    - API authentication methods
    - API testing commands
    - API documentation references
    """

    def __init__(self):
        """Initialize the API Endpoint provider."""
        super().__init__("api_endpoint", priority=70)

        # API-specific configuration
        self.set_config("min_query_length", 1)
        self.set_config("max_results", 20)
        self.set_config("include_http_methods", True)
        self.set_config("include_endpoints", True)
        self.set_config("include_parameters", True)
        self.set_config("include_auth_methods", True)

        # Common API endpoints (can be expanded based on actual API)
        self._common_endpoints = {
            "GET": [
                "/api/v1/agents",
                "/api/v1/agents/{id}",
                "/api/v1/tasks",
                "/api/v1/tasks/{id}",
                "/api/v1/system/status",
                "/api/v1/system/metrics",
                "/api/v1/modes",
                "/api/v1/health",
                "/api/v1/info",
                "/api/v1/docs",
                "/api/v1/ecommerce/products",
                "/api/v1/ecommerce/categories",
                "/api/v1/ecommerce/orders",
                "/api/v1/ecommerce/cart"
            ],
            "POST": [
                "/api/v1/agents",
                "/api/v1/tasks",
                "/api/v1/agents/{id}/tasks",
                "/api/v1/ecommerce/products",
                "/api/v1/ecommerce/orders",
                "/api/v1/ecommerce/cart"
            ],
            "PUT": [
                "/api/v1/agents/{id}",
                "/api/v1/tasks/{id}",
                "/api/v1/ecommerce/products/{id}",
                "/api/v1/ecommerce/cart/{id}"
            ],
            "DELETE": [
                "/api/v1/agents/{id}",
                "/api/v1/tasks/{id}",
                "/api/v1/ecommerce/products/{id}",
                "/api/v1/ecommerce/cart/{id}/items/{item_id}"
            ]
        }

        # Common API parameters
        self._common_parameters = [
            "limit", "offset", "page", "size", "sort", "order",
            "filter", "search", "query", "id", "name", "type",
            "status", "created_at", "updated_at", "user_id",
            "agent_id", "task_id", "product_id", "category_id"
        ]

        # HTTP methods
        self._http_methods = [
            "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"
        ]

        # Authentication methods
        self._auth_methods = [
            "Bearer", "Basic", "API-Key", "OAuth", "JWT", "None"
        ]

    async def get_completions(self, query: str, context: str = "",
                            context_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get API endpoint-related auto-completion suggestions.

        Args:
            query: The partial input to complete
            context: Additional context information
            context_data: Structured context data

        Returns:
            List of completion suggestions
        """
        if not self.validate_query(query):
            return []

        start_time = time.time()
        completions = []

        try:
            # Get different types of completions
            if self.get_config("include_http_methods"):
                completions.extend(await self._get_http_method_completions(query, context))

            if self.get_config("include_endpoints"):
                completions.extend(await self._get_endpoint_completions(query, context))

            if self.get_config("include_parameters"):
                completions.extend(await self._get_parameter_completions(query, context))

            if self.get_config("include_auth_methods"):
                completions.extend(await self._get_auth_completions(query, context))

            # Filter and rank completions
            completions = self.filter_completions(completions, min_score=0.1)
            completions = self.rank_completions(completions)
            completions = self.limit_completions(completions, self.get_config("max_results"))

            # Update metrics
            self.update_metrics(True, time.time() - start_time)

            return completions

        except Exception as e:
            self.logger.error(f"Error getting API endpoint completions: {e}")
            self.update_metrics(False, time.time() - start_time)
            return []

    async def _get_http_method_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for HTTP methods."""
        completions = []

        for method in self._http_methods:
            if query.upper() in method:
                score = self._calculate_similarity(query.upper(), method)
                completions.append(self.format_completion(
                    method,
                    score=score,
                    metadata={
                        "type": "http_method",
                        "category": "api_method",
                        "description": f"HTTP method: {method}"
                    }
                ))

        return completions

    async def _get_endpoint_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for API endpoints."""
        completions = []

        # Check if query starts with HTTP method
        method_match = None
        query_upper = query.upper()

        for method in self._http_methods:
            if query_upper.startswith(method + " "):
                method_match = method
                endpoint_query = query[len(method) + 1:].strip()
                break

        # If no method specified, suggest endpoints for all methods
        methods_to_check = [method_match] if method_match else self._http_methods

        for method in methods_to_check:
            if method in self._common_endpoints:
                for endpoint in self._common_endpoints[method]:
                    # Check if endpoint matches the query
                    if endpoint_query:
                        if endpoint_query.lower() in endpoint.lower():
                            score = self._calculate_similarity(endpoint_query, endpoint)
                            full_completion = f"{method} {endpoint}"
                            completions.append(self.format_completion(
                                full_completion,
                                score=score,
                                metadata={
                                    "type": "api_endpoint",
                                    "category": "endpoint",
                                    "method": method,
                                    "endpoint": endpoint,
                                    "description": f"API endpoint: {method} {endpoint}"
                                }
                            ))
                    else:
                        # Suggest method + endpoint combinations
                        score = 0.6  # Base score for method + endpoint
                        completions.append(self.format_completion(
                            f"{method} {endpoint}",
                            score=score,
                            metadata={
                                "type": "api_endpoint",
                                "category": "endpoint",
                                "method": method,
                                "endpoint": endpoint,
                                "description": f"API endpoint: {method} {endpoint}"
                            }
                        ))

        return completions

    async def _get_parameter_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for API parameters."""
        completions = []

        # Check if query contains parameter patterns
        param_patterns = [
            (r'(\w+)=', 'parameter_assignment'),
            (r'\?(\w+)', 'query_parameter'),
            (r'&(\w+)', 'query_parameter'),
            (r'params\[["\']?(\w+)', 'parameter_key')
        ]

        for pattern, param_type in param_patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                for param in self._common_parameters:
                    if match.lower() in param.lower():
                        score = self._calculate_similarity(match, param)
                        if param_type == 'parameter_assignment':
                            completion = f"{param}="
                            description = f"Parameter assignment: {param}="
                        elif param_type == 'query_parameter':
                            completion = f"{param}="
                            description = f"Query parameter: {param}="
                        else:
                            completion = param
                            description = f"Parameter: {param}"

                        completions.append(self.format_completion(
                            completion,
                            score=score,
                            metadata={
                                "type": "api_parameter",
                                "category": "parameter",
                                "parameter_type": param_type,
                                "description": description
                            }
                        ))

        # Also suggest parameters directly if query looks like a parameter
        if not matches and any(char in query for char in "?&= "):
            for param in self._common_parameters:
                if query.lower() in param.lower():
                    score = self._calculate_similarity(query, param)
                    completions.append(self.format_completion(
                        param,
                        score=score,
                        metadata={
                            "type": "api_parameter",
                            "category": "parameter",
                            "description": f"API parameter: {param}"
                        }
                    ))

        return completions

    async def _get_auth_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for authentication methods."""
        completions = []

        # Check for auth-related keywords
        auth_keywords = ["auth", "authorization", "bearer", "token", "api", "key", "jwt", "oauth"]

        if any(keyword in query.lower() for keyword in auth_keywords):
            for auth_method in self._auth_methods:
                if query.lower() in auth_method.lower():
                    score = self._calculate_similarity(query, auth_method)
                    completions.append(self.format_completion(
                        auth_method,
                        score=score,
                        metadata={
                            "type": "auth_method",
                            "category": "authentication",
                            "description": f"Authentication method: {auth_method}"
                        }
                    ))

        return completions

    def _calculate_similarity(self, query: str, target: str) -> float:
        """
        Calculate similarity score between query and target string.

        Args:
            query: The search query
            target: The target string to compare against

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not query or not target:
            return 0.0

        query_lower = query.lower()
        target_lower = target.lower()

        # Exact prefix match gets highest score
        if target_lower.startswith(query_lower):
            return 0.95

        # Contains query as substring
        if query_lower in target_lower:
            return 0.8

        # Word boundary matches
        query_words = set(query_lower.split())
        target_words = set(target_lower.split())
        if query_words.intersection(target_words):
            return 0.7

        # Character overlap for partial matches
        query_chars = set(query_lower)
        target_chars = set(target_lower)
        overlap = len(query_chars.intersection(target_chars))
        total_chars = len(query_chars.union(target_chars))

        if total_chars > 0:
            char_similarity = overlap / total_chars
            return 0.2 + (char_similarity * 0.3)  # 0.2 to 0.5 range

        return 0.1  # Minimum score

    async def refresh(self):
        """Refresh provider data."""
        # Could refresh endpoints from API documentation or live API
        await super().refresh()

    async def shutdown(self):
        """Shutdown the provider."""
        await super().shutdown()

    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = super().health_check()

        # Add API-specific health information
        health["endpoints_count"] = sum(len(endpoints) for endpoints in self._common_endpoints.values())
        health["parameters_count"] = len(self._common_parameters)
        health["http_methods_count"] = len(self._http_methods)
        health["auth_methods_count"] = len(self._auth_methods)

        return health</code></edit>
</edit_file>