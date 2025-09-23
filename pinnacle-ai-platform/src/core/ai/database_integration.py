"""
Pinnacle AI Database Integration

This module provides database integration for the AI system components,
enabling persistent storage of agents, tasks, and contexts.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from src.core.database.manager import DatabaseManager
from src.core.ai.types import AITask, AIContext, TaskPriority


class AIDatabaseManager:
    """
    Database integration layer for the AI system.

    Provides high-level database operations specifically for AI components
    including agents, tasks, contexts, and performance metrics.
    """

    def __init__(self):
        """Initialize the AI database manager."""
        self.logger = logging.getLogger(__name__)
        self.db_manager = DatabaseManager()

    async def initialize(self) -> bool:
        """Initialize the database connection."""
        try:
            await self.db_manager.initialize()
            self.logger.info("✅ AI Database Manager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize AI Database Manager: {e}")
            return False

    async def shutdown(self):
        """Shutdown database connections."""
        await self.db_manager.shutdown()

    @asynccontextmanager
    async def get_session(self):
        """Get database session context manager."""
        async with self.db_manager.get_session() as session:
            yield session

    # Agent operations
    async def create_agent(self, agent_data: Dict[str, Any]) -> str:
        """Create a new agent in the database."""
        return await self.db_manager.create_agent(agent_data)

    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID."""
        return await self.db_manager.get_agent(agent_id)

    async def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update agent information."""
        return await self.db_manager.update_agent(agent_id, updates)

    async def list_agents(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List agents with optional filters."""
        return await self.db_manager.list_agents(filters)

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        return await self.db_manager.delete_agent(agent_id)

    # Task operations
    async def create_task(self, task: AITask) -> str:
        """Create a new task in the database."""
        task_data = {
            "id": task.id,
            "type": task.type,
            "priority": task.priority.value,
            "data": task.data,
            "mode": task.mode,
            "agent_id": task.agent_id,
            "user_id": task.user_id,
            "created_at": task.created_at,
            "deadline": task.deadline,
            "max_retries": task.max_retries,
            "retry_count": task.retry_count,
            "status": task.status,
            "result": task.result,
            "error": task.error,
            "processing_time": task.processing_time
        }
        return await self.db_manager.create_task(task_data)

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID."""
        return await self.db_manager.get_task(task_id)

    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update task information."""
        return await self.db_manager.update_task(task_id, updates)

    async def list_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List tasks with optional filters."""
        return await self.db_manager.list_tasks(filters)

    async def mark_task_completed(self, task_id: str, result: Any, processing_time: float) -> bool:
        """Mark a task as completed with result and processing time."""
        updates = {
            "status": "completed",
            "result": result,
            "processing_time": processing_time,
            "completed_at": datetime.utcnow()
        }
        return await self.db_manager.update_task(task_id, updates)

    async def mark_task_failed(self, task_id: str, error: str, retry_count: int) -> bool:
        """Mark a task as failed with error information."""
        updates = {
            "status": "failed",
            "error": error,
            "retry_count": retry_count
        }
        return await self.db_manager.update_task(task_id, updates)

    # Context operations
    async def save_context(self, context: AIContext) -> str:
        """Save AI context to database."""
        # For now, we'll store context as part of task data
        # In a more advanced implementation, we might have a separate context table
        return context.session_id

    async def get_context(self, session_id: str) -> Optional[AIContext]:
        """Retrieve AI context from database."""
        # For now, return a new context
        # In a more advanced implementation, we would retrieve from database
        return AIContext(session_id=session_id)

    # Performance metrics
    async def store_performance_metric(self, metric_type: str, value: float, metadata: Optional[Dict[str, Any]] = None):
        """Store a performance metric."""
        await self.db_manager.store_metric(metric_type, value, metadata)

    async def get_performance_metrics(self, metric_type: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance metrics for a specific type."""
        return await self.db_manager.get_metrics(metric_type, hours)

    # Analytics
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        return await self.db_manager.get_system_stats()

    async def cleanup_old_data(self, days: int = 30):
        """Clean up old data to prevent database bloat."""
        await self.db_manager.cleanup_old_data(days)


# Global AI database manager instance
ai_db_manager = AIDatabaseManager()