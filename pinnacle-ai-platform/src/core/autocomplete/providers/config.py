"""
Config Auto-Completion Provider

This module provides auto-completion suggestions for configuration files,
environment variables, and system settings.
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import BaseAutoCompletionProvider


class ConfigProvider(BaseAutoCompletionProvider):
    """
    Auto-completion provider for configuration-related suggestions.

    This provider offers completions for:
    - Configuration file names and paths
    - Environment variables
    - Configuration keys and values
    - Settings and parameters
    """

    def __init__(self):
        """Initialize the Config provider."""
        super().__init__("config", priority=50)

        self.set_config("min_query_length", 1)
        self.set_config("max_results", 15)
        self.set_config("include_config_files", True)
        self.set_config("include_env_vars", True)
        self.set_config("include_settings", True)

        # Configuration files
        self._config_files = [
            ".env", ".env.example", "config.json", "config.yaml", "config.yml",
            "settings.json", "settings.yaml", "pyproject.toml", "requirements.txt",
            "Dockerfile", "docker-compose.yml", ".gitignore", ".dockerignore"
        ]

        # Environment variables
        self._env_vars = [
            "DATABASE_URL", "REDIS_URL", "API_KEY", "SECRET_KEY", "DEBUG",
            "LOG_LEVEL", "PORT", "HOST", "ALLOWED_ORIGINS", "DATABASE_NAME",
            "CACHE_TTL", "SESSION_TIMEOUT", "MAX_CONNECTIONS", "WORKERS"
        ]

        # Configuration settings
        self._config_settings = [
            "debug", "host", "port", "database", "cache", "logging",
            "security", "cors", "rate_limit", "timeout", "retries"
        ]

    async def get_completions(self, query: str, context: str = "",
                            context_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get configuration-related auto-completion suggestions."""
        if not self.validate_query(query):
            return []

        start_time = time.time()
        completions = []

        try:
            if self.get_config("include_config_files"):
                completions.extend(await self._get_config_file_completions(query, context))

            if self.get_config("include_env_vars"):
                completions.extend(await self._get_env_var_completions(query, context))

            if self.get_config("include_settings"):
                completions.extend(await self._get_setting_completions(query, context))

            completions = self.filter_completions(completions, min_score=0.1)
            completions = self.rank_completions(completions)
            completions = self.limit_completions(completions, self.get_config("max_results"))

            self.update_metrics(True, time.time() - start_time)
            return completions

        except Exception as e:
            self.logger.error(f"Error getting config completions: {e}")
            self.update_metrics(False, time.time() - start_time)
            return []

    async def _get_config_file_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for configuration files."""
        completions = []

        for config_file in self._config_files:
            if query.lower() in config_file.lower():
                score = self._calculate_similarity(query, config_file)
                completions.append(self.format_completion(
                    config_file,
                    score=score,
                    metadata={
                        "type": "config_file",
                        "category": "configuration",
                        "description": f"Configuration file: {config_file}"
                    }
                ))

        return completions

    async def _get_env_var_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for environment variables."""
        completions = []

        for env_var in self._env_vars:
            if query.upper() in env_var:
                score = self._calculate_similarity(query.upper(), env_var)
                completions.append(self.format_completion(
                    env_var,
                    score=score,
                    metadata={
                        "type": "env_var",
                        "category": "environment",
                        "description": f"Environment variable: {env_var}"
                    }
                ))

        return completions

    async def _get_setting_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for configuration settings."""
        completions = []

        for setting in self._config_settings:
            if query.lower() in setting.lower():
                score = self._calculate_similarity(query, setting)
                completions.append(self.format_completion(
                    setting,
                    score=score,
                    metadata={
                        "type": "config_setting",
                        "category": "configuration",
                        "description": f"Configuration setting: {setting}"
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
        health["config_files_count"] = len(self._config_files)
        health["env_vars_count"] = len(self._env_vars)
        health["settings_count"] = len(self._config_settings)
        return health</code></edit>
</edit_file>