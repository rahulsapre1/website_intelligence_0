"""
Caching service for improved performance and reduced API costs.
"""

import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from app.core.config import settings
from app.utils.logger import api_logger


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    data: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = None


class MemoryCache:
    """In-memory cache with TTL and size limits."""
    
    def __init__(self, max_size: int = 1000, default_ttl_seconds: int = 3600):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, prefix: str, *args) -> str:
        """Generate cache key from arguments."""
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > entry.expires_at
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self.cache.items()
            if self._is_expired(entry)
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self.cache:
            return
        
        lru_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].last_accessed or self.cache[k].created_at
        )
        del self.cache[lru_key]
    
    def get(self, prefix: str, *args) -> Optional[Any]:
        """Get cached data."""
        key = self._generate_key(prefix, *args)
        
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        if self._is_expired(entry):
            del self.cache[key]
            self.misses += 1
            return None
        
        # Update access info
        entry.access_count += 1
        entry.last_accessed = datetime.utcnow()
        self.hits += 1
        
        return entry.data
    
    def set(self, prefix: str, data: Any, ttl_seconds: Optional[int] = None, *args):
        """Set cached data."""
        key = self._generate_key(prefix, *args)
        ttl = ttl_seconds or self.default_ttl_seconds
        
        # Cleanup if needed
        self._cleanup_expired()
        
        # Evict if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_lru()
        
        # Create cache entry
        now = datetime.utcnow()
        entry = CacheEntry(
            data=data,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl),
            access_count=0,
            last_accessed=now
        )
        
        self.cache[key] = entry
    
    def delete(self, prefix: str, *args) -> bool:
        """Delete cached data."""
        key = self._generate_key(prefix, *args)
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self):
        """Clear all cached data."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
            "expired_entries": len([e for e in self.cache.values() if self._is_expired(e)])
        }


class CacheService:
    """High-level caching service for the application."""
    
    def __init__(self):
        self.cache = MemoryCache(max_size=1000, default_ttl_seconds=3600)
        
        # Different TTLs for different types of data
        self.ttls = {
            "scraped_content": 1800,  # 30 minutes
            "ai_insights": 3600,      # 1 hour
            "embeddings": 7200,       # 2 hours
            "analysis_results": 1800, # 30 minutes
            "chat_responses": 300,    # 5 minutes
        }
    
    def get_scraped_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached scraped content."""
        return self.cache.get("scraped_content", url)
    
    def set_scraped_content(self, url: str, content: Dict[str, Any]):
        """Cache scraped content."""
        self.cache.set("scraped_content", content, self.ttls["scraped_content"], url)
        api_logger.debug("Cached scraped content", url=url, content_length=len(str(content)))
    
    def get_ai_insights(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached AI insights."""
        return self.cache.get("ai_insights", content_hash)
    
    def set_ai_insights(self, content_hash: str, insights: Dict[str, Any]):
        """Cache AI insights."""
        self.cache.set("ai_insights", insights, self.ttls["ai_insights"], content_hash)
        api_logger.debug("Cached AI insights", content_hash=content_hash)
    
    def get_embeddings(self, text_hash: str) -> Optional[list]:
        """Get cached embeddings."""
        return self.cache.get("embeddings", text_hash)
    
    def set_embeddings(self, text_hash: str, embeddings: list):
        """Cache embeddings."""
        self.cache.set("embeddings", embeddings, self.ttls["embeddings"], text_hash)
        api_logger.debug("Cached embeddings", text_hash=text_hash, dimensions=len(embeddings))
    
    def get_analysis_result(self, url: str, questions_hash: str = "") -> Optional[Dict[str, Any]]:
        """Get cached analysis result."""
        return self.cache.get("analysis_results", url, questions_hash)
    
    def set_analysis_result(self, url: str, result: Dict[str, Any], questions_hash: str = ""):
        """Cache analysis result."""
        self.cache.set("analysis_results", result, self.ttls["analysis_results"], url, questions_hash)
        api_logger.debug("Cached analysis result", url=url, questions_hash=questions_hash)
    
    def get_chat_response(self, query_hash: str, context_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached chat response."""
        return self.cache.get("chat_responses", query_hash, context_hash)
    
    def set_chat_response(self, query_hash: str, context_hash: str, response: Dict[str, Any]):
        """Cache chat response."""
        self.cache.set("chat_responses", response, self.ttls["chat_responses"], query_hash, context_hash)
        api_logger.debug("Cached chat response", query_hash=query_hash, context_hash=context_hash)
    
    def invalidate_url(self, url: str):
        """Invalidate all cache entries for a URL."""
        # This is a simplified invalidation - in production, you might want more sophisticated logic
        patterns = ["scraped_content", "analysis_results"]
        for pattern in patterns:
            self.cache.delete(pattern, url)
        api_logger.info("Invalidated cache for URL", url=url)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()
    
    def clear_all(self):
        """Clear all cached data."""
        self.cache.clear()
        api_logger.info("Cleared all cache data")


# Global cache service instance
cache_service = CacheService()
