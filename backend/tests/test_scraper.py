"""
Unit tests for web scraping functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.scraper import WebScraper
from app.services.scraper_fallback import FallbackScraper
from app.utils.content_detector import ContentDetector


class TestWebScraper:
    """Test cases for WebScraper."""
    
    @pytest.fixture
    def scraper(self):
        return WebScraper()
    
    @pytest.mark.asyncio
    async def test_scrape_url_success(self, scraper):
        """Test successful URL scraping."""
        mock_html = "<html><body><h1>Test Company</h1><p>We provide amazing services.</p></body></html>"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.text = mock_html
            mock_response.status_code = 200
            mock_response.headers = {"date": "2025-01-08T10:00:00Z"}
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await scraper.scrape_url("https://example.com")
            
            assert result["success"] is True
            assert result["url"] == "https://example.com"
            assert result["scraping_method"] == "primary"
            assert "Test Company" in result["full_text"]
    
    @pytest.mark.asyncio
    async def test_scrape_url_timeout(self, scraper):
        """Test URL scraping timeout."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Timeout")
            
            result = await scraper.scrape_url("https://example.com")
            
            assert result["success"] is False
            assert result["error_type"] == "unexpected_error"
    
    @pytest.mark.asyncio
    async def test_scrape_url_http_error(self, scraper):
        """Test URL scraping with HTTP error."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = Exception("404 Not Found")
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await scraper.scrape_url("https://example.com")
            
            assert result["success"] is False
            assert result["error_type"] == "unexpected_error"


class TestFallbackScraper:
    """Test cases for FallbackScraper."""
    
    @pytest.fixture
    def fallback_scraper(self):
        return FallbackScraper()
    
    @pytest.mark.asyncio
    async def test_scrape_url_success(self, fallback_scraper):
        """Test successful fallback scraping."""
        mock_response_data = {
            "content": "# Test Company\n\nWe provide amazing services.",
            "title": "Test Company",
            "description": "Amazing services company"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_data
            mock_response.status_code = 200
            mock_response.headers = {"date": "2025-01-08T10:00:00Z"}
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await fallback_scraper.scrape_url("https://example.com")
            
            assert result["success"] is True
            assert result["url"] == "https://example.com"
            assert result["scraping_method"] == "fallback"
            assert "Test Company" in result["full_text"]
    
    def test_is_available_with_key(self, fallback_scraper):
        """Test availability check with API key."""
        fallback_scraper.api_key = "test_key"
        assert fallback_scraper.is_available() is True
    
    def test_is_available_without_key(self, fallback_scraper):
        """Test availability check without API key."""
        fallback_scraper.api_key = None
        assert fallback_scraper.is_available() is False


class TestContentDetector:
    """Test cases for ContentDetector."""
    
    @pytest.fixture
    def detector(self):
        return ContentDetector()
    
    def test_should_use_fallback_insufficient_content(self, detector):
        """Test fallback decision for insufficient content."""
        html = "<html><body><script>console.log('test');</script></body></html>"
        text = "test"
        
        result = detector.should_use_fallback(html, text)
        
        assert result["should_fallback"] is True
        assert "Text too short" in result["reason"]
    
    def test_should_use_fallback_low_ratio(self, detector):
        """Test fallback decision for low text ratio."""
        html = "<html><body>" + "x" * 10000 + "</body></html>"
        text = "short"
        
        result = detector.should_use_fallback(html, text)
        
        assert result["should_fallback"] is True
        assert "Low text ratio" in result["reason"]
    
    def test_should_not_use_fallback_good_content(self, detector):
        """Test no fallback for good content."""
        html = "<html><body><h1>Company</h1><p>We provide amazing services to our customers.</p></body></html>"
        text = "Company We provide amazing services to our customers."
        
        result = detector.should_use_fallback(html, text)
        
        assert result["should_fallback"] is False
        assert "sufficient" in result["reason"]
    
    def test_has_only_scripts(self, detector):
        """Test detection of script-only content."""
        html = "<html><head><script>var x = 1;</script></head><body><script>console.log(x);</script></body></html>"
        
        assert detector._has_only_scripts(html) is True
