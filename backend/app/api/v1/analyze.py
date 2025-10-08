"""
API endpoint for website analysis.
"""

import logging
import time
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.middleware.auth import get_current_user
from app.middleware.rate_limit import analyze_rate_limit
from app.models.requests import AnalyzeRequest
from app.models.responses import AnalyzeResponse, ErrorResponse, ErrorDetail
from app.services.scraper import WebScraper
from app.services.scraper_fallback import FallbackScraper
from app.services.ai_processor import AIProcessor
from app.services.embeddings import EmbeddingService
from app.services.database import DatabaseService
from app.services.vector_store import VectorStoreService
from app.utils.text_processor import TextProcessor

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Services will be initialized lazily to avoid import-time errors


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate Limited"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Analyze Website",
    description="Extract business insights from a website homepage using AI"
)
@analyze_rate_limit
async def analyze_website(
    request: AnalyzeRequest,
    current_user: str = Depends(get_current_user)
) -> AnalyzeResponse:
    """
    Analyze a website and extract business insights.
    
    This endpoint:
    1. Scrapes the website content (with fallback for JS-heavy sites)
    2. Uses AI to extract structured business insights
    3. Stores the analysis in the database
    4. Creates vector embeddings for semantic search
    5. Returns comprehensive business intelligence
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting analysis for URL: {request.url}")
        
        # Initialize services
        scraper = WebScraper()
        fallback_scraper = FallbackScraper()
        ai_processor = AIProcessor()
        embedding_service = EmbeddingService()
        database_service = DatabaseService()
        vector_store_service = VectorStoreService()
        text_processor = TextProcessor()
        
        # Check for recent analysis (simple caching)
        recent_session = await database_service.check_recent_analysis(str(request.url), hours=1)
        if recent_session:
            logger.info(f"Returning cached analysis for {request.url}")
            return _create_response_from_session(recent_session, request.questions)
        
        # Step 1: Scrape website content
        scraping_result = await scraper.scrape_url(str(request.url))
        
        if not scraping_result["success"]:
            # Try fallback scraper if available
            if fallback_scraper.is_available():
                logger.info(f"Primary scraper failed, trying fallback for {request.url}")
                scraping_result = await fallback_scraper.scrape_url(str(request.url))
            
            if not scraping_result["success"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorDetail(
                        message="Failed to scrape website content",
                        code="SCRAPING_FAILED",
                        details={"url": str(request.url), "error": scraping_result.get("error_message")}
                    )
                )
        
        # Step 2: Extract business insights using AI
        content = scraping_result["full_text"]
        if not content or len(content.strip()) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorDetail(
                    message="Insufficient content extracted from website",
                    code="INSUFFICIENT_CONTENT",
                    details={"content_length": len(content) if content else 0}
                )
            )
        
        insights = await ai_processor.extract_business_insights(
            content, 
            request.questions
        )
        
        if insights.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorDetail(
                    message="AI processing failed",
                    code="AI_PROCESSING_FAILED",
                    details={"error": insights.get("error_message")}
                )
            )
        
        # Step 3: Create analysis session in database
        session_data = await database_service.create_analysis_session(
            url=str(request.url),
            scraped_content=scraping_result["html_content"],
            scraping_method=scraping_result["scraping_method"],
            insights=insights
        )
        
        # Step 4: Process content for vector storage
        structured_content = scraping_result.get("structured_content", {})
        chunks = text_processor.chunk_text(content, "paragraph")
        
        # Generate embeddings for chunks
        chunks_with_embeddings = await embedding_service.generate_chunk_embeddings(chunks)
        
        # Store in vector database
        await vector_store_service.add_document_chunks(
            session_id=session_data["id"],
            url=str(request.url),
            chunks=chunks_with_embeddings
        )
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        # Create response
        response = AnalyzeResponse(
            session_id=session_data["id"],
            url=str(request.url),
            scraped_at=scraping_result.get("scraped_at", ""),
            insights=insights,
            custom_answers=insights.get("custom_answers"),
            extraction_metadata={
                "content_length": len(content),
                "custom_questions_count": len(request.questions) if request.questions else 0,
                "extraction_method": "gemini_2.5_flash",
                "confidence": insights.get("confidence_score", "Not provided"),
                "scraping_method": scraping_result["scraping_method"],
                "processing_time_ms": processing_time
            },
            fallback_used=scraping_result["scraping_method"] == "fallback",
            success=True
        )
        
        logger.info(f"Successfully analyzed {request.url} in {processing_time}ms")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error analyzing {request.url}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                message="Internal server error during analysis",
                code="INTERNAL_ERROR",
                details={"error": str(e)}
            )
        )


def _create_response_from_session(session_data: Dict[str, Any], custom_questions: list = None) -> AnalyzeResponse:
    """Create response from cached session data."""
    insights = session_data.get("insights", {})
    
    return AnalyzeResponse(
        session_id=session_data["id"],
        url=session_data["url"],
        scraped_at=session_data["created_at"],
        insights=insights,
        custom_answers=insights.get("custom_answers") if custom_questions else None,
        extraction_metadata={
            "content_length": len(session_data.get("scraped_content", "")),
            "custom_questions_count": len(custom_questions) if custom_questions else 0,
            "extraction_method": "cached",
            "confidence": insights.get("confidence_score", "Not provided"),
            "scraping_method": session_data.get("scraping_method", "unknown"),
            "processing_time_ms": 0
        },
        fallback_used=session_data.get("scraping_method") == "fallback",
        success=True
    )
