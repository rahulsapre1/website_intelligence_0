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
            
            # Return mock response if in mock mode
            if self.mock_mode:
                logger.info("Returning mock chat response - API key not configured")
                return self._get_mock_chat_response(query, context, conversation_history)
            
            # Generate prompt with brevity and directness
            prompt = ConversationPrompts.get_chat_prompt(query, context, conversation_history)
            prompt += "\n\nInstructions: Answer succinctly (2-5 sentences). Be specific to the question. Use only provided context. If unknown, say so briefly."
            
            # Generate response
            response = await self._generate_response(prompt)
            # Enforce brevity post-process as safeguard
            if len(response) > 800:
                response = response[:800].rsplit('. ', 1)[0] + '.'
            
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
    
    def _get_mock_chat_response(self, query: str, context: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate mock chat response for demonstration purposes."""
        
        # Extract website domain from context if available
        website_domain = "this website"
        if context and "Website content for" in context:
            try:
                # Extract URL from context like "Website content for https://example.com"
                url_start = context.find("Website content for ") + len("Website content for ")
                url_end = context.find(" - Database not available")
                if url_end > url_start:
                    url = context[url_start:url_end]
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    website_domain = parsed.netloc or url
            except:
                pass
        
        # Generate contextual responses based on common question types
        query_lower = query.lower()
        
        if "pricing" in query_lower or "cost" in query_lower or "price" in query_lower:
            answer = f"Based on {website_domain}, I can see this appears to be a business website. For pricing information, I'd recommend checking their pricing page, product pages, or contacting them directly. Most businesses display their pricing structure prominently on their website, often in a dedicated pricing section or within their product/service descriptions."
        
        elif "contact" in query_lower or "email" in query_lower or "phone" in query_lower:
            answer = f"To find contact information for {website_domain}, I'd suggest looking in several common locations: the footer of the website, an 'About Us' or 'Contact' page, or in the header navigation. Most websites include contact details such as email addresses, phone numbers, or contact forms. You might also find social media links or a physical address if they have an office location."
        
        elif "services" in query_lower or "products" in query_lower or "offer" in query_lower:
            answer = f"Looking at {website_domain}, this appears to be a business website. To understand what services or products they offer, I'd recommend exploring their main navigation menu, product pages, or service descriptions. Most businesses clearly outline their offerings on their homepage or in dedicated sections. You might also find case studies, testimonials, or detailed service descriptions that explain what they provide."
        
        elif "about" in query_lower or "company" in query_lower or "who" in query_lower:
            answer = f"To learn more about the company behind {website_domain}, I'd suggest checking their 'About Us' page, company history section, or team page. Most businesses provide information about their mission, values, team members, and company background. You might also find information about their founding story, leadership team, or company culture in these sections."
        
        elif "location" in query_lower or "where" in query_lower or "address" in query_lower:
            answer = f"For location information about {website_domain}, I'd recommend checking their contact page, footer, or 'About Us' section. Most businesses include their physical address, office locations, or service areas. You might also find information about whether they serve specific regions, have multiple locations, or operate primarily online."
        
        elif "hours" in query_lower or "time" in query_lower or "open" in query_lower:
            answer = f"To find business hours or operating times for {website_domain}, I'd suggest checking their contact page, footer, or any location-specific pages. Most businesses display their hours of operation, especially if they have a physical location or customer service hours. This information is typically found alongside contact details."
        
        elif "reviews" in query_lower or "testimonials" in query_lower or "feedback" in query_lower:
            answer = f"For reviews and testimonials about {website_domain}, I'd recommend looking for a testimonials section, case studies, or customer reviews on their website. Many businesses showcase client feedback, success stories, or reviews from customers. You might also find links to external review platforms or social proof elements throughout their site."
        
        else:
            answer = f"Based on {website_domain}, I can see this is a business website. Regarding your question about '{query}', I'd recommend exploring their website more thoroughly to find the specific information you're looking for. Most businesses organize their content logically, so try checking relevant sections like their main navigation, product pages, or contact information. If you can't find what you need, contacting them directly through their website would be the best approach."
        
        return {
            "answer": answer,
            "query": query,
            "context_length": len(context),
            "conversation_turns": len(conversation_history) if conversation_history else 0,
            "answer_metadata": {
                "model": "mock_demo",
                "response_length": len(answer),
                "has_context": len(context) > 0,
                "mock_mode": True,
                "website_analyzed": website_domain
            }
        }
