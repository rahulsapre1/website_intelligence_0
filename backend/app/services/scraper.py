"""
Primary web scraper using httpx + BeautifulSoup.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.utils.content_detector import ContentDetector
from app.utils.text_processor import TextProcessor

logger = logging.getLogger(__name__)


class WebScraper:
    """Primary web scraper using httpx and BeautifulSoup."""
    
    def __init__(self):
        self.timeout = settings.scraping_timeout
        self.content_detector = ContentDetector()
        self.text_processor = TextProcessor()
        
        # User agent to identify as a bot
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Website Intelligence Bot/1.0; +https://github.com/your-repo)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
    
    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape a URL and extract content.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dict containing scraped content and metadata
        """
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid URL: {url}")
            
            # Ensure HTTPS
            if parsed_url.scheme == 'http':
                url = url.replace('http://', 'https://', 1)
            
            logger.info(f"Scraping URL: {url}")
            
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
                follow_redirects=True,
                verify=True
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Extract content
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract structured content
                structured_content = self.text_processor.extract_structured_content(html_content)
                
                # Get full text for analysis
                full_text = structured_content["full_text"]
                
                # Check if fallback is needed
                fallback_decision = self.content_detector.should_use_fallback(html_content, full_text)
                
                result = {
                    "success": True,
                    "url": url,
                    "status_code": response.status_code,
                    "scraping_method": "primary",
                    "html_content": html_content,
                    "structured_content": structured_content,
                    "full_text": full_text,
                    "fallback_decision": fallback_decision,
                    "response_headers": dict(response.headers),
                    "scraped_at": response.headers.get("date", ""),
                    "content_length": len(html_content),
                    "text_length": len(full_text)
                }
                
                logger.info(f"Successfully scraped {url}: {len(full_text)} chars, fallback needed: {fallback_decision['should_fallback']}")
                return result
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout scraping {url}")
            return self._create_error_result(url, "timeout", "Request timed out")
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error scraping {url}: {e.response.status_code}")
            return self._create_error_result(url, "http_error", f"HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            logger.warning(f"Request error scraping {url}: {str(e)}")
            return self._create_error_result(url, "request_error", str(e))
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {str(e)}")
            return self._create_error_result(url, "unexpected_error", str(e))
    
    def _create_error_result(self, url: str, error_type: str, error_message: str) -> Dict[str, Any]:
        """Create error result structure."""
        return {
            "success": False,
            "url": url,
            "error_type": error_type,
            "error_message": error_message,
            "scraping_method": "primary",
            "fallback_decision": {"should_fallback": True, "reason": f"Primary scraper failed: {error_message}"}
        }
    
    async def scrape_multiple_urls(self, urls: list[str]) -> Dict[str, Any]:
        """
        Scrape multiple URLs concurrently.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            Dict with results for each URL
        """
        tasks = [self.scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "results": results,
            "total_urls": len(urls),
            "successful": sum(1 for r in results if isinstance(r, dict) and r.get("success", False)),
            "failed": sum(1 for r in results if isinstance(r, dict) and not r.get("success", False))
        }
