"""
Integration tests for analyze API endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)


class TestAnalyzeEndpoint:
    """Test cases for /api/v1/analyze endpoint."""
    
    def test_analyze_without_auth(self):
        """Test analyze endpoint without authentication."""
        response = client.post("/api/v1/analyze", json={"url": "https://example.com"})
        
        assert response.status_code == 401
    
    @patch('app.services.scraper.WebScraper.scrape_url')
    @patch('app.services.ai_processor.AIProcessor.extract_business_insights')
    @patch('app.services.database.DatabaseService.create_analysis_session')
    @patch('app.services.vector_store.VectorStoreService.add_document_chunks')
    def test_analyze_success(self, mock_vector_store, mock_db, mock_ai, mock_scraper):
        """Test successful website analysis."""
        # Mock responses
        mock_scraper.return_value = {
            "success": True,
            "url": "https://example.com",
            "scraping_method": "primary",
            "html_content": "<html>Test content</html>",
            "full_text": "Test company provides amazing services",
            "scraped_at": "2025-01-08T10:00:00Z"
        }
        
        mock_ai.return_value = {
            "industry": "SaaS",
            "company_size": "Medium",
            "location": "San Francisco",
            "usp": "Amazing services",
            "products_services": ["Analytics"],
            "target_audience": "Enterprises",
            "contact_info": {"email": "test@example.com"},
            "confidence_score": 8
        }
        
        mock_db.return_value = {
            "id": "test-session-id",
            "url": "https://example.com",
            "created_at": "2025-01-08T10:00:00Z"
        }
        
        mock_vector_store.return_value = True
        
        # Test request
        response = client.post(
            "/api/v1/analyze",
            json={"url": "https://example.com"},
            headers={"Authorization": "Bearer dev_secret_key_123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["url"] == "https://example.com"
        assert data["insights"]["industry"] == "SaaS"
        assert data["session_id"] == "test-session-id"
    
    @patch('app.services.scraper.WebScraper.scrape_url')
    @patch('app.services.scraper_fallback.FallbackScraper.scrape_url')
    def test_analyze_with_fallback(self, mock_fallback, mock_scraper):
        """Test analysis with fallback scraper."""
        # Mock primary scraper failure
        mock_scraper.return_value = {
            "success": False,
            "error_type": "timeout",
            "error_message": "Request timed out"
        }
        
        # Mock fallback scraper success
        mock_fallback.return_value = {
            "success": True,
            "url": "https://example.com",
            "scraping_method": "fallback",
            "html_content": "",
            "full_text": "Test company provides amazing services",
            "scraped_at": "2025-01-08T10:00:00Z"
        }
        
        with patch('app.services.ai_processor.AIProcessor.extract_business_insights') as mock_ai:
            with patch('app.services.database.DatabaseService.create_analysis_session') as mock_db:
                with patch('app.services.vector_store.VectorStoreService.add_document_chunks') as mock_vector:
                    mock_ai.return_value = {"industry": "SaaS", "company_size": "Medium"}
                    mock_db.return_value = {"id": "test-session-id", "url": "https://example.com"}
                    mock_vector.return_value = True
                    
                    response = client.post(
                        "/api/v1/analyze",
                        json={"url": "https://example.com"},
                        headers={"Authorization": "Bearer dev_secret_key_123"}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["fallback_used"] is True
    
    def test_analyze_invalid_url(self):
        """Test analysis with invalid URL."""
        response = client.post(
            "/api/v1/analyze",
            json={"url": "not-a-url"},
            headers={"Authorization": "Bearer dev_secret_key_123"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_analyze_with_custom_questions(self):
        """Test analysis with custom questions."""
        with patch('app.services.scraper.WebScraper.scrape_url') as mock_scraper:
            with patch('app.services.ai_processor.AIProcessor.extract_business_insights') as mock_ai:
                with patch('app.services.database.DatabaseService.create_analysis_session') as mock_db:
                    with patch('app.services.vector_store.VectorStoreService.add_document_chunks') as mock_vector:
                        mock_scraper.return_value = {
                            "success": True,
                            "url": "https://example.com",
                            "scraping_method": "primary",
                            "html_content": "<html>Test</html>",
                            "full_text": "Test company",
                            "scraped_at": "2025-01-08T10:00:00Z"
                        }
                        
                        mock_ai.return_value = {
                            "industry": "SaaS",
                            "company_size": "Medium",
                            "custom_answers": ["Subscription-based", "Not specified"]
                        }
                        
                        mock_db.return_value = {"id": "test-session-id", "url": "https://example.com"}
                        mock_vector.return_value = True
                        
                        response = client.post(
                            "/api/v1/analyze",
                            json={
                                "url": "https://example.com",
                                "questions": ["What is your pricing model?", "Who are your competitors?"]
                            },
                            headers={"Authorization": "Bearer dev_secret_key_123"}
                        )
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["custom_answers"] == ["Subscription-based", "Not specified"]
    
    @patch('app.services.database.DatabaseService.check_recent_analysis')
    def test_analyze_cached_result(self, mock_recent):
        """Test analysis with cached result."""
        mock_recent.return_value = {
            "id": "cached-session-id",
            "url": "https://example.com",
            "created_at": "2025-01-08T10:00:00Z",
            "scraping_method": "primary",
            "scraped_content": "<html>Test</html>",
            "insights": {
                "industry": "SaaS",
                "company_size": "Medium",
                "location": "San Francisco",
                "usp": "Amazing services",
                "products_services": ["Analytics"],
                "target_audience": "Enterprises",
                "contact_info": {"email": "test@example.com"},
                "confidence_score": 8
            }
        }
        
        response = client.post(
            "/api/v1/analyze",
            json={"url": "https://example.com"},
            headers={"Authorization": "Bearer dev_secret_key_123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "cached-session-id"
        assert data["extraction_metadata"]["extraction_method"] == "cached"
