"""
Dashboard routes for monitoring and control
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime, timedelta
import psutil

router = APIRouter()

class SystemMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_connections: int

class AgentMetrics(BaseModel):
    total_agents: int
    active_agents: int
    tasks_completed: int
    average_response_time: float

class DashboardResponse(BaseModel):
    system_metrics: SystemMetrics
    agent_metrics: AgentMetrics
    recent_activities: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]

@router.get("/", response_model=DashboardResponse)
async def get_dashboard():
    """Get dashboard overview with key metrics"""
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    network_connections = len(psutil.net_connections())
    
    system_metrics = SystemMetrics(
        cpu_percent=cpu_percent,
        memory_percent=memory.percent,
        disk_percent=disk.percent,
        network_connections=network_connections
    )
    
    # Agent metrics (mock data for now)
    agent_metrics = AgentMetrics(
        total_agents=5,
        active_agents=4,
        tasks_completed=2034,
        average_response_time=2.3
    )
    
    # Recent activities
    recent_activities = [
        {
            "id": "1",
            "type": "agent_started",
            "message": "Sales Agent started successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "level": "info"
        },
        {
            "id": "2", 
            "type": "task_completed",
            "message": "Product research task completed",
            "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
            "level": "success"
        },
        {
            "id": "3",
            "type": "alert",
            "message": "High CPU usage detected",
            "timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
            "level": "warning"
        }
    ]
    
    # Alerts
    alerts = [
        {
            "id": "cpu_alert",
            "type": "system",
            "message": "CPU usage above 80%",
            "severity": "warning",
            "timestamp": datetime.utcnow().isoformat()
        }
    ]
    
    return DashboardResponse(
        system_metrics=system_metrics,
        agent_metrics=agent_metrics,
        recent_activities=recent_activities,
        alerts=alerts
    )

@router.get("/metrics/system")
async def get_system_metrics():
    """Get detailed system metrics"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "cpu": {
            "percent": cpu_percent,
            "cores": psutil.cpu_count(),
            "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else None
        },
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent": memory.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "percent": disk.percent
        },
        "network": {
            "connections": len(psutil.net_connections())
        }
    }

@router.get("/metrics/agents")
async def get_agent_metrics():
    """Get detailed agent performance metrics"""
    # TODO: Implement actual agent metrics from orchestrator
    return {
        "total_agents": 5,
        "active_agents": 4,
        "idle_agents": 1,
        "tasks_completed_today": 47,
        "tasks_completed_week": 324,
        "average_task_duration": 45.2,  # seconds
        "success_rate": 0.96,
        "error_rate": 0.04,
        "agents_by_type": {
            "executive": 1,
            "sales": 1,
            "marketing": 1,
            "support": 1,
            "operations": 1
        }
    }

@router.post("/system/restart")
async def restart_system():
    """Restart the entire OmniCore system"""
    # TODO: Implement system restart logic
    return {"message": "System restart initiated"}

@router.post("/agents/restart-all")
async def restart_all_agents():
    """Restart all AI agents"""
    # TODO: Implement agent restart logic
    return {"message": "All agents restart initiated"}
