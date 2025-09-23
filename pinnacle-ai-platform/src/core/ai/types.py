"""
Shared AI types and enums for the Pinnacle AI Platform.

This module contains common types used across the AI system to avoid circular imports.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class AIStatus(Enum):
    """AI Engine status enumeration."""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class AITask:
    """Represents an AI task with metadata."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    data: Dict[str, Any] = field(default_factory=dict)
    mode: str = "auto"
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    max_retries: int = 3
    retry_count: int = 0
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class AIContext:
    """Context information for AI operations."""
    user_id: Optional[str] = None
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    active_agents: List[str] = field(default_factory=list)
    current_mode: str = "auto"
    preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
