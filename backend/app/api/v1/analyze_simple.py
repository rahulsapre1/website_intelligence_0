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
from app.services.crawler import FocusedCrawler
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.core.config import settings

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
@analyze_rate_limit
async def analyze_website_simple(
    request: Request,
    analyze_request: AnalyzeRequest,
    current_user: str = Depends(get_current_user)
) -> AnalyzeResponse:
    """
    Analyze a website and extract business insights (simplified version without database).
    """
    start_time = time.time()
    
    try:
        api_logger.info("Starting simplified analysis", url=str(analyze_request.url), user="demo")
        
        # Check cache first
        questions_hash = hashlib.md5(str(analyze_request.questions or []).encode()).hexdigest()
        cached_result = cache_service.get_analysis_result(str(analyze_request.url), questions_hash)
        
        if cached_result:
            api_logger.info("Returning cached analysis result", url=str(analyze_request.url))
            return AnalyzeResponse(**cached_result)
        
        # Initialize services (excluding database and vector store)
        scraper = WebScraper()
        fallback_scraper = FallbackScraper()
        ai_processor = AIProcessor()
        text_processor = TextProcessor()
        
        # Step 1: Scrape website content (check cache first)
        scraping_result = cache_service.get_scraped_content(str(analyze_request.url))
        
        if not scraping_result:
            scraping_result = await scraper.scrape_url(str(analyze_request.url))
            # Cache the scraping result
            if scraping_result["success"]:
                cache_service.set_scraped_content(str(analyze_request.url), scraping_result)
        
        if not scraping_result["success"]:
            # Try fallback scraper if available
            if fallback_scraper.is_available():
                logger.info(f"Primary scraper failed, trying fallback for {analyze_request.url}")
                scraping_result = await fallback_scraper.scrape_url(str(analyze_request.url))
            
            if not scraping_result["success"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorDetail(
                        message="Failed to scrape website content",
                        code="SCRAPING_FAILED",
                        details={"url": str(analyze_request.url), "error": scraping_result.get("error_message")}
                    ).dict()
                )
        
        # Step 2: Optionally crawl a few relevant in-domain pages for richer context
        content = scraping_result["full_text"]
        crawled_urls = []
        try:
            crawler = FocusedCrawler()
            extra_pages = await crawler.crawl(
                base_url=str(analyze_request.url),
                homepage_html=scraping_result.get("html_content", ""),
                questions=analyze_request.questions or []
            )
            if extra_pages:
                # Merge extra page texts, capped to a reasonable size
                merged_extra = "\n\n".join(p["full_text"][:8000] for p in extra_pages)
                content = (content + "\n\n" + merged_extra)[:50000]
                crawled_urls = [p["url"] for p in extra_pages]
                api_logger.info("Augmented content with crawled pages", extra_pages=len(extra_pages))
        except Exception as e:
            logger.warning(f"Focused crawl skipped due to error: {e}")
        # Generate a session_id early so we can use it for vector storage
        import uuid
        session_id = str(uuid.uuid4())

        # Step 3: Persist to vector store (if configured): chunk → embed → upsert
        try:
            if settings.qdrant_url and settings.qdrant_api_key and settings.gemini_api_key:
                text_chunks = text_processor.chunk_text(content, chunk_type="mixed")
                if text_chunks:
                    # Cap chunk count to control cost/time
                    max_chunks = 40
                    text_chunks = text_chunks[:max_chunks]
                    embedding_service = EmbeddingService()
                    vector_store = VectorStoreService()
                    # Generate embeddings (sequential; can be optimized later)
                    for ch in text_chunks:
                        chunk_text = ch["text"][:4000]
                        ch["embedding"] = await embedding_service.generate_embedding(chunk_text)
                    # Upsert to Qdrant
                    await vector_store.add_document_chunks(
                        session_id=session_id,
                        url=str(analyze_request.url),
                        chunks=text_chunks
                    )
                    api_logger.info("Stored chunks in vector store", chunks=len(text_chunks))
        except Exception as e:
            logger.warning(f"Vector store step skipped due to error: {e}")

        api_logger.info("Extracted content for AI processing", content_length=len(content))
        
        # Check cache for AI insights
        content_hash = hashlib.md5(content.encode()).hexdigest()
        insights = cache_service.get_ai_insights(content_hash)
        
        if not insights:
            insights = await ai_processor.extract_business_insights(
                content, 
                custom_questions=analyze_request.questions
            )
            # Cache the AI insights
            cache_service.set_ai_insights(content_hash, insights)
        
        # Step 4: Create response (without database storage)
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
            custom_questions_count=len(analyze_request.questions) if analyze_request.questions else 0,
            extraction_method="gemini_2.5_flash",
            confidence=insights.get("confidence_score", 5),
            scraping_method=scraping_result["scraping_method"],
            processing_time_ms=processing_time_ms
        )
        
        response = AnalyzeResponse(
            session_id=session_id,
            url=str(analyze_request.url),
            scraped_at=scraping_result["scraped_at"],
            insights=business_insights,
            custom_answers=insights.get("custom_answers", []),
            extraction_metadata=extraction_metadata,
            fallback_used=scraping_result["scraping_method"] == "fallback",
            success=True,
            crawled_urls=crawled_urls or None
        )
        
        # Cache the complete result
        cache_service.set_analysis_result(str(analyze_request.url), response.dict(), questions_hash)
        
        api_logger.info("Analysis completed", 
                       processing_time_ms=processing_time_ms, 
                       url=str(analyze_request.url),
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
            ).dict()
        )
