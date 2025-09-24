"""
OmniCore AI Platform - Main FastAPI Application
Fully autonomous AI-powered company-in-a-box backend
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import asyncio
from datetime import datetime

# Import our modules
from app.core.config import settings
from app.core.database import init_databases, close_databases
from app.core.logging import setup_logging
from app.routes import agents, dashboard, auth, health
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.monitoring import MonitoringService

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global services
agent_orchestrator = None
monitoring_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global agent_orchestrator, monitoring_service
    
    logger.info("🚀 Starting OmniCore AI Platform...")
    
    # Initialize databases
    await init_databases()
    
    # Initialize services
    agent_orchestrator = AgentOrchestrator()
    monitoring_service = MonitoringService()
    
    # Start background tasks
    await agent_orchestrator.start()
    await monitoring_service.start()
    
    logger.info("✅ OmniCore AI Platform started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down OmniCore AI Platform...")
    
    await agent_orchestrator.stop()
    await monitoring_service.stop()
    await close_databases()
    
    logger.info("✅ OmniCore AI Platform shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="OmniCore AI Platform",
    description="Fully autonomous AI-powered company-in-a-box backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(agents.router, prefix="/agents", tags=["AI Agents"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(health.router, prefix="/health", tags=["Health"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system status"""
    return {
        "message": "Welcome to OmniCore AI Platform",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "agents": len(agent_orchestrator.agents) if agent_orchestrator else 0,
            "monitoring": "active" if monitoring_service else "inactive"
        }
    }

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if monitoring_service:
        return monitoring_service.get_metrics()
    return {"error": "Monitoring service not available"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
