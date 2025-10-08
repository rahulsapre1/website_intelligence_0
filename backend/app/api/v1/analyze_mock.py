"""
Mock API endpoint for website analysis (returns sample data).
"""

import asyncio
import logging
import time
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.middleware.auth import get_current_user
from app.middleware.rate_limit import analyze_rate_limit
from app.models.requests import AnalyzeRequest
from app.models.responses import AnalyzeResponse, ErrorResponse, ErrorDetail, BusinessInsights, ContactInfo, ExtractionMetadata

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()


@router.post(
    "/analyze-mock",
    response_model=AnalyzeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate Limited"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Analyze Website (Mock)",
    description="Mock endpoint that returns sample business insights"
)
async def analyze_website_mock(
    request: AnalyzeRequest,
    current_user: str = Depends(get_current_user)
) -> AnalyzeResponse:
    """
    Mock analyze endpoint that returns sample data.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Mock analysis for URL: {request.url}")
        
        # Simulate processing time
        await asyncio.sleep(1)
        
        # Return mock data
        session_id = f"mock_{int(time.time())}_{hash(str(request.url)) % 10000}"
        
        # Create proper ContactInfo object
        contact_info = ContactInfo(
            email="contact@example.com",
            phone="+1 (555) 123-4567",
            social_media=["https://linkedin.com/company/example", "https://twitter.com/example"]
        )
        
        # Create proper BusinessInsights object
        mock_insights = BusinessInsights(
            industry="Technology/SaaS",
            company_size="Medium (50-200 employees)",
            location="San Francisco, CA",
            usp="AI-powered platform that helps businesses automate their workflows and increase productivity through intelligent automation tools.",
            products_services=[
                "Workflow Automation",
                "AI Analytics",
                "Integration Services",
                "Custom Solutions"
            ],
            target_audience="B2B enterprises looking to streamline operations and improve efficiency",
            contact_info=contact_info,
            confidence_score=8,
            key_insights=[
                "Modern SaaS platform with AI capabilities",
                "Focus on workflow automation for enterprises",
                "Strong emphasis on productivity and efficiency",
                "Professional B2B positioning"
            ]
        )
        
        # Create proper ExtractionMetadata object
        processing_time_ms = int((time.time() - start_time) * 1000)
        extraction_metadata = ExtractionMetadata(
            content_length=1500,
            custom_questions_count=len(request.questions) if request.questions else 0,
            extraction_method="mock_data",
            confidence=8,
            scraping_method="mock",
            processing_time_ms=processing_time_ms
        )
        
        response = AnalyzeResponse(
            session_id=session_id,
            url=str(request.url),
            scraped_at=time.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            insights=mock_insights,
            custom_answers=["Mock answer 1", "Mock answer 2"] if request.questions else [],
            extraction_metadata=extraction_metadata,
            fallback_used=False,
            success=True
        )
        
        logger.info(f"Mock analysis completed in {processing_time_ms}ms")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during mock analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                message="Internal server error during mock analysis",
                code="MOCK_ANALYSIS_ERROR",
                details={"error": str(e)}
            )
        )
