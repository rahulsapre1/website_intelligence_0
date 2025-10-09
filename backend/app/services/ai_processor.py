"""
AI processing service using Google Gemini 2.5 Flash.
"""

import json
import logging
from typing import Dict, Any, List, Optional
import google.generativeai as genai

from app.core.config import settings
from app.prompts.extraction import ExtractionPrompts
from app.prompts.conversation import ConversationPrompts

logger = logging.getLogger(__name__)


class AIProcessor:
    """AI processing service using Gemini 2.5 Flash."""
    
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.mock_mode = not bool(self.api_key)
        
        if not self.mock_mode:
            genai.configure(api_key=self.api_key)
            # Initialize Gemini model
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            logger.warning("AIProcessor initialized in mock mode - no API key provided")
            self.model = None
        
        # Configure generation parameters
        self.generation_config = {
            "temperature": 0.1,  # Low temperature for consistent extraction
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 4096,
        }
    
    async def extract_business_insights(
        self, 
        content: str, 
        custom_questions: List[str] = None
    ) -> Dict[str, Any]:
        """
        Extract business insights from website content.
        
        Args:
            content: Website content to analyze
            custom_questions: Optional custom questions to answer
            
        Returns:
            Dict containing extracted insights
        """
        try:
            logger.info(f"Extracting business insights from {len(content)} characters of content")
            
            # Return mock data if in mock mode
            if self.mock_mode:
                logger.info("Returning mock insights - API key not configured")
                return self._get_mock_insights(content, custom_questions)
            
            # Generate prompt
            prompt = ExtractionPrompts.get_core_insights_prompt(content, custom_questions)
            
            # Generate response
            response = await self._generate_response(prompt)
            
            # Parse JSON response
            insights = self._parse_json_response(response)
            
            # Add metadata
            insights["extraction_metadata"] = {
                "content_length": len(content),
                "custom_questions_count": len(custom_questions) if custom_questions else 0,
                "extraction_method": "gemini_2.5_flash",
                "confidence": insights.get("confidence_score", "Not provided")
            }
            
            logger.info(f"Successfully extracted insights with confidence: {insights.get('confidence_score', 'N/A')}")
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting business insights: {str(e)}")
            return self._create_error_response("extraction_failed", str(e))
    
    async def answer_question(
        self, 
        query: str, 
        context: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Answer a question based on website content.
        
        Args:
            query: User's question
            context: Website content context
            conversation_history: Previous conversation turns
            
        Returns:
            Dict containing answer and metadata
        """
        try:
            logger.info(f"Answering question: {query[:100]}...")
            
            # Generate prompt
            prompt = ConversationPrompts.get_chat_prompt(query, context, conversation_history)
            
            # Generate response
            response = await self._generate_response(prompt)
            
            # Create response structure
            answer = {
                "answer": response,
                "query": query,
                "context_length": len(context),
                "conversation_turns": len(conversation_history) if conversation_history else 0,
                "answer_metadata": {
                    "model": "gemini_2.5_flash",
                    "response_length": len(response),
                    "has_context": len(context) > 0
                }
            }
            
            logger.info(f"Successfully answered question with {len(response)} character response")
            return answer
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return {
                "answer": "I apologize, but I encountered an error while processing your question. Please try again.",
                "query": query,
                "error": str(e),
                "answer_metadata": {"error": True}
            }
    
    async def generate_follow_up_suggestions(self, context: str) -> List[str]:
        """
        Generate follow-up question suggestions.
        
        Args:
            context: Website content context
            
        Returns:
            List of suggested questions
        """
        try:
            prompt = ConversationPrompts.get_follow_up_suggestions_prompt(context)
            response = await self._generate_response(prompt)
            
            # Parse JSON response
            suggestions_data = self._parse_json_response(response)
            return suggestions_data.get("suggestions", [])
            
        except Exception as e:
            logger.error(f"Error generating follow-up suggestions: {str(e)}")
            return []
    
    async def _generate_response(self, prompt: str) -> str:
        """
        Generate response using Gemini model.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated response text
        """
        try:
            # Use async generation if available, otherwise sync
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(**self.generation_config)
            )
            
            if response.text:
                return response.text.strip()
            else:
                raise Exception("Empty response from Gemini")
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response from Gemini.
        
        Args:
            response: Raw response text
            
        Returns:
            Parsed JSON data
        """
        try:
            # Try to find JSON in the response
            response = response.strip()
            
            # Look for JSON block markers
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                if end > start:
                    response = response[start:end].strip()
            
            # Parse JSON
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {str(e)}")
            # Return a fallback structure
            return {
                "error": "Failed to parse AI response",
                "raw_response": response,
                "confidence_score": 1
            }
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return {
                "error": "Error parsing response",
                "raw_response": response,
                "confidence_score": 1
            }
    
    def _create_error_response(self, error_type: str, error_message: str) -> Dict[str, Any]:
        """Create error response structure."""
        return {
            "error": True,
            "error_type": error_type,
            "error_message": error_message,
            "confidence_score": 1,
            "extraction_metadata": {
                "error": True,
                "error_type": error_type
            }
        }
    
    def _get_mock_insights(self, content: str, custom_questions: List[str] = None) -> Dict[str, Any]:
        """Generate mock insights for demonstration purposes."""
        return {
            "industry": "Technology/SaaS",
            "company_size": "Medium (50-200 employees)",
            "location": "San Francisco, CA",
            "usp": "AI-powered platform that helps businesses automate their workflows and increase productivity through intelligent automation tools.",
            "products_services": [
                "Workflow Automation",
                "AI Analytics", 
                "Integration Services",
                "Custom Solutions"
            ],
            "target_audience": "B2B enterprises looking to streamline operations and improve efficiency",
            "contact_info": {
                "email": "contact@example.com",
                "phone": "+1 (555) 123-4567",
                "address": "123 Tech Street, San Francisco, CA 94105"
            },
            "custom_answers": [
                "This appears to be a technology company focused on business automation solutions.",
                "They offer AI-powered tools for workflow management and productivity enhancement.",
                "Target market includes mid to large-scale B2B enterprises seeking operational efficiency."
            ] if custom_questions else [],
            "extraction_metadata": {
                "content_length": len(content),
                "custom_questions_count": len(custom_questions) if custom_questions else 0,
                "extraction_method": "mock_demo",
                "confidence": "Mock data for demonstration"
            }
        }
