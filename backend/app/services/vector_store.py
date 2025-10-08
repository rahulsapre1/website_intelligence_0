"""
Vector store service for Qdrant integration.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for vector operations using Qdrant."""
    
    def __init__(self):
        self.qdrant_url = settings.qdrant_url
        self.qdrant_api_key = settings.qdrant_api_key
        
        # Initialize Qdrant client
        self.client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key
        )
        
        self.collection_name = "website_content"
        self.vector_size = 768  # Gemini text-embedding-004 dimensions
        
        logger.info("Vector store service initialized")
    
    async def create_collection(self) -> bool:
        """
        Create the vector collection if it doesn't exist.
        
        Returns:
            True if collection exists or was created
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name in collection_names:
                logger.info(f"Collection {self.collection_name} already exists")
                return True
            
            # Create collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"Created collection {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            return False
    
    async def add_document_chunks(
        self, 
        session_id: str, 
        url: str, 
        chunks: List[Dict[str, Any]]
    ) -> bool:
        """
        Add document chunks to the vector store.
        
        Args:
            session_id: Analysis session ID
            url: Website URL
            chunks: List of text chunks with embeddings
            
        Returns:
            True if successful
        """
        try:
            # Ensure collection exists
            await self.create_collection()
            
            # Prepare points for insertion
            points = []
            for i, chunk in enumerate(chunks):
                if not chunk.get('embedding'):
                    logger.warning(f"Chunk {i} has no embedding, skipping")
                    continue
                
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=chunk['embedding'],
                    payload={
                        "session_id": session_id,
                        "url": url,
                        "text_chunk": chunk['text'],
                        "chunk_type": chunk.get('chunk_type', 'paragraph'),
                        "chunk_index": chunk.get('chunk_index', i),
                        "scraped_at": datetime.utcnow().isoformat(),
                        "text_length": len(chunk['text'])
                    }
                )
                points.append(point)
            
            if not points:
                logger.warning("No valid chunks to add to vector store")
                return False
            
            # Insert points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added {len(points)} chunks to vector store for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document chunks: {str(e)}")
            return False
    
    async def search_similar_chunks(
        self, 
        query_embedding: List[float], 
        session_id: str = None,
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            session_id: Optional session ID to filter by
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar chunks with metadata
        """
        try:
            # Build filter
            filter_condition = None
            if session_id:
                filter_condition = Filter(
                    must=[
                        FieldCondition(
                            key="session_id",
                            match=MatchValue(value=session_id)
                        )
                    ]
                )
            
            # Search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=filter_condition,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            results = []
            for hit in search_result:
                results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "text": hit.payload.get("text_chunk", ""),
                    "chunk_type": hit.payload.get("chunk_type", ""),
                    "session_id": hit.payload.get("session_id", ""),
                    "url": hit.payload.get("url", ""),
                    "chunk_index": hit.payload.get("chunk_index", 0),
                    "text_length": hit.payload.get("text_length", 0)
                })
            
            logger.debug(f"Found {len(results)} similar chunks")
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            return []
    
    async def get_session_chunks(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific session.
        
        Args:
            session_id: Analysis session ID
            
        Returns:
            List of chunks for the session
        """
        try:
            # Search with session filter
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="session_id",
                            match=MatchValue(value=session_id)
                        )
                    ]
                ),
                limit=1000  # Adjust based on expected chunk count
            )
            
            # Format results
            chunks = []
            for point in search_result[0]:  # scroll returns (points, next_page_offset)
                chunks.append({
                    "id": point.id,
                    "text": point.payload.get("text_chunk", ""),
                    "chunk_type": point.payload.get("chunk_type", ""),
                    "chunk_index": point.payload.get("chunk_index", 0),
                    "text_length": point.payload.get("text_length", 0),
                    "scraped_at": point.payload.get("scraped_at", "")
                })
            
            # Sort by chunk index
            chunks.sort(key=lambda x: x.get("chunk_index", 0))
            
            logger.debug(f"Retrieved {len(chunks)} chunks for session {session_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error getting session chunks: {str(e)}")
            return []
    
    async def delete_session_chunks(self, session_id: str) -> bool:
        """
        Delete all chunks for a specific session.
        
        Args:
            session_id: Analysis session ID
            
        Returns:
            True if successful
        """
        try:
            # Get all points for the session
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="session_id",
                            match=MatchValue(value=session_id)
                        )
                    ]
                ),
                limit=1000
            )
            
            if not search_result[0]:
                logger.info(f"No chunks found for session {session_id}")
                return True
            
            # Extract point IDs
            point_ids = [point.id for point in search_result[0]]
            
            # Delete points
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids
            )
            
            logger.info(f"Deleted {len(point_ids)} chunks for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session chunks: {str(e)}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            # Get collection info
            collection_info = self.client.get_collection(self.collection_name)
            
            # Get point count
            count_result = self.client.count(self.collection_name)
            
            return {
                "collection_name": self.collection_name,
                "vector_size": self.vector_size,
                "points_count": count_result.count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "status": "connected"
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {
                "collection_name": self.collection_name,
                "vector_size": self.vector_size,
                "points_count": 0,
                "indexed_vectors_count": 0,
                "status": "error",
                "error": str(e)
            }
