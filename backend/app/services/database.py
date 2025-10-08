"""
Database service for Supabase integration.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from supabase import create_client, Client
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database operations using Supabase."""
    
    def __init__(self):
        self.supabase_url = settings.supabase_url
        self.supabase_key = settings.supabase_key
        
        # Initialize Supabase client
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        logger.info("Database service initialized")
    
    async def create_analysis_session(
        self, 
        url: str, 
        scraped_content: str, 
        scraping_method: str,
        insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new analysis session.
        
        Args:
            url: Website URL
            scraped_content: Scraped content
            scraping_method: 'primary' or 'fallback'
            insights: Extracted insights
            
        Returns:
            Created session data
        """
        try:
            session_data = {
                "id": str(uuid.uuid4()),
                "url": url,
                "scraped_content": scraped_content,
                "scraping_method": scraping_method,
                "insights": insights,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("analysis_sessions").insert(session_data).execute()
            
            if result.data:
                logger.info(f"Created analysis session for {url}")
                return result.data[0]
            else:
                raise Exception("Failed to create analysis session")
                
        except Exception as e:
            logger.error(f"Error creating analysis session: {str(e)}")
            raise
    
    async def get_analysis_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analysis session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None
        """
        try:
            result = self.client.table("analysis_sessions").select("*").eq("id", session_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting analysis session: {str(e)}")
            return None
    
    async def get_analysis_session_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get most recent analysis session by URL.
        
        Args:
            url: Website URL
            
        Returns:
            Session data or None
        """
        try:
            result = (
                self.client.table("analysis_sessions")
                .select("*")
                .eq("url", url)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting analysis session by URL: {str(e)}")
            return None
    
    async def update_analysis_session(
        self, 
        session_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update analysis session.
        
        Args:
            session_id: Session ID
            updates: Fields to update
            
        Returns:
            Updated session data or None
        """
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = (
                self.client.table("analysis_sessions")
                .update(updates)
                .eq("id", session_id)
                .execute()
            )
            
            if result.data:
                logger.info(f"Updated analysis session {session_id}")
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error updating analysis session: {str(e)}")
            return None
    
    async def create_conversation(
        self, 
        session_id: str, 
        query: str, 
        answer: str,
        context_used: List[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new conversation entry.
        
        Args:
            session_id: Analysis session ID
            query: User query
            answer: AI answer
            context_used: List of context chunks used
            
        Returns:
            Created conversation data
        """
        try:
            conversation_data = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "query": query,
                "answer": answer,
                "context_used": context_used or [],
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("conversations").insert(conversation_data).execute()
            
            if result.data:
                logger.info(f"Created conversation for session {session_id}")
                return result.data[0]
            else:
                raise Exception("Failed to create conversation")
                
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Analysis session ID
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation data
        """
        try:
            result = (
                self.client.table("conversations")
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            # Reverse to get chronological order
            conversations = result.data or []
            conversations.reverse()
            
            logger.debug(f"Retrieved {len(conversations)} conversations for session {session_id}")
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    async def check_recent_analysis(self, url: str, hours: int = 1) -> Optional[Dict[str, Any]]:
        """
        Check if URL was analyzed recently.
        
        Args:
            url: Website URL
            hours: Hours to look back
            
        Returns:
            Recent session data or None
        """
        try:
            from datetime import timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            result = (
                self.client.table("analysis_sessions")
                .select("*")
                .eq("url", url)
                .gte("created_at", cutoff_time.isoformat())
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            
            if result.data:
                logger.info(f"Found recent analysis for {url} within {hours} hours")
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error checking recent analysis: {str(e)}")
            return None
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            # Get session count
            sessions_result = self.client.table("analysis_sessions").select("id", count="exact").execute()
            session_count = sessions_result.count or 0
            
            # Get conversation count
            conversations_result = self.client.table("conversations").select("id", count="exact").execute()
            conversation_count = conversations_result.count or 0
            
            # Get recent activity (last 24 hours)
            from datetime import timedelta
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            
            recent_sessions_result = (
                self.client.table("analysis_sessions")
                .select("id", count="exact")
                .gte("created_at", recent_cutoff.isoformat())
                .execute()
            )
            recent_sessions = recent_sessions_result.count or 0
            
            return {
                "total_sessions": session_count,
                "total_conversations": conversation_count,
                "recent_sessions_24h": recent_sessions,
                "database_status": "connected"
            }
            
        except Exception as e:
            logger.error(f"Error getting session stats: {str(e)}")
            return {
                "total_sessions": 0,
                "total_conversations": 0,
                "recent_sessions_24h": 0,
                "database_status": "error",
                "error": str(e)
            }
