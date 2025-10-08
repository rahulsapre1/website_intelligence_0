"""
Embedding service using Gemini text-embedding-004.
"""

import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Gemini."""
    
    def __init__(self):
        self.api_key = settings.gemini_api_key
        genai.configure(api_key=self.api_key)
        
        # Initialize embedding model
        self.embedding_model = genai.embed_content
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return []
            
            # Generate embedding
            result = self.embedding_model(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            
            if result and 'embedding' in result:
                logger.debug(f"Generated embedding with {len(result['embedding'])} dimensions")
                return result['embedding']
            else:
                logger.error("No embedding returned from Gemini")
                return []
                
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return []
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        try:
            if not texts:
                return []
            
            logger.info(f"Generating embeddings for {len(texts)} texts")
            
            # Process texts in batches to avoid rate limits
            batch_size = 10
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = []
                
                for text in batch:
                    embedding = await self.generate_embedding(text)
                    batch_embeddings.append(embedding)
                
                all_embeddings.extend(batch_embeddings)
                
                # Small delay between batches
                if i + batch_size < len(texts):
                    import asyncio
                    await asyncio.sleep(0.1)
            
            logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            return []
    
    async def generate_chunk_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for text chunks.
        
        Args:
            chunks: List of chunk dictionaries with 'text' field
            
        Returns:
            List of chunks with added 'embedding' field
        """
        try:
            if not chunks:
                return []
            
            # Extract texts
            texts = [chunk.get('text', '') for chunk in chunks]
            
            # Generate embeddings
            embeddings = await self.generate_embeddings_batch(texts)
            
            # Add embeddings to chunks
            result_chunks = []
            for i, chunk in enumerate(chunks):
                chunk_copy = chunk.copy()
                chunk_copy['embedding'] = embeddings[i] if i < len(embeddings) else []
                result_chunks.append(chunk_copy)
            
            logger.info(f"Added embeddings to {len(result_chunks)} chunks")
            return result_chunks
            
        except Exception as e:
            logger.error(f"Error generating chunk embeddings: {str(e)}")
            return chunks  # Return original chunks without embeddings
    
    def get_embedding_dimensions(self) -> int:
        """Get the number of dimensions for Gemini embeddings."""
        return 768  # Gemini text-embedding-004 has 768 dimensions
    
    async def similarity_search(
        self, 
        query_embedding: List[float], 
        document_embeddings: List[List[float]], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find most similar documents using cosine similarity.
        
        Args:
            query_embedding: Query embedding
            document_embeddings: List of document embeddings
            top_k: Number of top results to return
            
        Returns:
            List of similar documents with scores
        """
        try:
            if not query_embedding or not document_embeddings:
                return []
            
            import numpy as np
            
            # Convert to numpy arrays
            query_vec = np.array(query_embedding)
            doc_vectors = np.array(document_embeddings)
            
            # Calculate cosine similarities
            similarities = np.dot(doc_vectors, query_vec) / (
                np.linalg.norm(doc_vectors, axis=1) * np.linalg.norm(query_vec)
            )
            
            # Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # Create results
            results = []
            for idx in top_indices:
                results.append({
                    "index": int(idx),
                    "similarity": float(similarities[idx]),
                    "embedding": document_embeddings[idx].tolist()
                })
            
            logger.debug(f"Found {len(results)} similar documents")
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []
