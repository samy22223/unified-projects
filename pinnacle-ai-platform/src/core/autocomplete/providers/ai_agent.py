"""
AI Agent Auto-Completion Provider

This module provides auto-completion suggestions based on AI agent capabilities,
available agents, and AI-related commands and functions.
"""

import re
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import BaseAutoCompletionProvider
from src.core.ai.engine import ai_engine
from src.core.ai.agent_manager import AgentManager


class AIAgentProvider(BaseAutoCompletionProvider):
    """
    Auto-completion provider for AI agent-related suggestions.

    This provider offers completions for:
    - Available AI agents
    - Agent capabilities and specializations
    - AI commands and functions
    - Agent management operations
    - AI modes and configurations
    """

    def __init__(self):
        """Initialize the AI Agent provider."""
        super().__init__("ai_agent", priority=80)  # High priority for AI-related completions

        # AI-specific configuration
        self.set_config("min_query_length", 2)
        self.set_config("max_results", 15)
        self.set_config("include_agent_commands", True)
        self.set_config("include_capabilities", True)
        self.set_config("include_modes", True)
        self.set_config("include_tasks", True)

        # Cache for agent data
        self._agent_cache: Dict[str, Any] = {}
        self._last_cache_update = None
        self._cache_ttl = 300  # 5 minutes

    async def get_completions(self, query: str, context: str = "",
                            context_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get AI agent-related auto-completion suggestions.

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
            # Refresh cache if needed
            await self._refresh_cache_if_needed()

            # Get different types of completions
            if self.get_config("include_agent_commands"):
                completions.extend(await self._get_agent_command_completions(query, context))

            if self.get_config("include_capabilities"):
                completions.extend(await self._get_capability_completions(query, context))

            if self.get_config("include_modes"):
                completions.extend(await self._get_mode_completions(query, context))

            if self.get_config("include_tasks"):
                completions.extend(await self._get_task_completions(query, context))

            # Filter and rank completions
            completions = self.filter_completions(completions, min_score=0.1)
            completions = self.rank_completions(completions)
            completions = self.limit_completions(completions, self.get_config("max_results"))

            # Update metrics
            self.update_metrics(True, time.time() - start_time)

            return completions

        except Exception as e:
            self.logger.error(f"Error getting AI agent completions: {e}")
            self.update_metrics(False, time.time() - start_time)
            return []

    async def _get_agent_command_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for AI agent commands."""
        completions = []

        # Agent management commands
        agent_commands = [
            "agent create",
            "agent list",
            "agent get",
            "agent delete",
            "agent status",
            "agent capabilities",
            "agent tasks",
            "agent performance",
            "agent configure",
            "agent restart",
            "agent pause",
            "agent resume"
        ]

        for command in agent_commands:
            if query.lower() in command.lower():
                score = self._calculate_similarity(query, command)
                completions.append(self.format_completion(
                    command,
                    score=score,
                    metadata={
                        "type": "agent_command",
                        "category": "management",
                        "description": f"AI agent management command: {command}"
                    }
                ))

        return completions

    async def _get_capability_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for AI agent capabilities."""
        completions = []

        # Common AI capabilities
        capabilities = [
            "text_processing",
            "image_analysis",
            "audio_transcription",
            "video_processing",
            "data_analysis",
            "code_generation",
            "content_creation",
            "language_translation",
            "sentiment_analysis",
            "question_answering",
            "summarization",
            "classification",
            "recommendation",
            "chat_interaction",
            "multi_modal_processing"
        ]

        for capability in capabilities:
            if query.lower() in capability.lower():
                score = self._calculate_similarity(query, capability)
                completions.append(self.format_completion(
                    capability,
                    score=score,
                    metadata={
                        "type": "capability",
                        "category": "ai_functionality",
                        "description": f"AI capability: {capability.replace('_', ' ').title()}"
                    }
                ))

        return completions

    async def _get_mode_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for AI modes."""
        completions = []

        # AI modes
        modes = [
            "auto",
            "manual",
            "batch",
            "real_time",
            "interactive",
            "background",
            "priority",
            "standard",
            "advanced",
            "expert",
            "learning",
            "production"
        ]

        for mode in modes:
            if query.lower() in mode.lower():
                score = self._calculate_similarity(query, mode)
                completions.append(self.format_completion(
                    mode,
                    score=score,
                    metadata={
                        "type": "mode",
                        "category": "ai_mode",
                        "description": f"AI processing mode: {mode.replace('_', ' ').title()}"
                    }
                ))

        return completions

    async def _get_task_completions(self, query: str, context: str) -> List[Dict[str, Any]]:
        """Get completions for AI task types."""
        completions = []

        # Task types
        task_types = [
            "text_analysis",
            "image_processing",
            "data_processing",
            "code_review",
            "content_generation",
            "translation",
            "summarization",
            "classification",
            "recommendation",
            "chat_response",
            "question_answering",
            "document_processing",
            "email_handling",
            "report_generation",
            "data_visualization"
        ]

        for task_type in task_types:
            if query.lower() in task_type.lower():
                score = self._calculate_similarity(query, task_type)
                completions.append(self.format_completion(
                    task_type,
                    score=score,
                    metadata={
                        "type": "task_type",
                        "category": "ai_task",
                        "description": f"AI task type: {task_type.replace('_', ' ').title()}"
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
            return 0.9

        # Contains query as substring
        if query_lower in target_lower:
            return 0.7

        # Calculate character overlap
        query_chars = set(query_lower)
        target_chars = set(target_lower)
        overlap = len(query_chars.intersection(target_chars))
        total_chars = len(query_chars.union(target_chars))

        if total_chars > 0:
            char_similarity = overlap / total_chars
            return 0.3 + (char_similarity * 0.4)  # 0.3 to 0.7 range

        return 0.1  # Minimum score

    async def _refresh_cache_if_needed(self):
        """Refresh the agent cache if it's stale."""
        now = datetime.utcnow()
        if (self._last_cache_update is None or
            (now - self._last_cache_update).total_seconds() > self._cache_ttl):

            await self._refresh_cache()
            self._last_cache_update = now

    async def _refresh_cache(self):
        """Refresh the cached agent data."""
        try:
            # Get available agents
            agents = await ai_engine.list_agents()

            # Cache agent information
            self._agent_cache = {
                "agents": agents,
                "agent_names": [agent.get("name", "") for agent in agents],
                "agent_types": list(set(agent.get("type", "") for agent in agents)),
                "agent_capabilities": list(set(
                    capability
                    for agent in agents
                    for capability in agent.get("capabilities", [])
                ))
            }

            self.logger.debug(f"AI agent cache refreshed with {len(agents)} agents")

        except Exception as e:
            self.logger.error(f"Error refreshing AI agent cache: {e}")
            self._agent_cache = {}

    async def refresh(self):
        """Refresh provider data."""
        await self._refresh_cache()
        await super().refresh()

    async def shutdown(self):
        """Shutdown the provider."""
        self._agent_cache.clear()
        await super().shutdown()

    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = super().health_check()

        # Add AI-specific health checks
        try:
            # Check if AI engine is available
            ai_status = ai_engine.health_check()
            health["ai_engine_status"] = "healthy"
        except Exception as e:
            health["ai_engine_status"] = f"unhealthy: {str(e)}"

        health["cached_agents"] = len(self._agent_cache.get("agents", []))
        health["cache_age"] = (
            self._last_cache_update.isoformat()
            if self._last_cache_update else None
        )

        return health
