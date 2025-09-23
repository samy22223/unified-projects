"""
Pinnacle AI Platform API v1

This module contains the main API router for the Pinnacle AI Platform,
including all endpoints for agent management, task processing, and system control.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
import logging

from .agents import router as agents_router
from .ecommerce import ecommerce_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(
    agents_router,
    prefix="/agents",
    tags=["AI Agents"],
    responses={404: {"description": "Not found"}}
)

api_router.include_router(
    ecommerce_router,
    prefix="/ecommerce",
    tags=["E-commerce"],
    responses={404: {"description": "Not found"}}
)

logger = logging.getLogger(__name__)


@api_router.get("/health")
async def api_health_check():
    """
    API health check endpoint.

    This endpoint provides a simple health check for the API layer
    and can be used for load balancer health checks.
    """
    return {
        "status": "healthy",
        "service": "pinnacle-ai-api",
        "version": "1.0.0",
        "timestamp": "2025-01-22T08:54:19.154Z"
    }


@api_router.get("/info")
async def api_info():
    """
    API information endpoint.

    This endpoint provides information about the API including
    available endpoints, versions, and capabilities.
    """
    return {
        "title": "Pinnacle AI Platform API",
        "version": "1.0.0",
        "description": "Advanced AI Assistant Platform with 200+ AI Agents",
        "endpoints": {
            "agents": {
                "create": "POST /api/v1/agents",
                "list": "GET /api/v1/agents",
                "get": "GET /api/v1/agents/{agent_id}",
                "delete": "DELETE /api/v1/agents/{agent_id}"
            },
            "tasks": {
                "create": "POST /api/v1/agents/tasks",
                "list": "GET /api/v1/agents/tasks",
                "get": "GET /api/v1/agents/tasks/{task_id}"
            },
            "system": {
                "status": "GET /api/v1/agents/system/status",
                "metrics": "GET /api/v1/agents/system/metrics"
            },
            "modes": {
                "list": "GET /api/v1/agents/modes",
                "switch": "POST /api/v1/agents/modes/{mode}/switch"
            },
            "ecommerce": {
                "products": {
                    "list": "GET /api/v1/ecommerce/products",
                    "get": "GET /api/v1/ecommerce/products/{product_id}",
                    "create": "POST /api/v1/ecommerce/products",
                    "update": "PUT /api/v1/ecommerce/products/{product_id}",
                    "delete": "DELETE /api/v1/ecommerce/products/{product_id}"
                },
                "cart": {
                    "get": "GET /api/v1/ecommerce/cart/{cart_id}",
                    "create": "POST /api/v1/ecommerce/cart",
                    "add_item": "POST /api/v1/ecommerce/cart/{cart_id}/items",
                    "update_item": "PUT /api/v1/ecommerce/cart/{cart_id}/items/{item_id}",
                    "remove_item": "DELETE /api/v1/ecommerce/cart/{cart_id}/items/{item_id}"
                },
                "orders": {
                    "list": "GET /api/v1/ecommerce/orders",
                    "get": "GET /api/v1/ecommerce/orders/{order_id}",
                    "create": "POST /api/v1/ecommerce/orders"
                },
                "categories": {
                    "list": "GET /api/v1/ecommerce/categories",
                    "get": "GET /api/v1/ecommerce/categories/{category_id}",
                    "create": "POST /api/v1/ecommerce/categories"
                },
                "reviews": {
                    "list": "GET /api/v1/ecommerce/products/{product_id}/reviews",
                    "create": "POST /api/v1/ecommerce/products/{product_id}/reviews"
                },
                "wishlist": {
                    "create": "POST /api/v1/ecommerce/wishlists",
                    "add_item": "POST /api/v1/ecommerce/wishlists/{wishlist_id}/items"
                },
                "analytics": {
                    "sales": "GET /api/v1/ecommerce/analytics/sales",
                    "products": "GET /api/v1/ecommerce/analytics/products"
                }
            }
        },
        "capabilities": [
            "Multi-modal AI processing",
            "200+ concurrent AI agents",
            "Priority-based task scheduling",
            "Real-time agent management",
            "Advanced performance monitoring",
            "Automatic load balancing",
            "Fault tolerance and recovery",
            "Complete e-commerce platform",
            "Product catalog management",
            "Shopping cart and checkout",
            "Order processing and tracking",
            "Customer reviews and ratings",
            "Wishlist management",
            "Inventory management",
            "Sales analytics",
            "Payment processing integration"
        ],
        "supported_modalities": [
            "Text processing and analysis",
            "Image recognition and analysis",
            "Audio transcription and analysis",
            "Video processing and analysis",
            "Multi-modal data fusion"
        ]
    }


@api_router.get("/docs")
async def api_documentation():
    """
    API documentation endpoint.

    This endpoint provides links to API documentation and
    interactive documentation interfaces.
    """
    return {
        "swagger_ui": "/docs",
        "redoc": "/redoc",
        "openapi_json": "/openapi.json",
        "description": "Interactive API documentation available at /docs"
    }


# Error handlers for the API
@api_router.exception_handler(HTTPException)
async def api_http_exception_handler(request, exc):
    """Custom HTTP exception handler for API."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "path": str(request.url),
        "timestamp": "2025-01-22T08:54:19.154Z"
    }


@api_router.exception_handler(Exception)
async def api_general_exception_handler(request, exc):
    """General exception handler for API."""
    logger.error(f"API error: {exc}", exc_info=True)
    return {
        "error": "Internal server error",
        "status_code": 500,
        "path": str(request.url),
        "timestamp": "2025-01-22T08:54:19.154Z"
    }</code></edit>
</edit_file>