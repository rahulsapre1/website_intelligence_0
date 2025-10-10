"""
Pydantic response models for API responses.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    message: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: ErrorDetail = Field(..., description="Error details")
    status_code: int = Field(..., description="HTTP status code")


class ContactInfo(BaseModel):
    """Contact information structure."""
    
    email: Optional[str] = Field(default=None, description="Primary contact email")
    phone: Optional[str] = Field(default=None, description="Phone number")
    social_media: List[str] = Field(default_factory=list, description="Social media links")


class BusinessInsights(BaseModel):
    """Business insights structure."""
    
    industry: str = Field(..., description="Company industry")
    company_size: str = Field(..., description="Company size category")
    location: str = Field(..., description="Company location")
    usp: str = Field(..., description="Unique selling proposition")
    products_services: List[str] = Field(..., description="Main products or services")
    target_audience: str = Field(..., description="Target audience")
    contact_info: ContactInfo = Field(..., description="Contact information")
    confidence_score: Optional[int] = Field(default=None, description="Confidence score 1-10")
    key_insights: List[str] = Field(default_factory=list, description="Additional insights")


class ExtractionMetadata(BaseModel):
    """Extraction process metadata."""
    
    content_length: int = Field(..., description="Length of scraped content")
    custom_questions_count: int = Field(..., description="Number of custom questions")
    extraction_method: str = Field(..., description="AI model used for extraction")
    confidence: Union[int, str] = Field(..., description="Overall confidence score")
    scraping_method: str = Field(..., description="Scraping method used")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time in milliseconds")


class AnalyzeResponse(BaseModel):
    """Response model for website analysis endpoint."""
    
    session_id: str = Field(..., description="Unique session identifier")
    url: str = Field(..., description="Analyzed website URL")
    scraped_at: str = Field(..., description="Timestamp when content was scraped")
    insights: BusinessInsights = Field(..., description="Extracted business insights")
    custom_answers: Optional[List[str]] = Field(default=None, description="Answers to custom questions")
    extraction_metadata: ExtractionMetadata = Field(..., description="Extraction process metadata")
    fallback_used: bool = Field(..., description="Whether fallback scraper was used")
    success: bool = Field(default=True, description="Whether analysis was successful")
    crawled_urls: Optional[List[str]] = Field(default=None, description="List of in-domain links crawled for additional context")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    
    session_id: str = Field(..., description="Analysis session ID")
    answer: str = Field(..., description="AI-generated answer")
    query: str = Field(..., description="Original user query")
    conversation_id: str = Field(..., description="Unique conversation identifier")
    sources: List[str] = Field(default_factory=list, description="Source chunks used for answer")
    answer_metadata: Dict[str, Any] = Field(..., description="Answer generation metadata")
    follow_up_suggestions: Optional[List[str]] = Field(default=None, description="Suggested follow-up questions")


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str = Field(..., description="Service status")
    environment: str = Field(..., description="Environment name")
    log_level: str = Field(..., description="Current log level")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = Field(default="1.0.0", description="API version")
    database_stats: Optional[Dict[str, Any]] = Field(default=None, description="Database statistics")
    vector_store_stats: Optional[Dict[str, Any]] = Field(default=None, description="Vector store statistics")


class StatsResponse(BaseModel):
    """Response model for statistics endpoint."""
    
    total_sessions: int = Field(..., description="Total analysis sessions")
    total_conversations: int = Field(..., description="Total conversations")
    recent_sessions_24h: int = Field(..., description="Sessions in last 24 hours")
    database_status: str = Field(..., description="Database connection status")
    vector_store_status: str = Field(..., description="Vector store connection status")
    uptime_seconds: Optional[int] = Field(default=None, description="Service uptime in seconds")


class ScrapingResult(BaseModel):
    """Scraping operation result."""
    
    success: bool = Field(..., description="Whether scraping was successful")
    url: str = Field(..., description="Scraped URL")
    scraping_method: str = Field(..., description="Method used for scraping")
    content_length: int = Field(..., description="Length of scraped content")
    text_length: int = Field(..., description="Length of extracted text")
    fallback_decision: Dict[str, Any] = Field(..., description="Fallback decision details")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class VectorSearchResult(BaseModel):
    """Vector search result."""
    
    id: str = Field(..., description="Chunk ID")
    score: float = Field(..., description="Similarity score")
    text: str = Field(..., description="Chunk text")
    chunk_type: str = Field(..., description="Type of chunk")
    session_id: str = Field(..., description="Source session ID")
    url: str = Field(..., description="Source URL")
    chunk_index: int = Field(..., description="Chunk index in document")
    text_length: int = Field(..., description="Length of chunk text")
