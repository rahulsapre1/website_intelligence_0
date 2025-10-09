"""
API endpoint for conversational chat about analyzed websites.
"""

import logging
import time
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.middleware.auth import get_current_user
from app.middleware.rate_limit import chat_rate_limit
from app.models.requests import ChatRequest
from app.models.responses import ChatResponse, ErrorResponse, ErrorDetail
from app.services.ai_processor import AIProcessor
from app.services.embeddings import EmbeddingService
from app.services.database import DatabaseService
from app.services.vector_store import VectorStoreService
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Services will be initialized lazily to avoid import-time errors


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Session Not Found"},
        429: {"model": ErrorResponse, "description": "Rate Limited"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Chat About Website",
    description="Ask questions about a previously analyzed website"
)
@chat_rate_limit
async def chat_about_website(
    request: ChatRequest,
    current_user: str = Depends(get_current_user)
) -> ChatResponse:
    """
    Chat about a previously analyzed website.
    
    This endpoint:
    1. Finds the analysis session (by session_id or URL)
    2. Retrieves relevant context using vector search
    3. Generates AI response using conversation history
    4. Stores the conversation for future context
    5. Returns the answer with sources
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing chat query: {request.query[:100]}...")
        
        # Initialize services with error handling
        ai_processor = AIProcessor()
        
        # Check if database services are available
        database_service = None
        vector_store_service = None
        embedding_service = None
        
        try:
            if settings.supabase_url and settings.supabase_key:
                database_service = DatabaseService()
            else:
                logger.warning("Supabase not configured, chat functionality limited")
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
        
        try:
            if settings.qdrant_url and settings.qdrant_api_key:
                vector_store_service = VectorStoreService()
                embedding_service = EmbeddingService()
            else:
                logger.warning("Qdrant not configured, vector search disabled")
        except Exception as e:
            logger.error(f"Failed to initialize vector services: {e}")
        
        # Step 1: Find analysis session
        session_data = None
        if database_service:
            if request.session_id:
                session_data = await database_service.get_analysis_session(request.session_id)
            elif request.url:
                session_data = await database_service.get_analysis_session_by_url(str(request.url))
        else:
            # If database not available, create a mock session for basic chat functionality
            if request.url:
                session_data = {
                    "id": f"mock_{hash(str(request.url))}",
                    "url": str(request.url),
                    "scraped_content": "Database not available - using mock session for basic chat functionality.",
                    "insights": {}
                }
                logger.info("Using mock session for chat due to database unavailability")
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorDetail(
                    message="Analysis session not found",
                    code="SESSION_NOT_FOUND",
                    details={
                        "session_id": request.session_id,
                        "url": str(request.url) if request.url else None,
                        "database_available": database_service is not None
                    }
                )
            )
        
        # Step 2: Get conversation history
        conversation_history = []
        if request.conversation_history:
            conversation_history = request.conversation_history
        elif database_service:
            # Get recent conversation history from database
            conversation_history = await database_service.get_conversation_history(
                session_data["id"], 
                limit=5
            )
            # Convert to expected format
            conversation_history = [
                {"query": conv["query"], "answer": conv["answer"]} 
                for conv in conversation_history
            ]
        
        # Step 3: Generate query embedding for context retrieval
        query_embedding = None
        if embedding_service:
            query_embedding = await embedding_service.generate_embedding(request.query)
        
        # Step 4: Find relevant context chunks
        relevant_chunks = []
        if query_embedding and vector_store_service:
            relevant_chunks = await vector_store_service.search_similar_chunks(
                query_embedding=query_embedding,
                session_id=session_data["id"],
                limit=5,
                score_threshold=0.6
            )
        
        # Step 5: Prepare context for AI
        context_parts = []
        sources = []
        
        # Add original scraped content as base context
        scraped_content = session_data.get("scraped_content", "")
        if scraped_content:
            context_parts.append(scraped_content[:2000])  # Limit base context
        
        # Add relevant chunks
        for chunk in relevant_chunks:
            context_parts.append(chunk["text"])
            sources.append(f"Chunk {chunk['chunk_index']}: {chunk['text'][:100]}...")
        
        # Combine context
        context = "\n\n".join(context_parts)
        
        # Step 6: Generate AI response
        ai_response = await ai_processor.answer_question(
            query=request.query,
            context=context,
            conversation_history=conversation_history
        )
        
        if ai_response.get("answer_metadata", {}).get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorDetail(
                    message="AI processing failed",
                    code="AI_PROCESSING_FAILED",
                    details={"error": ai_response.get("answer_metadata", {}).get("error")}
                )
            )
        
        # Step 7: Generate follow-up suggestions
        follow_up_suggestions = await ai_processor.generate_follow_up_suggestions(context)
        
        # Step 8: Store conversation in database (if available)
        conversation_data = {"id": "mock_conversation_id"}
        if database_service:
            try:
                conversation_data = await database_service.create_conversation(
                    session_id=session_data["id"],
                    query=request.query,
                    answer=ai_response["answer"],
                    context_used=sources
                )
            except Exception as e:
                logger.warning(f"Failed to store conversation: {e}")
                conversation_data = {"id": f"failed_{int(time.time())}"}
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        # Create response
        response = ChatResponse(
            session_id=session_data["id"],
            answer=ai_response["answer"],
            query=request.query,
            conversation_id=conversation_data["id"],
            sources=sources,
            answer_metadata={
                "model": "gemini_2.5_flash",
                "response_length": len(ai_response["answer"]),
                "context_length": len(context),
                "sources_count": len(sources),
                "processing_time_ms": processing_time,
                "conversation_turns": len(conversation_history)
            },
            follow_up_suggestions=follow_up_suggestions[:5]  # Limit to 5 suggestions
        )
        
        logger.info(f"Successfully processed chat query in {processing_time}ms")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing chat query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                message="Internal server error during chat processing",
                code="INTERNAL_ERROR",
                details={"error": str(e)}
            )
        )
