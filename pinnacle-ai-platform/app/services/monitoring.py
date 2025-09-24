"""
Monitoring service for metrics collection and health tracking
"""

import time
import logging
from typing import Dict, Any
from prometheus_client import Counter, Gauge, Histogram, generate_latest
import psutil
from app.core.config import settings

logger = logging.getLogger(__name__)

class MonitoringService:
    """Service for collecting and exposing metrics"""
    
    def __init__(self):
        self.running = False
        
        # Prometheus metrics
        self.request_count = Counter(
            'omnicore_requests_total', 
            'Total number of requests', 
            ['method', 'endpoint', 'status']
        )
        
        self.active_agents = Gauge(
            'omnicore_agents_active', 
            'Number of active AI agents'
        )
        
        self.task_completion_time = Histogram(
            'omnicore_task_duration_seconds', 
            'Time spent processing tasks',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )
        
        self.system_cpu_usage = Gauge(
            'omnicore_system_cpu_percent', 
            'System CPU usage percentage'
        )
        
        self.system_memory_usage = Gauge(
            'omnicore_system_memory_percent', 
            'System memory usage percentage'
        )
        
        self.database_connections = Gauge(
            'omnicore_database_connections', 
            'Number of active database connections',
            ['database']
        )
    
    async def start(self):
        """Start the monitoring service"""
        logger.info("🚀 Starting Monitoring Service...")
        self.running = True
        
        # Set initial metrics
        self._update_system_metrics()
        
        logger.info("✅ Monitoring Service started")
    
    async def stop(self):
        """Stop the monitoring service"""
        logger.info("🛑 Stopping Monitoring Service...")
        self.running = False
        logger.info("✅ Monitoring Service stopped")
    
    def _update_system_metrics(self):
        """Update system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.percent)
            
            # Database connections (mock for now)
            self.database_connections.labels(database='postgresql').set(5)
            self.database_connections.labels(database='mongodb').set(3)
            self.database_connections.labels(database='redis').set(2)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def record_request(self, method: str, endpoint: str, status: int):
        """Record an HTTP request"""
        self.request_count.labels(
            method=method, 
            endpoint=endpoint, 
            status=str(status)
        ).inc()
    
    def update_agent_count(self, count: int):
        """Update the number of active agents"""
        self.active_agents.set(count)
    
    def record_task_duration(self, duration: float):
        """Record task completion time"""
        self.task_completion_time.observe(duration)
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        self._update_system_metrics()  # Update before returning
        return generate_latest().decode('utf-8')
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "metrics": {
                "cpu_percent": self.system_cpu_usage._value,
                "memory_percent": self.system_memory_usage._value,
                "active_agents": self.active_agents._value
            }
        }
    
    def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics for dashboard"""
        return {
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory": psutil.virtual_memory()._asdict(),
                "disk": psutil.disk_usage('/')._asdict(),
                "network": {
                    "connections": len(psutil.net_connections())
                }
            },
            "application": {
                "active_agents": self.active_agents._value,
                "total_requests": sum(
                    metric._value 
                    for metric in self.request_count._metrics.values()
                ),
                "uptime_seconds": time.time() - psutil.boot_time()
            },
            "databases": {
                "postgresql_connections": 5,  # Mock
                "mongodb_connections": 3,     # Mock
                "redis_connections": 2        # Mock
            }
        }
