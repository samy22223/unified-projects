"""
Health check endpoints
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import psutil
import asyncio
from app.core.database import mongodb_client, postgres_pool, redis_client, neo4j_driver, chroma_client

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "OmniCore AI Platform"
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with system metrics"""
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database health checks
    db_status = {}
    
    try:
        if mongodb_client:
            await mongodb_client.admin.command('ping')
            db_status["mongodb"] = "healthy"
        else:
            db_status["mongodb"] = "not_initialized"
    except Exception as e:
        db_status["mongodb"] = f"unhealthy: {str(e)}"
    
    try:
        if postgres_pool:
            async with postgres_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_status["postgresql"] = "healthy"
        else:
            db_status["postgresql"] = "not_initialized"
    except Exception as e:
        db_status["postgresql"] = f"unhealthy: {str(e)}"
    
    try:
        if redis_client:
            await redis_client.ping()
            db_status["redis"] = "healthy"
        else:
            db_status["redis"] = "not_initialized"
    except Exception as e:
        db_status["redis"] = f"unhealthy: {str(e)}"
    
    try:
        if neo4j_driver:
            async with neo4j_driver.session() as session:
                await session.run("RETURN 1")
            db_status["neo4j"] = "healthy"
        else:
            db_status["neo4j"] = "not_initialized"
    except Exception as e:
        db_status["neo4j"] = f"unhealthy: {str(e)}"
    
    try:
        if chroma_client:
            chroma_client.heartbeat()
            db_status["chroma"] = "healthy"
        else:
            db_status["chroma"] = "not_initialized"
    except Exception as e:
        db_status["chroma"] = f"unhealthy: {str(e)}"
    
    # Overall health
    all_healthy = all(status == "healthy" for status in db_status.values())
    overall_status = "healthy" if all_healthy else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "OmniCore AI Platform",
        "version": "1.0.0",
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2)
        },
        "databases": db_status,
        "uptime_seconds": psutil.boot_time()
    }

@router.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    # Check if all critical services are ready
    critical_services = ["mongodb", "postgresql", "redis"]
    
    for service in critical_services:
        if service == "mongodb" and mongodb_client:
            try:
                await mongodb_client.admin.command('ping')
            except:
                raise HTTPException(status_code=503, detail=f"{service} not ready")
        elif service == "postgresql" and postgres_pool:
            try:
                async with postgres_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
            except:
                raise HTTPException(status_code=503, detail=f"{service} not ready")
        elif service == "redis" and redis_client:
            try:
                await redis_client.ping()
            except:
                raise HTTPException(status_code=503, detail=f"{service} not ready")
        else:
            raise HTTPException(status_code=503, detail=f"{service} not initialized")
    
    return {"status": "ready"}

@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}
