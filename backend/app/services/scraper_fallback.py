"""
Fallback web scraper using Jina AI Reader API.
"""

import logging
from typing import Dict, Any, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class FallbackScraper:
    """Fallback scraper using Jina AI Reader API for JS-heavy sites."""
    
    def __init__(self):
        self.api_key = settings.jina_ai_api_key
        self.base_url = "https://r.jina.ai"
        self.timeout = settings.scraping_timeout
        
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Website Intelligence Bot/1.0"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape a URL using Jina AI Reader API.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dict containing scraped content and metadata
        """
        try:
            logger.info(f"Using fallback scraper for URL: {url}")
            
            # Jina AI Reader API endpoint
            api_url = f"{self.base_url}/{url}"
            
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers
            ) as client:
                response = await client.get(api_url)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract content from Jina response
                content = data.get("content", "")
                title = data.get("title", "")
                description = data.get("description", "")
                
                # Create structured content similar to primary scraper
                structured_content = {
                    "title": title,
                    "description": description,
                    "full_text": content,
                    "headings": self._extract_headings_from_markdown(content),
                    "paragraphs": self._split_into_paragraphs(content),
                    "lists": [],
                    "links": []
                }
                
                result = {
                    "success": True,
                    "url": url,
                    "status_code": response.status_code,
                    "scraping_method": "fallback",
                    "html_content": "",  # Jina returns markdown, not HTML
                    "structured_content": structured_content,
                    "full_text": content,
                    "fallback_decision": {"should_fallback": False, "reason": "Fallback scraper succeeded"},
                    "response_headers": dict(response.headers),
                    "scraped_at": response.headers.get("date", ""),
                    "content_length": len(content),
                    "text_length": len(content),
                    "jina_metadata": {
                        "title": title,
                        "description": description,
                        "raw_response": data
                    }
                }
                
                logger.info(f"Successfully scraped {url} with fallback: {len(content)} chars")
                return result
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout with fallback scraper for {url}")
            return self._create_error_result(url, "timeout", "Fallback scraper timed out")
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error with fallback scraper for {url}: {e.response.status_code}")
            return self._create_error_result(url, "http_error", f"HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            logger.warning(f"Request error with fallback scraper for {url}: {str(e)}")
            return self._create_error_result(url, "request_error", str(e))
        except Exception as e:
            logger.error(f"Unexpected error with fallback scraper for {url}: {str(e)}")
            return self._create_error_result(url, "unexpected_error", str(e))
    
    def _extract_headings_from_markdown(self, content: str) -> list[str]:
        """Extract headings from markdown content."""
        import re
        headings = []
        for line in content.split('\n'):
            if line.strip().startswith('#'):
                # Remove # symbols and clean
                heading = re.sub(r'^#+\s*', '', line.strip())
                if heading:
                    headings.append(heading)
        return headings
    
    def _split_into_paragraphs(self, content: str) -> list[str]:
        """Split content into paragraphs."""
        paragraphs = []
        for paragraph in content.split('\n\n'):
            paragraph = paragraph.strip()
            if paragraph and len(paragraph) > 20:  # Filter out very short paragraphs
                paragraphs.append(paragraph)
        return paragraphs
    
    def _create_error_result(self, url: str, error_type: str, error_message: str) -> Dict[str, Any]:
        """Create error result structure."""
        return {
            "success": False,
            "url": url,
            "error_type": error_type,
            "error_message": error_message,
            "scraping_method": "fallback",
            "fallback_decision": {"should_fallback": False, "reason": f"Fallback scraper failed: {error_message}"}
        }
    
    def is_available(self) -> bool:
        """Check if fallback scraper is available (has API key)."""
        return self.api_key is not None
