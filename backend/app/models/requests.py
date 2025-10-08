"""
Pydantic request models for API validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator


class AnalyzeRequest(BaseModel):
    """Request model for website analysis endpoint."""
    
    url: HttpUrl = Field(..., description="Website URL to analyze")
    questions: Optional[List[str]] = Field(
        default=None, 
        description="Optional custom questions to answer about the website"
    )
    
    @validator('questions')
    def validate_questions(cls, v):
        if v is not None and len(v) > 10:
            raise ValueError('Maximum 10 custom questions allowed')
        return v


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    
    session_id: Optional[str] = Field(
        default=None, 
        description="Analysis session ID (alternative to URL)"
    )
    url: Optional[HttpUrl] = Field(
        default=None, 
        description="Website URL (alternative to session_id)"
    )
    query: str = Field(..., description="User's question about the website")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Previous conversation turns for context"
    )
    
    @validator('conversation_history')
    def validate_conversation_history(cls, v):
        if v is not None and len(v) > 20:
            raise ValueError('Maximum 20 conversation history entries allowed')
        return v
    
    @validator('query')
    def validate_query(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Query must be at least 3 characters long')
        if len(v) > 1000:
            raise ValueError('Query must be less than 1000 characters')
        return v.strip()


class HealthCheckRequest(BaseModel):
    """Request model for health check endpoint."""
    
    include_stats: Optional[bool] = Field(
        default=False,
        description="Whether to include database and vector store statistics"
    )
