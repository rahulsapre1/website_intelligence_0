"""
Unit tests for AI processing functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.ai_processor import AIProcessor
from app.services.embeddings import EmbeddingService


class TestAIProcessor:
    """Test cases for AIProcessor."""
    
    @pytest.fixture
    def ai_processor(self):
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel'):
                return AIProcessor()
    
    @pytest.mark.asyncio
    async def test_extract_business_insights_success(self, ai_processor):
        """Test successful business insights extraction."""
        content = "We are a SaaS company providing AI-powered analytics to enterprises."
        mock_response = '{"industry": "SaaS", "company_size": "Medium", "location": "San Francisco"}'
        
        with patch.object(ai_processor, '_generate_response', return_value=mock_response):
            result = await ai_processor.extract_business_insights(content)
            
            assert "industry" in result
            assert result["industry"] == "SaaS"
            assert result["extraction_metadata"]["content_length"] == len(content)
    
    @pytest.mark.asyncio
    async def test_extract_business_insights_with_custom_questions(self, ai_processor):
        """Test business insights extraction with custom questions."""
        content = "We are a SaaS company providing AI-powered analytics to enterprises."
        questions = ["What is your pricing model?", "Who are your competitors?"]
        mock_response = '{"industry": "SaaS", "custom_answers": ["Subscription-based", "Not specified"]}'
        
        with patch.object(ai_processor, '_generate_response', return_value=mock_response):
            result = await ai_processor.extract_business_insights(content, questions)
            
            assert "custom_answers" in result
            assert len(result["custom_answers"]) == 2
    
    @pytest.mark.asyncio
    async def test_answer_question_success(self, ai_processor):
        """Test successful question answering."""
        query = "What does this company do?"
        context = "We are a SaaS company providing AI-powered analytics to enterprises."
        mock_response = "This company provides AI-powered analytics solutions to enterprises."
        
        with patch.object(ai_processor, '_generate_response', return_value=mock_response):
            result = await ai_processor.answer_question(query, context)
            
            assert result["answer"] == mock_response
            assert result["query"] == query
            assert result["context_length"] == len(context)
    
    @pytest.mark.asyncio
    async def test_answer_question_with_history(self, ai_processor):
        """Test question answering with conversation history."""
        query = "What about their pricing?"
        context = "We offer subscription plans starting at $99/month."
        history = [{"query": "What does this company do?", "answer": "They provide analytics."}]
        mock_response = "They offer subscription plans starting at $99/month."
        
        with patch.object(ai_processor, '_generate_response', return_value=mock_response):
            result = await ai_processor.answer_question(query, context, history)
            
            assert result["answer"] == mock_response
            assert result["conversation_turns"] == 1
    
    def test_parse_json_response_valid(self, ai_processor):
        """Test parsing valid JSON response."""
        response = '{"industry": "SaaS", "company_size": "Medium"}'
        result = ai_processor._parse_json_response(response)
        
        assert result["industry"] == "SaaS"
        assert result["company_size"] == "Medium"
    
    def test_parse_json_response_with_markers(self, ai_processor):
        """Test parsing JSON response with code markers."""
        response = '```json\n{"industry": "SaaS"}\n```'
        result = ai_processor._parse_json_response(response)
        
        assert result["industry"] == "SaaS"
    
    def test_parse_json_response_invalid(self, ai_processor):
        """Test parsing invalid JSON response."""
        response = "This is not JSON"
        result = ai_processor._parse_json_response(response)
        
        assert "error" in result
        assert result["confidence_score"] == 1


class TestEmbeddingService:
    """Test cases for EmbeddingService."""
    
    @pytest.fixture
    def embedding_service(self):
        with patch('google.generativeai.configure'):
            return EmbeddingService()
    
    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, embedding_service):
        """Test successful embedding generation."""
        text = "This is a test text for embedding."
        mock_embedding = [0.1, 0.2, 0.3] * 256  # 768 dimensions
        
        with patch.object(embedding_service, 'embedding_model', return_value={'embedding': mock_embedding}):
            result = await embedding_service.generate_embedding(text)
            
            assert len(result) == 768
            assert result == mock_embedding
    
    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, embedding_service):
        """Test embedding generation with empty text."""
        result = await embedding_service.generate_embedding("")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, embedding_service):
        """Test batch embedding generation."""
        texts = ["Text 1", "Text 2", "Text 3"]
        mock_embedding = [0.1, 0.2, 0.3] * 256
        
        with patch.object(embedding_service, 'generate_embedding', return_value=mock_embedding):
            result = await embedding_service.generate_embeddings_batch(texts)
            
            assert len(result) == 3
            assert all(len(emb) == 768 for emb in result)
    
    @pytest.mark.asyncio
    async def test_generate_chunk_embeddings(self, embedding_service):
        """Test embedding generation for text chunks."""
        chunks = [
            {"text": "Chunk 1", "chunk_type": "paragraph"},
            {"text": "Chunk 2", "chunk_type": "header"}
        ]
        mock_embedding = [0.1, 0.2, 0.3] * 256
        
        with patch.object(embedding_service, 'generate_embedding', return_value=mock_embedding):
            result = await embedding_service.generate_chunk_embeddings(chunks)
            
            assert len(result) == 2
            assert all("embedding" in chunk for chunk in result)
            assert all(len(chunk["embedding"]) == 768 for chunk in result)
    
    def test_get_embedding_dimensions(self, embedding_service):
        """Test getting embedding dimensions."""
        assert embedding_service.get_embedding_dimensions() == 768
