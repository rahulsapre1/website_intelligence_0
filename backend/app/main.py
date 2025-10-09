"""
Website Intelligence API - Main FastAPI application.
"""

import logging
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

@app.post("/test-endpoint")
async def test_endpoint():
    """Test endpoint without authentication."""
    return {"message": "Test endpoint working", "status": "success"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "log_level": settings.log_level
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
