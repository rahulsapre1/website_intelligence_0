"""
Simplified API endpoint for website analysis (without database).
"""

import logging
import time
import hashlib
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.middleware.auth import get_current_user
from app.middleware.rate_limit import analyze_rate_limit
from app.models.requests import AnalyzeRequest
from app.models.responses import AnalyzeResponse, ErrorResponse, ErrorDetail, BusinessInsights, ContactInfo, ExtractionMetadata
from app.services.scraper import WebScraper
from app.services.scraper_fallback import FallbackScraper
from app.services.ai_processor import AIProcessor
from app.services.cache import cache_service
from app.utils.text_processor import TextProcessor
from app.utils.logger import api_logger

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()


@router.post(
    "/analyze-simple",
    response_model=AnalyzeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate Limited"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Analyze Website (Simplified)",
    description="Extract business insights from a website homepage using AI (without database storage)"
)
# @analyze_rate_limit  # Temporarily disabled for debugging
async def analyze_website_simple(
    request: AnalyzeRequest,
    # current_user: str = Depends(get_current_user)  # Temporarily disabled for testing
) -> AnalyzeResponse:
    """
    Analyze a website and extract business insights (simplified version without database).
    """
    start_time = time.time()
    
    try:
        api_logger.info("Starting simplified analysis", url=str(request.url), user="demo")
        
        # Check cache first
        questions_hash = hashlib.md5(str(request.questions or []).encode()).hexdigest()
        cached_result = cache_service.get_analysis_result(str(request.url), questions_hash)
        
        if cached_result:
            api_logger.info("Returning cached analysis result", url=str(request.url))
            return AnalyzeResponse(**cached_result)
        
        # Initialize services (excluding database and vector store)
        scraper = WebScraper()
        fallback_scraper = FallbackScraper()
        ai_processor = AIProcessor()
        text_processor = TextProcessor()
        
        # Step 1: Scrape website content (check cache first)
        scraping_result = cache_service.get_scraped_content(str(request.url))
        
        if not scraping_result:
            scraping_result = await scraper.scrape_url(str(request.url))
            # Cache the scraping result
            if scraping_result["success"]:
                cache_service.set_scraped_content(str(request.url), scraping_result)
        
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
        api_logger.info("Extracted content for AI processing", content_length=len(content))
        
        # Check cache for AI insights
        content_hash = hashlib.md5(content.encode()).hexdigest()
        insights = cache_service.get_ai_insights(content_hash)
        
        if not insights:
            insights = await ai_processor.extract_business_insights(
                content, 
                custom_questions=request.questions
            )
            # Cache the AI insights
            cache_service.set_ai_insights(content_hash, insights)
        
        # Step 3: Create response (without database storage)
        session_id = f"simple_{int(time.time())}_{hash(str(request.url)) % 10000}"
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Create proper response objects
        contact_info = ContactInfo(
            email=insights.get("contact_info", {}).get("email"),
            phone=insights.get("contact_info", {}).get("phone"),
            social_media=insights.get("contact_info", {}).get("social_media", [])
        )
        
        business_insights = BusinessInsights(
            industry=insights.get("industry", "Unknown"),
            company_size=insights.get("company_size", "Unknown"),
            location=insights.get("location", "Unknown"),
            usp=insights.get("usp", "Not specified"),
            products_services=insights.get("products_services", []),
            target_audience=insights.get("target_audience", "Not specified"),
            contact_info=contact_info,
            confidence_score=insights.get("confidence_score", 5),
            key_insights=insights.get("key_insights", [])
        )
        
        extraction_metadata = ExtractionMetadata(
            content_length=len(content),
            custom_questions_count=len(request.questions) if request.questions else 0,
            extraction_method="gemini_2.5_flash",
            confidence=insights.get("confidence_score", 5),
            scraping_method=scraping_result["scraping_method"],
            processing_time_ms=processing_time_ms
        )
        
        response = AnalyzeResponse(
            session_id=session_id,
            url=str(request.url),
            scraped_at=scraping_result["scraped_at"],
            insights=business_insights,
            custom_answers=insights.get("custom_answers", []),
            extraction_metadata=extraction_metadata,
            fallback_used=scraping_result["scraping_method"] == "fallback",
            success=True
        )
        
        # Cache the complete result
        cache_service.set_analysis_result(str(request.url), response.dict(), questions_hash)
        
        api_logger.info("Analysis completed", 
                       processing_time_ms=processing_time_ms, 
                       url=str(request.url),
                       cached=True)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                message="Internal server error during analysis",
                code="ANALYSIS_ERROR",
                details={"error": str(e)}
            )
        )
