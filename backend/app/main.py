"""
Website Intelligence API - Main FastAPI application.
"""

import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.middleware.rate_limit import limiter, rate_limit_handler


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log") if settings.environment == "production" else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Website Intelligence API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Log Level: {settings.log_level}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Website Intelligence API...")


# Create FastAPI app
app = FastAPI(
    title="Website Intelligence API",
    description="AI-powered website analysis and conversational interface",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [
        "https://website-intelligence.vercel.app",
        "https://www.website-intelligence.vercel.app",
        "https://website-intelligence-frontend.vercel.app",
        "https://website-intelligence-0.vercel.app",
        "https://website-intelligence-0-git-main-rahuls-projects-ce3d64d4.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Handle OPTIONS requests explicitly
@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests."""
    return Response(status_code=200)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    logger.info(f"{request.method} {request.url} - {request.client.host}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response


@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Website Intelligence API",
        "version": "1.0.0",
        "status": "healthy",
        "environment": settings.environment
    }

@app.post("/test-demo")
async def test_demo():
    """Simple test endpoint."""
    return {"message": "Demo endpoint working", "timestamp": int(time.time())}

@app.get("/test-services")
async def test_services():
    """Test endpoint to check service status."""
    from app.services.ai_processor import AIProcessor
    from app.services.scraper import WebScraper
    from app.services.scraper_fallback import FallbackScraper
    
    ai_processor = AIProcessor()
    scraper = WebScraper()
    fallback_scraper = FallbackScraper()
    
    return {
        "ai_processor_mock_mode": ai_processor.mock_mode,
        "ai_processor_has_api_key": bool(ai_processor.api_key),
        "fallback_scraper_mock_mode": fallback_scraper.mock_mode,
        "fallback_scraper_has_api_key": bool(fallback_scraper.api_key),
        "scraper_timeout": scraper.timeout,
        "timestamp": int(time.time())
    }

@app.post("/api/v1/analyze-simple-debug")
async def analyze_simple_debug(request: dict):
    """Debug version of analyze-simple to identify issues."""
    try:
        from app.services.ai_processor import AIProcessor
        from app.services.scraper import WebScraper
        from app.services.scraper_fallback import FallbackScraper
        
        # Test service initialization
        ai_processor = AIProcessor()
        scraper = WebScraper()
        fallback_scraper = FallbackScraper()
        
        return {
            "status": "services_initialized",
            "ai_processor_mock_mode": ai_processor.mock_mode,
            "fallback_scraper_mock_mode": fallback_scraper.mock_mode,
            "url": request.get("url", "https://example.com"),
            "timestamp": int(time.time())
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "url": request.get("url", "https://example.com"),
            "timestamp": int(time.time())
        }

@app.post("/api/v1/test-imports")
async def test_imports(request: dict):
    """Test endpoint to check if imports are working."""
    try:
        # Test basic imports
        from app.models.requests import AnalyzeRequest
        from app.models.responses import AnalyzeResponse
        
        # Test service imports
        from app.services.ai_processor import AIProcessor
        from app.services.scraper import WebScraper
        from app.services.scraper_fallback import FallbackScraper
        from app.services.cache import cache_service
        from app.utils.text_processor import TextProcessor
        
        return {
            "status": "imports_successful",
            "url": request.get("url", "https://example.com"),
            "timestamp": int(time.time())
        }
    except Exception as e:
        return {
            "status": "import_error",
            "error": str(e),
            "error_type": type(e).__name__,
            "url": request.get("url", "https://example.com"),
            "timestamp": int(time.time())
        }

@app.post("/api/v1/analyze-demo")
async def analyze_demo(request: dict):
    """Demo endpoint that returns mock analysis data without authentication."""
    from app.services.ai_processor import AIProcessor
    from app.services.scraper import WebScraper
    from app.services.scraper_fallback import FallbackScraper
    
    ai_processor = AIProcessor()
    scraper = WebScraper()
    fallback_scraper = FallbackScraper()
    
    return {
        "session_id": f"demo_{int(time.time())}",
        "url": request.get("url", "https://example.com"),
        "scraped_at": "2024-01-01T00:00:00Z",
        "insights": {
            "industry": "Technology/SaaS",
            "company_size": "Medium (50-200 employees)",
            "location": "San Francisco, CA",
            "usp": "AI-powered platform that helps businesses automate their workflows and increase productivity through intelligent automation tools.",
            "products_services": [
                "Workflow Automation",
                "AI Analytics", 
                "Integration Services",
                "Custom Solutions"
            ],
            "target_audience": "B2B enterprises looking to streamline operations and improve efficiency",
            "contact_info": {
                "email": "contact@example.com",
                "phone": "+1 (555) 123-4567",
                "address": "123 Tech Street, San Francisco, CA 94105"
            }
        },
        "custom_answers": [
            "This appears to be a technology company focused on business automation solutions.",
            "They offer AI-powered tools for workflow management and productivity enhancement.",
            "Target market includes mid to large-scale B2B enterprises seeking operational efficiency."
        ],
        "processing_time": 2.5,
        "scraping_method": "demo",
        "content_length": 1500,
        "service_status": {
            "ai_processor_mock_mode": ai_processor.mock_mode,
            "ai_processor_has_api_key": bool(ai_processor.api_key),
            "fallback_scraper_mock_mode": fallback_scraper.mock_mode,
            "fallback_scraper_has_api_key": bool(fallback_scraper.api_key),
            "scraper_timeout": scraper.timeout,
            "env_vars": {
                "gemini_api_key_present": bool(settings.gemini_api_key),
                "jina_ai_api_key_present": bool(settings.jina_ai_api_key),
                "environment": settings.environment
            }
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "log_level": settings.log_level
    }

@app.get("/env-check")
async def env_check():
    """Check environment variables for debugging."""
    return {
        "gemini_api_key_present": bool(settings.gemini_api_key),
        "jina_ai_api_key_present": bool(settings.jina_ai_api_key),
        "environment": settings.environment,
        "api_secret_key_present": bool(settings.api_secret_key),
        "timestamp": int(time.time())
    }


# Include API routes
from app.api.v1 import analyze, chat, analyze_simple, test_simple, analyze_mock, monitoring
app.include_router(analyze.router, prefix="/api/v1", tags=["analysis"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(analyze_simple.router, prefix="/api/v1", tags=["analysis-simple"])
app.include_router(test_simple.router, prefix="/api/v1", tags=["test"])
app.include_router(analyze_mock.router, prefix="/api/v1", tags=["analysis-mock"])
app.include_router(monitoring.router, prefix="/api/v1", tags=["monitoring"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
