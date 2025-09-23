"""
AI Agents API Endpoints

This module contains all API endpoints for AI agent management and communication.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

from src.core.ai.engine import ai_engine, AITask, AIContext, TaskPriority
from src.core.database.manager import DatabaseManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class AgentCreateRequest(BaseModel):
    """Request model for creating an agent."""
    name: str = Field(..., description="Agent name")
    type: str = Field(..., description="Agent type")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    max_concurrent_tasks: int = Field(default=3, description="Maximum concurrent tasks")
    specializations: List[str] = Field(default_factory=list, description="Agent specializations")
    model_preferences: Dict[str, Any] = Field(default_factory=dict, description="Model preferences")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Additional settings")


class AgentResponse(BaseModel):
    """Response model for agent information."""
    id: str
    name: str
    type: str
    status: str
    created_at: datetime
    last_active: datetime
    task_count: int
    success_rate: float
    current_tasks: List[str]
    performance_metrics: Dict[str, Any]


class TaskCreateRequest(BaseModel):
    """Request model for creating a task."""
    type: str = Field(..., description="Task type")
    priority: str = Field(default="normal", description="Task priority")
    data: Dict[str, Any] = Field(..., description="Task data")
    mode: str = Field(default="auto", description="Processing mode")
    agent_id: Optional[str] = Field(None, description="Specific agent ID")
    user_id: Optional[str] = Field(None, description="User ID")
    deadline: Optional[datetime] = Field(None, description="Task deadline")
    max_retries: int = Field(default=3, description="Maximum retries")


class TaskResponse(BaseModel):
    """Response model for task information."""
    id: str
    type: str
    priority: str
    status: str
    created_at: datetime
    deadline: Optional[datetime]
    max_retries: int
    retry_count: int
    result: Optional[Any]
    error: Optional[str]
    processing_time: Optional[float]


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    status: str
    ready: bool
    components: Dict[str, bool]
    metrics: Dict[str, Any]


class ModeInfoResponse(BaseModel):
    """Response model for mode information."""
    name: str
    type: str
    description: str
    capabilities: Dict[str, Any]
    enabled: bool
    priority: int


# Dependency to get database manager
async def get_database_manager():
    """Dependency to get database manager instance."""
    return DatabaseManager()


@router.post("/agents", response_model=Dict[str, str])
async def create_agent(request: AgentCreateRequest):
    """
    Create a new AI agent.

    This endpoint allows creating new AI agents with specified capabilities
    and configurations for the Pinnacle AI Platform.
    """
    try:
        logger.info(f"Creating agent: {request.name}")

        # Create agent using the AI engine
        agent_id = await ai_engine.create_agent(request.type, request.dict())

        return {"agent_id": agent_id, "message": "Agent created successfully"}

    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@router.get("/agents", response_model=List[AgentResponse])
async def list_agents(
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    name: Optional[str] = None
):
    """
    List all AI agents with optional filters.

    This endpoint provides a comprehensive view of all agents in the system
    with filtering capabilities.
    """
    try:
        filters = {}
        if agent_type:
            filters["type"] = agent_type
        if status:
            filters["status"] = status
        if name:
            filters["name"] = name

        agents = await ai_engine.list_agents(filters)
        return agents

    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """
    Get detailed information about a specific agent.

    This endpoint provides detailed information about an individual agent
    including its status, performance metrics, and current tasks.
    """
    try:
        agent = await ai_engine.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return agent

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """
    Delete an AI agent.

    This endpoint removes an agent from the system. Only idle agents
    can be deleted to prevent disruption of active tasks.
    """
    try:
        # Check if agent exists and is idle
        agent = await ai_engine.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        if agent.get("status") not in ["idle", "ready"]:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete agent with active tasks"
            )

        # Remove agent from AI engine
        success = await ai_engine.agent_manager.remove_agent(agent_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove agent")

        return {"message": "Agent deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")


@router.post("/tasks", response_model=Dict[str, str])
async def create_task(request: TaskCreateRequest, background_tasks: BackgroundTasks):
    """
    Create a new AI task.

    This endpoint creates a new task for processing by the AI agents.
    Tasks are automatically queued and assigned to appropriate agents.
    """
    try:
        logger.info(f"Creating task: {request.type}")

        # Convert priority string to enum
        priority_map = {
            "critical": TaskPriority.CRITICAL,
            "urgent": TaskPriority.URGENT,
            "high": TaskPriority.HIGH,
            "normal": TaskPriority.NORMAL,
            "low": TaskPriority.LOW
        }

        priority = priority_map.get(request.priority.lower(), TaskPriority.NORMAL)

        # Create AI task
        task = AITask(
            type=request.type,
            priority=priority,
            data=request.data,
            mode=request.mode,
            agent_id=request.agent_id,
            user_id=request.user_id,
            deadline=request.deadline,
            max_retries=request.max_retries
        )

        # Add background task processing
        background_tasks.add_task(process_task_background, task)

        return {"task_id": task.id, "message": "Task created successfully"}

    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


async def process_task_background(task: AITask):
    """Process task in background."""
    try:
        # Create context
        context = AIContext(
            user_id=task.user_id,
            current_mode=task.mode
        )

        # Process task using AI engine
        result = await ai_engine.process_task(task, context)

        logger.info(f"Task {task.id} processed successfully")

    except Exception as e:
        logger.error(f"Error processing task {task.id}: {e}")
        # Update task status to failed
        task.status = "failed"
        task.error = str(e)


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    task_type: Optional[str] = None
):
    """
    List tasks with optional filters.

    This endpoint provides a view of all tasks in the system with
    comprehensive filtering options.
    """
    try:
        filters = {}
        if status:
            filters["status"] = status
        if user_id:
            filters["user_id"] = user_id
        if agent_id:
            filters["agent_id"] = agent_id
        if task_type:
            filters["type"] = task_type

        # Get tasks from database
        db_manager = DatabaseManager()
        tasks = await db_manager.list_tasks(filters)

        return tasks

    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """
    Get detailed information about a specific task.

    This endpoint provides detailed information about a task including
    its status, result, and processing history.
    """
    try:
        # Get task from database
        db_manager = DatabaseManager()
        task = await db_manager.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")


@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    Get overall system status and health information.

    This endpoint provides comprehensive system status including
    component health, performance metrics, and system statistics.
    """
    try:
        # Get status from AI engine
        status = await ai_engine.health_check()

        return SystemStatusResponse(**status)

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


