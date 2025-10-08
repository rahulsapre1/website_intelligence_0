"""
Prompt templates for business insight extraction using Gemini.
"""

from typing import Dict, Any, List


class ExtractionPrompts:
    """Prompt templates for extracting business insights from website content."""
    
    @staticmethod
    def get_core_insights_prompt(content: str, custom_questions: List[str] = None) -> str:
        """
        Generate prompt for extracting core business insights.
        
        Args:
            content: Website content to analyze
            custom_questions: Optional custom questions to answer
            
        Returns:
            Formatted prompt string
        """
        base_prompt = f"""
You are an expert business analyst. Analyze the following website content and extract key business insights.

Website Content:
{content[:8000]}  # Limit to 8k chars for context

Extract the following information in JSON format:

{{
  "industry": "What industry does this company primarily belong to? (e.g., SaaS, E-commerce, Healthcare, etc.)",
  "company_size": "What is the approximate company size? (e.g., Startup, Small, Medium, Large, Enterprise)",
  "location": "Where is the company headquartered or primarily located? (city, state/country)",
  "usp": "What is the company's unique selling proposition? What makes them stand out?",
  "products_services": ["List the main products or services offered"],
  "target_audience": "Who is the primary target audience or customer demographic?",
  "contact_info": {{
    "email": "Primary contact email if found",
    "phone": "Phone number if found",
    "social_media": ["Social media links if found"]
  }},
  "confidence_score": "Rate your confidence in this analysis (1-10)",
  "key_insights": ["Additional important insights about the business"]
}}

Guidelines:
- Be specific and factual based on the content
- If information is not available, use "Not specified" or empty arrays
- Focus on information explicitly stated or clearly implied
- For company size, infer from context (team size mentions, funding, etc.)
- For industry, be as specific as possible (not just "Technology")
- Confidence score should reflect how clear the information is in the content

"""
        
        if custom_questions:
            base_prompt += f"""
Additionally, answer these specific questions:
{chr(10).join(f"- {q}" for q in custom_questions)}

Include answers in a "custom_answers" field in the JSON response.
"""
        
        return base_prompt
    
    @staticmethod
    def get_industry_classification_prompt(content: str) -> str:
        """Generate prompt for industry classification."""
        return f"""
Classify the industry of this business based on the website content:

Content: {content[:4000]}

Respond with a JSON object:
{{
  "primary_industry": "Most specific industry category",
  "secondary_industries": ["Related industry categories"],
  "business_model": "How they make money (B2B, B2C, Marketplace, etc.)",
  "technology_focus": "If tech company, what specific technology area",
  "market_segment": "Target market segment (Enterprise, SMB, Consumer, etc.)",
  "confidence": "Confidence level 1-10"
}}

Be as specific as possible. For example:
- Instead of "Technology" → "SaaS/Cloud Computing" or "AI/ML Platform"
- Instead of "E-commerce" → "Fashion E-commerce" or "B2B Marketplace"
"""
    
    @staticmethod
    def get_company_size_prompt(content: str) -> str:
        """Generate prompt for company size estimation."""
        return f"""
Estimate the company size based on this website content:

Content: {content[:4000]}

Look for indicators like:
- Team size mentions
- Funding information
- Office locations
- Customer base size
- Revenue indicators
- Job postings

Respond with JSON:
{{
  "estimated_size": "Startup/Small/Medium/Large/Enterprise",
  "employee_range": "Specific range if determinable (e.g., 10-50, 100-500)",
  "indicators_found": ["List specific indicators that led to this conclusion"],
  "confidence": "Confidence level 1-10"
}}
"""
    
    @staticmethod
    def get_contact_extraction_prompt(content: str) -> str:
        """Generate prompt for contact information extraction."""
        return f"""
Extract contact information from this website content:

Content: {content[:4000]}

Find and extract:
- Email addresses
- Phone numbers
- Physical addresses
- Social media links
- Contact forms

Respond with JSON:
{{
  "emails": ["email1@domain.com", "email2@domain.com"],
  "phones": ["+1-555-123-4567", "555-123-4567"],
  "addresses": ["123 Main St, City, State 12345"],
  "social_media": {{
    "twitter": "https://twitter.com/company",
    "linkedin": "https://linkedin.com/company/company",
    "facebook": "https://facebook.com/company",
    "instagram": "https://instagram.com/company"
  }},
  "contact_forms": ["URLs to contact forms if found"]
}}

Only include information that is clearly visible in the content.
"""
    
    @staticmethod
    def get_products_services_prompt(content: str) -> str:
        """Generate prompt for products/services extraction."""
        return f"""
Extract the main products and services from this website content:

Content: {content[:4000]}

Respond with JSON:
{{
  "products": [
    {{
      "name": "Product name",
      "description": "Brief description",
      "category": "Product category"
    }}
  ],
  "services": [
    {{
      "name": "Service name", 
      "description": "Brief description",
      "category": "Service category"
    }}
  ],
  "pricing_mentioned": "Yes/No - whether pricing information is visible",
  "free_trial": "Yes/No - whether free trial is offered",
  "main_offering": "The primary product or service they lead with"
}}
"""
