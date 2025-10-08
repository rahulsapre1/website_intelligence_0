"""
Production monitoring and health check services.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from app.core.config import settings
from app.utils.logger import api_logger


@dataclass
class HealthStatus:
    """Health status for a service component."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time_ms: float
    last_check: datetime
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class HealthChecker:
    """Health check service for monitoring system components."""
    
    def __init__(self):
        self.checks = {}
        self.last_full_check = None
    
    async def check_database(self) -> HealthStatus:
        """Check database connectivity."""
        start_time = time.time()
        
        try:
            from app.services.database import DatabaseService
            db = DatabaseService()
            
            # Simple connectivity test
            await db.test_connection()
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                name="database",
                status="healthy",
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                metadata={"connection": "active"}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            api_logger.error("Database health check failed", 
                           error=str(e), 
                           response_time_ms=response_time)
            
            return HealthStatus(
                name="database",
                status="unhealthy",
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def check_vector_store(self) -> HealthStatus:
        """Check vector store connectivity."""
        start_time = time.time()
        
        try:
            from app.services.vector_store import VectorStoreService
            vector_store = VectorStoreService()
            
            # Simple connectivity test
            await vector_store.test_connection()
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                name="vector_store",
                status="healthy",
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                metadata={"connection": "active"}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            api_logger.error("Vector store health check failed", 
                           error=str(e), 
                           response_time_ms=response_time)
            
            return HealthStatus(
                name="vector_store",
                status="unhealthy",
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def check_ai_services(self) -> HealthStatus:
        """Check AI services (Gemini API)."""
        start_time = time.time()
        
        try:
            from app.services.ai_processor import AIProcessor
            ai_processor = AIProcessor()
            
            # Simple API test
            await ai_processor.test_connection()
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthStatus(
                name="ai_services",
                status="healthy",
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                metadata={"gemini_api": "active"}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            api_logger.error("AI services health check failed", 
                           error=str(e), 
                           response_time_ms=response_time)
            
            return HealthStatus(
                name="ai_services",
                status="unhealthy",
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def check_scraping_services(self) -> HealthStatus:
        """Check web scraping services."""
        start_time = time.time()
        
        try:
            from app.services.scraper import WebScraper
            scraper = WebScraper()
            
            # Test with a simple, reliable site
            result = await scraper.scrape_url("https://httpbin.org/html")
            
            response_time = (time.time() - start_time) * 1000
            
            if result["success"]:
                status = "healthy"
            else:
                status = "degraded"
            
            return HealthStatus(
                name="scraping_services",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                metadata={"primary_scraper": "active" if result["success"] else "failed"}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            api_logger.error("Scraping services health check failed", 
                           error=str(e), 
                           response_time_ms=response_time)
            
            return HealthStatus(
                name="scraping_services",
                status="unhealthy",
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def run_all_checks(self) -> Dict[str, HealthStatus]:
        """Run all health checks concurrently."""
        checks = [
            self.check_database(),
            self.check_vector_store(),
            self.check_ai_services(),
            self.check_scraping_services()
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        health_status = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                health_status[f"check_{i}"] = HealthStatus(
                    name=f"check_{i}",
                    status="unhealthy",
                    response_time_ms=0,
                    last_check=datetime.utcnow(),
                    error_message=str(result)
                )
            else:
                health_status[result.name] = result
        
        self.last_full_check = datetime.utcnow()
        return health_status
    
    def get_overall_status(self, health_status: Dict[str, HealthStatus]) -> str:
        """Get overall system status."""
        if not health_status:
            return "unknown"
        
        statuses = [status.status for status in health_status.values()]
        
        if "unhealthy" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        else:
            return "healthy"


class MetricsCollector:
    """Collect and store system metrics."""
    
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "average_response_time_ms": 0,
            "scraping_attempts": 0,
            "scraping_successes": 0,
            "ai_processing_attempts": 0,
            "ai_processing_successes": 0,
            "rate_limit_hits": 0,
            "last_reset": datetime.utcnow()
        }
    
    def record_request(self, success: bool, response_time_ms: float):
        """Record API request metrics."""
        self.metrics["requests_total"] += 1
        if success:
            self.metrics["requests_successful"] += 1
        else:
            self.metrics["requests_failed"] += 1
        
        # Update average response time
        total_requests = self.metrics["requests_total"]
        current_avg = self.metrics["average_response_time_ms"]
        self.metrics["average_response_time_ms"] = (
            (current_avg * (total_requests - 1) + response_time_ms) / total_requests
        )
    
    def record_scraping(self, success: bool):
        """Record scraping metrics."""
        self.metrics["scraping_attempts"] += 1
        if success:
            self.metrics["scraping_successes"] += 1
    
    def record_ai_processing(self, success: bool):
        """Record AI processing metrics."""
        self.metrics["ai_processing_attempts"] += 1
        if success:
            self.metrics["ai_processing_successes"] += 1
    
    def record_rate_limit_hit(self):
        """Record rate limit hit."""
        self.metrics["rate_limit_hits"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset metrics (call periodically)."""
        self.metrics = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "average_response_time_ms": 0,
            "scraping_attempts": 0,
            "scraping_successes": 0,
            "ai_processing_attempts": 0,
            "ai_processing_successes": 0,
            "rate_limit_hits": 0,
            "last_reset": datetime.utcnow()
        }


# Global instances
health_checker = HealthChecker()
metrics_collector = MetricsCollector()
