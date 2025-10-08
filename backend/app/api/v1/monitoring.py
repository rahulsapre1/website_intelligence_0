"""
Monitoring and health check API endpoints.
"""

import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.middleware.auth import get_current_user
from app.services.monitoring import health_checker, metrics_collector
from app.utils.logger import api_logger

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "production"
    }


@router.get("/health/detailed")
async def detailed_health_check(current_user: str = Depends(get_current_user)):
    """Detailed health check with all service components."""
    try:
        health_status = await health_checker.run_all_checks()
        overall_status = health_checker.get_overall_status(health_status)
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "environment": "production",
            "services": {
                name: {
                    "status": status.status,
                    "response_time_ms": status.response_time_ms,
                    "last_check": status.last_check.isoformat(),
                    "error": status.error_message,
                    "metadata": status.metadata
                }
                for name, status in health_status.items()
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.get("/metrics")
async def get_metrics(current_user: str = Depends(get_current_user)):
    """Get system metrics."""
    try:
        metrics = metrics_collector.get_metrics()
        
        # Calculate success rates
        total_requests = metrics["requests_total"]
        if total_requests > 0:
            success_rate = (metrics["requests_successful"] / total_requests) * 100
        else:
            success_rate = 0
        
        scraping_attempts = metrics["scraping_attempts"]
        if scraping_attempts > 0:
            scraping_success_rate = (metrics["scraping_successes"] / scraping_attempts) * 100
        else:
            scraping_success_rate = 0
        
        ai_attempts = metrics["ai_processing_attempts"]
        if ai_attempts > 0:
            ai_success_rate = (metrics["ai_processing_successes"] / ai_attempts) * 100
        else:
            ai_success_rate = 0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                **metrics,
                "success_rate_percent": round(success_rate, 2),
                "scraping_success_rate_percent": round(scraping_success_rate, 2),
                "ai_success_rate_percent": round(ai_success_rate, 2)
            }
        }
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metrics retrieval failed"
        )


@router.post("/metrics/reset")
async def reset_metrics(current_user: str = Depends(get_current_user)):
    """Reset system metrics."""
    try:
        metrics_collector.reset_metrics()
        api_logger.info("Metrics reset by user", user=current_user)
        
        return {
            "message": "Metrics reset successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Metrics reset failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metrics reset failed"
        )


@router.get("/status")
async def system_status():
    """Get system status for monitoring tools."""
    try:
        # Quick health check
        health_status = await health_checker.run_all_checks()
        overall_status = health_checker.get_overall_status(health_status)
        
        # Get basic metrics
        metrics = metrics_collector.get_metrics()
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - metrics["last_reset"]).total_seconds(),
            "requests_total": metrics["requests_total"],
            "average_response_time_ms": metrics["average_response_time_ms"],
            "services_healthy": sum(1 for s in health_status.values() if s.status == "healthy"),
            "services_total": len(health_status)
        }
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
