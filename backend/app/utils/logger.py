"""
Enhanced logging utilities for production monitoring.
"""

import logging
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager
from app.core.config import settings


class StructuredLogger:
    """Structured logger for production monitoring."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, settings.log_level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for production
        if settings.environment == "production":
            file_handler = logging.FileHandler("app.log")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _log_structured(self, level: str, message: str, **kwargs):
        """Log structured data."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "environment": settings.environment,
            **kwargs
        }
        
        if level.upper() == "ERROR":
            self.logger.error(json.dumps(log_data))
        elif level.upper() == "WARNING":
            self.logger.warning(json.dumps(log_data))
        elif level.upper() == "INFO":
            self.logger.info(json.dumps(log_data))
        else:
            self.logger.debug(json.dumps(log_data))
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        self._log_structured("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        self._log_structured("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data."""
        self._log_structured("ERROR", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data."""
        self._log_structured("DEBUG", message, **kwargs)
    
    @contextmanager
    def log_performance(self, operation: str, **context):
        """Context manager for performance logging."""
        start_time = datetime.utcnow()
        self.info(f"Starting {operation}", operation=operation, **context)
        
        try:
            yield
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.info(f"Completed {operation}", operation=operation, duration_seconds=duration, **context)
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.error(f"Failed {operation}", operation=operation, duration_seconds=duration, 
                      error=str(e), traceback=traceback.format_exc(), **context)
            raise
    
    def log_api_request(self, method: str, url: str, status_code: int, 
                       duration_ms: float, user_id: Optional[str] = None, **kwargs):
        """Log API request with performance metrics."""
        self.info("API Request", 
                 method=method, 
                 url=str(url), 
                 status_code=status_code,
                 duration_ms=duration_ms,
                 user_id=user_id,
                 **kwargs)
    
    def log_scraping_result(self, url: str, success: bool, method: str, 
                           content_length: int, duration_ms: float, **kwargs):
        """Log web scraping results."""
        level = "INFO" if success else "WARNING"
        self._log_structured(level, "Web Scraping Result",
                           url=url,
                           success=success,
                           method=method,
                           content_length=content_length,
                           duration_ms=duration_ms,
                           **kwargs)
    
    def log_ai_processing(self, operation: str, success: bool, duration_ms: float, 
                         content_length: int, **kwargs):
        """Log AI processing results."""
        level = "INFO" if success else "ERROR"
        self._log_structured(level, "AI Processing",
                           operation=operation,
                           success=success,
                           duration_ms=duration_ms,
                           content_length=content_length,
                           **kwargs)
    
    def log_rate_limit(self, ip_address: str, endpoint: str, limit: str):
        """Log rate limit violations."""
        self.warning("Rate Limit Exceeded",
                    ip_address=ip_address,
                    endpoint=endpoint,
                    limit=limit)
    
    def log_security_event(self, event_type: str, ip_address: str, **kwargs):
        """Log security-related events."""
        self.warning("Security Event",
                    event_type=event_type,
                    ip_address=ip_address,
                    **kwargs)


# Global logger instances
api_logger = StructuredLogger("api")
scraper_logger = StructuredLogger("scraper")
ai_logger = StructuredLogger("ai")
security_logger = StructuredLogger("security")
