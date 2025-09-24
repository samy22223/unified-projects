#!/usr/bin/env python3
"""
Payment Analytics Service
FastAPI service providing comprehensive payment analytics and reporting
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from payment_analytics import analytics_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Payment Analytics Service",
    description="Comprehensive payment analytics and business intelligence dashboard",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize analytics service"""
    logger.info("Starting payment analytics service...")

@app.get("/dashboard/{platform}", response_model=Dict[str, Any])
async def get_payment_dashboard(
    platform: str,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    api_key: str = Depends(get_api_key)
):
    """
    Get comprehensive payment dashboard for a specific platform

    Returns summary metrics, trends, breakdowns, forecasts, and alerts
    for the specified time period.
    """
    try:
        dashboard = await analytics_engine.get_payment_dashboard(platform, days)
        return dashboard

    except Exception as e:
        logger.error(f"Failed to get dashboard for {platform}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")

@app.get("/dashboard", response_model=Dict[str, Any])
async def get_global_dashboard(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    api_key: str = Depends(get_api_key)
):
    """
    Get global payment dashboard across all platforms

    Aggregates data from all platforms for unified business intelligence.
    """
    try:
        dashboard = await analytics_engine.get_payment_dashboard(None, days)
        return dashboard

    except Exception as e:
        logger.error(f"Failed to get global dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve global dashboard")

@app.get("/metrics/{platform}/summary", response_model=Dict[str, Any])
async def get_payment_summary(
    platform: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    api_key: str = Depends(get_api_key)
):
    """
    Get payment summary metrics for a platform

    Returns key performance indicators and summary statistics.
    """
    try:
        if start_date and end_date:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.utcnow()
            start = end - timedelta(days=30)

        summary = await analytics_engine._get_payment_summary(platform, start, end)

        return {
            'platform': platform,
            'period': {
                'start': start.isoformat(),
                'end': end.isoformat()
            },
            'summary': summary
        }

    except Exception as e:
        logger.error(f"Failed to get summary for {platform}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve summary")

@app.get("/metrics/{platform}/trends", response_model=Dict[str, Any])
async def get_payment_trends(
    platform: str,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    api_key: str = Depends(get_api_key)
):
    """
    Get payment trends and time-series data

    Returns daily revenue, transaction counts, and trend analysis.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        trends = await analytics_engine._get_payment_trends(platform, start_date, end_date)

        return {
            'platform': platform,
            'period_days': days,
            'trends': trends
        }

    except Exception as e:
        logger.error(f"Failed to get trends for {platform}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trends")

@app.get("/metrics/{platform}/forecast", response_model=Dict[str, Any])
async def get_revenue_forecast(
    platform: str,
    days: int = Query(30, description="Forecast period in days", ge=1, le=365),
    api_key: str = Depends(get_api_key)
):
    """
    Get revenue forecast based on historical data

    Uses time-series analysis to predict future revenue trends.
    """
    try:
        forecast = await analytics_engine._get_revenue_forecast(platform, days)

        return {
            'platform': platform,
            'forecast': forecast
        }

    except Exception as e:
        logger.error(f"Failed to get forecast for {platform}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate forecast")

@app.get("/alerts/{platform}", response_model=List[Dict[str, Any]])
async def get_payment_alerts(
    platform: str,
    api_key: str = Depends(get_api_key)
):
    """
    Get active payment alerts and warnings

    Returns current alerts that require attention.
    """
    try:
        alerts = await analytics_engine._get_payment_alerts(platform)

        return alerts

    except Exception as e:
        logger.error(f"Failed to get alerts for {platform}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")

@app.get("/breakdown/{platform}", response_model=Dict[str, Any])
async def get_payment_breakdown(
    platform: str,
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    api_key: str = Depends(get_api_key)
):
    """
    Get detailed payment breakdown by categories

    Returns breakdowns by payment method, geography, amount ranges, etc.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        breakdown = await analytics_engine._get_payment_breakdown(platform, start_date, end_date)

        return {
            'platform': platform,
            'period_days': days,
            'breakdown': breakdown
        }

    except Exception as e:
        logger.error(f"Failed to get breakdown for {platform}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve breakdown")