@router.get("/system/metrics")
async def get_system_metrics():
    """
    Get detailed system performance metrics.

    This endpoint provides detailed performance metrics for monitoring
    and analytics purposes.
    """
    try:
        # Get metrics from AI engine
        metrics = await ai_engine.get_performance_metrics()

        # Get additional metrics from database
        db_manager = DatabaseManager()
        stats = await db_manager.get_system_stats()

        return {
            "ai_engine_metrics": metrics,
            "system_stats": stats,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")


@router.get("/modes", response_model=List[ModeInfoResponse])
async def list_modes():
    """
    List all available AI modes.

    This endpoint provides information about all available AI modes
    including their capabilities and configurations.
    """
    try:
        # Get modes from mode manager
        modes = await ai_engine.mode_manager.get_available_modes()

        return [ModeInfoResponse(**mode) for mode in modes]

    except Exception as e:
        logger.error(f"Error listing modes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list modes: {str(e)}")


@router.post("/modes/{mode}/switch")
async def switch_mode(mode: str):
    """
    Switch to a different AI mode.

    This endpoint allows switching the AI engine to a different processing mode.
    """
    try:
        # Create context for mode switch
        context = AIContext(current_mode=mode)

        # Switch mode using mode manager
        success = await ai_engine.switch_mode(mode, context)

        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to switch to mode: {mode}")

        return {"message": f"Switched to {mode} mode successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching mode to {mode}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to switch mode: {str(e)}")


@router.post("/multi-modal/process")
async def process_multi_modal(
    text: Optional[str] = None,
    image_data: Optional[str] = None,  # base64 encoded
    audio_data: Optional[str] = None,  # base64 encoded
    video_data: Optional[str] = None,  # base64 encoded
    modality: str = "text"
):
    """
    Process multi-modal data.

    This endpoint allows processing of different types of data including
    text, images, audio, and video.
    """
    try:
        # Create context
        context = AIContext()

        # Process based on modality
        if modality == "text" and text:
            result = await ai_engine.process_multi_modal(text, "text", context)
        elif modality == "image" and image_data:
            # Convert base64 to appropriate format
            # This would need proper image processing implementation
            result = {"message": "Image processing not yet implemented"}
        elif modality == "audio" and audio_data:
            # Convert base64 to bytes
            # This would need proper audio processing implementation
            result = {"message": "Audio processing not yet implemented"}
        elif modality == "video" and video_data:
            # Convert base64 to bytes
            # This would need proper video processing implementation
            result = {"message": "Video processing not yet implemented"}
        else:
            raise HTTPException(status_code=400, detail="Invalid modality or missing data")

        return {"result": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing multi-modal data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process multi-modal data: {str(e)}")</code></edit>
</edit_file>