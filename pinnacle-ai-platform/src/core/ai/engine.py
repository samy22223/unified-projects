"""
Pinnacle AI Engine - Core AI Assistant Framework

This module contains the main AI engine that orchestrates all AI operations,
manages agents, and provides the foundation for all Pinnacle modes.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from src.core.config.settings import settings
from src.core.ai.types import AIStatus, TaskPriority, AITask, AIContext
from src.core.ai.modes import ModeManager
from src.core.ai.agent_manager import AgentManager
from src.core.ai.multi_modal import MultiModalProcessor
from src.core.ai.task_queue import TaskQueueManager
from src.core.database import DatabaseManager


class PinnacleAIEngine:
    """
    Main AI Engine for the Pinnacle AI Platform.

    This class orchestrates all AI operations, manages agents, and provides
    the foundation for multi-modal AI processing and mode switching.
    """

    def __init__(self):
        """Initialize the AI engine."""
        self.logger = logging.getLogger(__name__)
        self.status = AIStatus.INITIALIZING

        # Core components
        self.mode_manager = None
        self.agent_manager = None
        self.multi_modal_processor = None
        self.task_queue_manager = None
        self.database_manager = None

        # Engine state
        self.active_tasks: Dict[str, AITask] = {}
        self.active_contexts: Dict[str, AIContext] = {}
        self.performance_metrics: Dict[str, Any] = {}

        # Configuration
        self.max_concurrent_tasks = settings.MAX_CONCURRENT_REQUESTS
        self.task_timeout = settings.REQUEST_TIMEOUT
        self.agent_timeout = settings.AGENT_TIMEOUT

        # Statistics
        self.stats = {
            "tasks_processed": 0,
            "agents_created": 0,
            "errors": 0,
            "uptime": 0
        }

        self.start_time = time.time()

    async def initialize(self) -> bool:
        """
        Initialize the AI engine and all its components.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("🚀 Initializing Pinnacle AI Engine...")

            # Initialize database manager
            self.database_manager = DatabaseManager()
            await self.database_manager.initialize()

            # Initialize mode manager
            self.mode_manager = ModeManager(self)
            await self.mode_manager.initialize()

            # Initialize agent manager
            self.agent_manager = AgentManager(self)
            await self.agent_manager.initialize()

            # Initialize multi-modal processor
            self.multi_modal_processor = MultiModalProcessor(self)
            await self.multi_modal_processor.initialize()

            # Initialize task queue manager
            self.task_queue_manager = TaskQueueManager(self)
            await self.task_queue_manager.initialize()

            self.status = AIStatus.READY
            self.logger.info("✅ Pinnacle AI Engine initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize AI engine: {e}")
            self.status = AIStatus.ERROR
            return False

    async def shutdown(self):
        """Shutdown the AI engine and clean up resources."""
        self.logger.info("🛑 Shutting down Pinnacle AI Engine...")

        self.status = AIStatus.SHUTDOWN

        # Shutdown components in reverse order
        if self.task_queue_manager:
            await self.task_queue_manager.shutdown()

        if self.multi_modal_processor:
            await self.multi_modal_processor.shutdown()

        if self.agent_manager:
            await self.agent_manager.shutdown()

        if self.mode_manager:
            await self.mode_manager.shutdown()

        if self.database_manager:
            await self.database_manager.shutdown()

        self.logger.info("✅ Pinnacle AI Engine shutdown complete")

    async def process_task(self, task: AITask, context: Optional[AIContext] = None) -> Any:
        """
        Process an AI task using the appropriate mode and agents.

        Args:
            task: The AI task to process
            context: Optional context for the task

        Returns:
            The result of task processing
        """
        if self.status != AIStatus.READY:
            raise RuntimeError(f"AI Engine is not ready (status: {self.status})")

        task_id = task.id
        self.active_tasks[task_id] = task

        try:
            # Update statistics
            self.stats["tasks_processed"] += 1

            # Create context if not provided
            if not context:
                context = AIContext()

            # Determine the appropriate mode
            mode = await self.mode_manager.select_mode(task, context)

            # Route task to appropriate mode
            result = await self.mode_manager.process_with_mode(task, context, mode)

            # Update task status
            task.status = "completed"
            task.result = result

            return result

        except Exception as e:
            self.logger.error(f"Error processing task {task_id}: {e}")
            self.stats["errors"] += 1

            task.status = "failed"
            task.error = str(e)

            raise
        finally:
            # Clean up active task
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

    async def create_agent(self, agent_type: str, config: Dict[str, Any]) -> str:
        """
        Create a new AI agent.

        Args:
            agent_type: Type of agent to create
            config: Agent configuration

        Returns:
            Agent ID
        """
        if not self.agent_manager:
            raise RuntimeError("Agent manager not initialized")

        agent_id = await self.agent_manager.create_agent(agent_type, config)
        self.stats["agents_created"] += 1

        return agent_id

    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent information by ID.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent information or None if not found
        """
        if not self.agent_manager:
            return None

        return await self.agent_manager.get_agent(agent_id)

    async def list_agents(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List all agents with optional filters.

        Args:
            filters: Optional filters to apply

        Returns:
            List of agent information
        """
        if not self.agent_manager:
            return []

        return await self.agent_manager.list_agents(filters)

    async def process_multi_modal(self, data: Any, modality: str, context: AIContext) -> Any:
        """
        Process multi-modal data (text, image, audio, video).

        Args:
            data: The data to process
            modality: Type of data (text, image, audio, video)
            context: Processing context

        Returns:
            Processed result
        """
        if not self.multi_modal_processor:
            raise RuntimeError("Multi-modal processor not initialized")

        return await self.multi_modal_processor.process(data, modality, context)

    async def switch_mode(self, mode: str, context: AIContext) -> bool:
        """
        Switch to a different AI mode.

        Args:
            mode: Mode to switch to
            context: Current context

        Returns:
            True if switch successful
        """
        if not self.mode_manager:
            return False

        return await self.mode_manager.switch_mode(mode, context)

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.

        Returns:
            Dictionary of performance metrics
        """
        uptime = time.time() - self.start_time

        return {
            "status": self.status.value,
            "uptime_seconds": uptime,
            "active_tasks": len(self.active_tasks),
            "active_contexts": len(self.active_contexts),
            "total_tasks_processed": self.stats["tasks_processed"],
            "total_agents_created": self.stats["agents_created"],
            "total_errors": self.stats["errors"],
            "memory_usage": self._get_memory_usage(),
            "cpu_usage": self._get_cpu_usage()
        }

    def _get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent()
            }
        except ImportError:
            return {"error": "psutil not available"}

    def _get_cpu_usage(self) -> Dict[str, float]:
        """Get current CPU usage statistics."""
        try:
            import psutil
            process = psutil.Process()
            return {
                "percent": process.cpu_percent(),
                "num_cores": psutil.cpu_count()
            }
        except ImportError:
            return {"error": "psutil not available"}

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the AI engine.

        Returns:
            Health status information
        """
        return {
            "status": self.status.value,
            "ready": self.status == AIStatus.READY,
            "components": {
                "mode_manager": self.mode_manager is not None,
                "agent_manager": self.agent_manager is not None,
                "multi_modal_processor": self.multi_modal_processor is not None,
                "task_queue_manager": self.task_queue_manager is not None,
                "database_manager": self.database_manager is not None
            },
            "metrics": await self.get_performance_metrics()
        }


# Global AI engine instance
ai_engine = PinnacleAIEngine()