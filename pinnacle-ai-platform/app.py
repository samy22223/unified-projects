"""
Pinnacle AI Platform - Main FastAPI Application

This is the main entry point for the Pinnacle AI Platform FastAPI application.
It includes all the core functionality, middleware, and API routes.

Usage:
    uvicorn app:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import time
import logging
from contextlib import asynccontextmanager

from src.core.config import settings
from src.api.v1.api import api_router
from src.core.database import init_db, close_db
from src.core.logging import setup_logging

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting Pinnacle AI Platform...")
    await init_db()
    logger.info("✅ Database initialized")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Pinnacle AI Platform...")
    await close_db()
    logger.info("✅ Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url=settings.API_DOCS_URL,
    redoc_url=settings.API_REDOC_URL,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "service": "pinnacle-ai-platform",
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Welcome to Pinnacle AI Platform",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


# API versioning info
@app.get("/api", tags=["API"])
async def api_info():
    """API information and available versions."""
    return {
        "title": settings.API_TITLE,
        "description": settings.API_DESCRIPTION,
        "version": settings.API_VERSION,
        "available_versions": ["v1"],
        "base_url": "/api/v1"
    }


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description=settings.API_DESCRIPTION,
        routes=app.routes,
    )

    # Add custom servers
    openapi_schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://api.pinnacle-ai.com", "description": "Production server"},
    ]

    # Add custom tags
    openapi_schema["tags"] = [
        {"name": "AI Agents", "description": "AI agent management and operations"},
        {"name": "E-commerce", "description": "E-commerce functionality and store management"},
        {"name": "Dropshipping", "description": "Dropshipping automation and fulfillment"},
        {"name": "Integrations", "description": "Third-party integrations and APIs"},
        {"name": "Analytics", "description": "Analytics and reporting"},
        {"name": "Health", "description": "Health checks and monitoring"},
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "type": "http_exception",
            "path": str(request.url),
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "type": "internal_error",
            "path": str(request.url),
            "timestamp": time.time()
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )