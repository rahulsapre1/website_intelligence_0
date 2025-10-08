"""
Prompt templates for conversational AI interactions.
"""

from typing import List, Dict, Any


class ConversationPrompts:
    """Prompt templates for conversational AI responses."""
    
    @staticmethod
    def get_chat_prompt(
        query: str, 
        context: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate prompt for conversational responses.
        
        Args:
            query: User's question
            context: Website content context
            conversation_history: Previous conversation turns
            
        Returns:
            Formatted prompt string
        """
        history_context = ""
        if conversation_history:
            history_context = "\n\nPrevious conversation:\n"
            for turn in conversation_history[-3:]:  # Last 3 turns for context
                history_context += f"User: {turn.get('query', '')}\n"
                history_context += f"Assistant: {turn.get('answer', '')}\n"
        
        return f"""
You are a helpful business intelligence assistant. Answer the user's question based on the website content provided.

Website Content Context:
{context[:6000]}

{history_context}

User Question: {query}

Instructions:
- Answer based ONLY on the provided website content
- Be specific and cite relevant information from the content
- If the information isn't available in the content, say so clearly
- Provide actionable insights when possible
- Keep responses concise but informative
- If asked about something not in the content, suggest what additional information would be helpful

Respond in a conversational, helpful tone. Focus on being accurate and useful.
"""
    
    @staticmethod
    def get_follow_up_suggestions_prompt(context: str) -> str:
        """Generate prompt for follow-up question suggestions."""
        return f"""
Based on this website content, suggest 3-5 follow-up questions a user might want to ask:

Website Content:
{context[:4000]}

Respond with JSON:
{{
  "suggestions": [
    "What is their pricing model?",
    "Who are their main competitors?",
    "What technology do they use?",
    "How long have they been in business?",
    "What makes them different from competitors?"
  ],
  "categories": {{
    "pricing": ["Questions about pricing and plans"],
    "technology": ["Questions about tech stack and features"],
    "business": ["Questions about company background"],
    "competition": ["Questions about market position"]
  }}
}}

Make suggestions that would be valuable for someone researching this company.
"""
    
    @staticmethod
    def get_summary_prompt(context: str, focus_area: str = None) -> str:
        """Generate prompt for focused summarization."""
        focus_instruction = ""
        if focus_area:
            focus_instruction = f"\nFocus specifically on: {focus_area}"
        
        return f"""
Provide a comprehensive summary of this website content{focus_instruction}:

Website Content:
{context[:6000]}

Structure your response as:
1. **Company Overview** - What they do and their main value proposition
2. **Key Products/Services** - Main offerings and features
3. **Target Market** - Who they serve
4. **Business Model** - How they operate and make money
5. **Key Differentiators** - What makes them unique
6. **Contact & Next Steps** - How to engage with them

Be thorough but concise. Use bullet points and clear headings.
"""
    
    @staticmethod
    def get_competitor_analysis_prompt(context: str) -> str:
        """Generate prompt for competitor analysis."""
        return f"""
Analyze this website content to identify potential competitors and market positioning:

Website Content:
{context[:4000]}

Respond with JSON:
{{
  "market_category": "What market category do they operate in?",
  "potential_competitors": [
    "List 3-5 well-known companies that might be competitors"
  ],
  "competitive_advantages": [
    "What advantages do they seem to have over competitors"
  ],
  "market_positioning": "How do they position themselves in the market?",
  "differentiation_factors": [
    "Key factors that differentiate them from competitors"
  ],
  "market_maturity": "Is this a mature market, emerging market, or new market?"
}}

Base this analysis on the content provided and general market knowledge.
"""
    
    @staticmethod
    def get_technical_analysis_prompt(context: str) -> str:
        """Generate prompt for technical analysis."""
        return f"""
Analyze the technical aspects of this business based on the website content:

Website Content:
{context[:4000]}

Respond with JSON:
{{
  "technology_stack": [
    "Technologies mentioned or implied"
  ],
  "platform_type": "Web app, Mobile app, Desktop, API, etc.",
  "deployment_model": "Cloud, On-premise, Hybrid, etc.",
  "integration_capabilities": [
    "Integration options mentioned"
  ],
  "technical_features": [
    "Technical features highlighted"
  ],
  "development_approach": "Agile, DevOps practices mentioned, etc.",
  "security_mentions": [
    "Security features or certifications mentioned"
  ],
  "scalability_indicators": [
    "Indicators of scalability or performance"
  ]
}}

Focus on technical details that would be relevant for technical decision-makers.
"""
