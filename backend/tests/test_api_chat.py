"""
Integration tests for chat API endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)


class TestChatEndpoint:
    """Test cases for /api/v1/chat endpoint."""
    
    def test_chat_without_auth(self):
        """Test chat endpoint without authentication."""
        response = client.post("/api/v1/chat", json={
            "query": "What does this company do?",
            "session_id": "test-session-id"
        })
        
        assert response.status_code == 401
    
    @patch('app.services.database.DatabaseService.get_analysis_session')
    @patch('app.services.ai_processor.AIProcessor.answer_question')
    @patch('app.services.database.DatabaseService.create_conversation')
    def test_chat_with_session_id(self, mock_create_conv, mock_ai, mock_db):
        """Test chat with session ID."""
        # Mock database response
        mock_db.return_value = {
            "id": "test-session-id",
            "url": "https://example.com",
            "scraped_content": "We are a SaaS company providing analytics."
        }
        
        # Mock AI response
        mock_ai.return_value = {
            "answer": "This company provides SaaS analytics solutions.",
            "query": "What does this company do?",
            "context_length": 50,
            "conversation_turns": 0,
            "answer_metadata": {"model": "gemini_2.5_flash"}
        }
        
        # Mock conversation creation
        mock_create_conv.return_value = {
            "id": "conv-123",
            "session_id": "test-session-id",
            "query": "What does this company do?",
            "answer": "This company provides SaaS analytics solutions."
        }
        
        # Mock vector search
        with patch('app.services.vector_store.VectorStoreService.search_similar_chunks') as mock_vector:
            with patch('app.services.embeddings.EmbeddingService.generate_embedding') as mock_embed:
                mock_vector.return_value = []
                mock_embed.return_value = [0.1, 0.2, 0.3] * 256
                
                response = client.post(
                    "/api/v1/chat",
                    json={
                        "query": "What does this company do?",
                        "session_id": "test-session-id"
                    },
                    headers={"Authorization": "Bearer dev_secret_key_123"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["answer"] == "This company provides SaaS analytics solutions."
                assert data["session_id"] == "test-session-id"
                assert data["conversation_id"] == "conv-123"
    
    @patch('app.services.database.DatabaseService.get_analysis_session_by_url')
    @patch('app.services.ai_processor.AIProcessor.answer_question')
    @patch('app.services.database.DatabaseService.create_conversation')
    def test_chat_with_url(self, mock_create_conv, mock_ai, mock_db):
        """Test chat with URL instead of session ID."""
        # Mock database response
        mock_db.return_value = {
            "id": "test-session-id",
            "url": "https://example.com",
            "scraped_content": "We are a SaaS company providing analytics."
        }
        
        # Mock AI response
        mock_ai.return_value = {
            "answer": "This company provides SaaS analytics solutions.",
            "query": "What does this company do?",
            "context_length": 50,
            "conversation_turns": 0,
            "answer_metadata": {"model": "gemini_2.5_flash"}
        }
        
        # Mock conversation creation
        mock_create_conv.return_value = {
            "id": "conv-123",
            "session_id": "test-session-id",
            "query": "What does this company do?",
            "answer": "This company provides SaaS analytics solutions."
        }
        
        # Mock vector search
        with patch('app.services.vector_store.VectorStoreService.search_similar_chunks') as mock_vector:
            with patch('app.services.embeddings.EmbeddingService.generate_embedding') as mock_embed:
                mock_vector.return_value = []
                mock_embed.return_value = [0.1, 0.2, 0.3] * 256
                
                response = client.post(
                    "/api/v1/chat",
                    json={
                        "query": "What does this company do?",
                        "url": "https://example.com"
                    },
                    headers={"Authorization": "Bearer dev_secret_key_123"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["answer"] == "This company provides SaaS analytics solutions."
    
    def test_chat_session_not_found(self):
        """Test chat with non-existent session."""
        with patch('app.services.database.DatabaseService.get_analysis_session') as mock_db:
            mock_db.return_value = None
            
            response = client.post(
                "/api/v1/chat",
                json={
                    "query": "What does this company do?",
                    "session_id": "non-existent-session"
                },
                headers={"Authorization": "Bearer dev_secret_key_123"}
            )
            
            assert response.status_code == 404
            data = response.json()
            assert data["error"]["code"] == "SESSION_NOT_FOUND"
    
    def test_chat_invalid_query(self):
        """Test chat with invalid query."""
        response = client.post(
            "/api/v1/chat",
            json={
                "query": "Hi",  # Too short
                "session_id": "test-session-id"
            },
            headers={"Authorization": "Bearer dev_secret_key_123"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.services.database.DatabaseService.get_analysis_session')
    @patch('app.services.database.DatabaseService.get_conversation_history')
    @patch('app.services.ai_processor.AIProcessor.answer_question')
    @patch('app.services.database.DatabaseService.create_conversation')
    def test_chat_with_conversation_history(self, mock_create_conv, mock_ai, mock_conv_history, mock_db):
        """Test chat with conversation history."""
        # Mock database response
        mock_db.return_value = {
            "id": "test-session-id",
            "url": "https://example.com",
            "scraped_content": "We are a SaaS company providing analytics."
        }
        
        # Mock conversation history
        mock_conv_history.return_value = [
            {"query": "What does this company do?", "answer": "They provide analytics."}
        ]
        
        # Mock AI response
        mock_ai.return_value = {
            "answer": "They offer subscription plans starting at $99/month.",
            "query": "What about their pricing?",
            "context_length": 50,
            "conversation_turns": 1,
            "answer_metadata": {"model": "gemini_2.5_flash"}
        }
        
        # Mock conversation creation
        mock_create_conv.return_value = {
            "id": "conv-123",
            "session_id": "test-session-id",
            "query": "What about their pricing?",
            "answer": "They offer subscription plans starting at $99/month."
        }
        
        # Mock vector search
        with patch('app.services.vector_store.VectorStoreService.search_similar_chunks') as mock_vector:
            with patch('app.services.embeddings.EmbeddingService.generate_embedding') as mock_embed:
                mock_vector.return_value = []
                mock_embed.return_value = [0.1, 0.2, 0.3] * 256
                
                response = client.post(
                    "/api/v1/chat",
                    json={
                        "query": "What about their pricing?",
                        "session_id": "test-session-id"
                    },
                    headers={"Authorization": "Bearer dev_secret_key_123"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["answer"] == "They offer subscription plans starting at $99/month."
                # Verify conversation history was passed to AI
                mock_ai.assert_called_once()
                call_args = mock_ai.call_args
                assert call_args[1]["conversation_history"] == [{"query": "What does this company do?", "answer": "They provide analytics."}]