@app.post("/reports/{platform}/export", response_model=Dict[str, Any])
async def export_analytics_report(
    platform: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    format: str = Query("json", description="Export format (json/csv/pdf)"),
    api_key: str = Depends(get_api_key)
):
    """
    Export comprehensive analytics report

    Generates detailed business intelligence reports for download.
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        report = await analytics_engine.export_analytics_report(platform, start, end, format)

        return report

    except Exception as e:
        logger.error(f"Failed to export report for {platform}: {e}")
        raise HTTPException(status_code=500, detail="Failed to export report")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connectivity
        import redis
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        redis_client.ping()

        return {
            "status": "healthy",
            "service": "payment-analytics",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "redis": "connected",
                "analytics_engine": "active"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "payment-analytics",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@app.get("/platforms")
async def get_available_platforms(api_key: str = Depends(get_api_key)):
    """
    Get list of available platforms for analytics

    Returns all platforms that have payment data available.
    """
    try:
        # In production, this would scan Redis for available platforms
        platforms = [
            {
                'id': 'pinnacle_ai',
                'name': 'Pinnacle AI Platform',
                'description': 'AI service subscriptions and payments'
            },
            {
                'id': 'free_ecommerce',
                'name': 'Free E-commerce Store',
                'description': 'Dropshipping store payments'
            }
        ]

        return {
            'platforms': platforms,
            'total': len(platforms)
        }

    except Exception as e:
        logger.error(f"Failed to get platforms: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve platforms")

# Custom metrics endpoints
@app.get("/metrics/revenue-comparison")
async def compare_platform_revenue(
    days: int = Query(30, description="Number of days to compare", ge=1, le=365),
    api_key: str = Depends(get_api_key)
):
    """
    Compare revenue across all platforms

    Returns side-by-side revenue comparison for business analysis.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        comparison = {}
        total_revenue = 0

        platforms = ['pinnacle_ai', 'free_ecommerce']

        for platform in platforms:
            summary = await analytics_engine._get_payment_summary(platform, start_date, end_date)
            comparison[platform] = {
                'revenue': summary['total_revenue'],
                'transactions': summary['transaction_count'],
                'average_transaction': summary['average_transaction_value'],
                'success_rate': summary['success_rate']
            }
            total_revenue += summary['total_revenue']

        # Calculate market share
        for platform in platforms:
            comparison[platform]['market_share'] = (
                comparison[platform]['revenue'] / total_revenue * 100
            ) if total_revenue > 0 else 0

        return {
            'period_days': days,
            'comparison': comparison,
            'total_revenue': total_revenue
        }

    except Exception as e:
        logger.error(f"Failed to compare platform revenue: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare revenue")

@app.get("/metrics/performance-indicators")
async def get_key_performance_indicators(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    api_key: str = Depends(get_api_key)
):
    """
    Get key performance indicators (KPIs) across all platforms

    Returns business-critical metrics for executive dashboards.
    """
    try:
        # Get global dashboard
        dashboard = await analytics_engine.get_payment_dashboard(None, days)
        summary = dashboard['summary']

        # Calculate KPIs
        kpis = {
            'monthly_recurring_revenue': 0,  # Would calculate from subscription data
            'customer_acquisition_cost': 0,   # Would calculate from marketing data
            'customer_lifetime_value': 0,     # Would calculate from historical data
            'churn_rate': 0,                  # Would calculate from subscription data
            'payment_success_rate': summary['success_rate'],
            'average_transaction_value': summary['average_transaction_value'],
            'total_revenue': summary['total_revenue'],
            'total_transactions': summary['transaction_count'],
            'revenue_growth_rate': 0,         # Would calculate from trends
            'customer_satisfaction_score': 0  # Would integrate from surveys
        }

        # Calculate revenue growth rate from trends
        trends = dashboard['trends']['daily_revenue']
        if len(trends) >= 14:
            recent_revenue = sum(t['revenue'] for t in trends[-7:])
            previous_revenue = sum(t['revenue'] for t in trends[-14:-7])

            if previous_revenue > 0:
                kpis['revenue_growth_rate'] = (
                    (recent_revenue - previous_revenue) / previous_revenue * 100
                )

        return {
            'period_days': days,
            'kpis': kpis,
            'last_updated': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get KPIs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve KPIs")

# Helper function for API key validation
async def get_api_key(api_key: str = Query(..., alias="api_key")):
    """Validate API key for analytics access"""
    expected_key = os.getenv('ANALYTICS_API_KEY', 'analytics_key_123')
    if api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

if __name__ == "__main__":
    uvicorn.run(
        "analytics-service:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8002)),
        reload=True
    )