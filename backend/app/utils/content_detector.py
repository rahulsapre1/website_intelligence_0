"""
Content quality detection for web scraping fallback decisions.
"""

import re
from typing import List, Dict, Any
from app.core.config import settings


class ContentDetector:
    """Detects if scraped content is sufficient or needs fallback scraping."""
    
    # Business-related keywords to look for
    BUSINESS_KEYWORDS = [
        "company", "about", "product", "service", "business", "team", "contact",
        "pricing", "features", "solutions", "platform", "technology", "industry",
        "customers", "clients", "partners", "mission", "vision", "values",
        "leadership", "careers", "jobs", "news", "blog", "resources", "support"
    ]
    
    def __init__(self):
        self.min_text_length = settings.min_text_length
        self.min_text_ratio = settings.min_text_ratio
        self.min_keyword_matches = settings.min_keyword_matches
    
    def should_use_fallback(self, html_content: str, text_content: str) -> Dict[str, Any]:
        """
        Determine if fallback scraping should be used based on content quality.
        
        Args:
            html_content: Raw HTML content
            text_content: Extracted text content
            
        Returns:
            Dict containing decision and metrics
        """
        metrics = self._analyze_content(html_content, text_content)
        
        # Decision logic: ANY of these conditions triggers fallback
        should_fallback = (
            metrics["text_length"] < self.min_text_length or
            metrics["text_ratio"] < self.min_text_ratio or
            metrics["keyword_matches"] < self.min_keyword_matches
        )
        
        return {
            "should_fallback": should_fallback,
            "reason": self._get_fallback_reason(metrics),
            "metrics": metrics,
            "thresholds": {
                "min_text_length": self.min_text_length,
                "min_text_ratio": self.min_text_ratio,
                "min_keyword_matches": self.min_keyword_matches
            }
        }
    
    def _analyze_content(self, html_content: str, text_content: str) -> Dict[str, Any]:
        """Analyze content quality metrics."""
        text_length = len(text_content.strip())
        html_length = len(html_content)
        text_ratio = text_length / html_length if html_length > 0 else 0
        
        # Count business keyword matches (case-insensitive)
        text_lower = text_content.lower()
        keyword_matches = sum(1 for keyword in self.BUSINESS_KEYWORDS 
                            if keyword.lower() in text_lower)
        
        # Check for common "empty" indicators
        has_scripts_only = self._has_only_scripts(html_content)
        has_minimal_content = text_length < 100
        
        return {
            "text_length": text_length,
            "html_length": html_length,
            "text_ratio": round(text_ratio, 3),
            "keyword_matches": keyword_matches,
            "has_scripts_only": has_scripts_only,
            "has_minimal_content": has_minimal_content
        }
    
    def _has_only_scripts(self, html_content: str) -> bool:
        """Check if HTML contains mostly scripts and minimal content."""
        # Remove script and style tags
        clean_html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', clean_html)
        # Check if remaining text is very short
        return len(clean_text.strip()) < 200
    
    def _get_fallback_reason(self, metrics: Dict[str, Any]) -> str:
        """Get human-readable reason for fallback decision."""
        reasons = []
        
        if metrics["text_length"] < self.min_text_length:
            reasons.append(f"Text too short ({metrics['text_length']} < {self.min_text_length})")
        
        if metrics["text_ratio"] < self.min_text_ratio:
            reasons.append(f"Low text ratio ({metrics['text_ratio']:.3f} < {self.min_text_ratio})")
        
        if metrics["keyword_matches"] < self.min_keyword_matches:
            reasons.append(f"Insufficient keywords ({metrics['keyword_matches']} < {self.min_keyword_matches})")
        
        if metrics["has_scripts_only"]:
            reasons.append("Content appears to be JavaScript-only")
        
        if metrics["has_minimal_content"]:
            reasons.append("Minimal content detected")
        
        return "; ".join(reasons) if reasons else "Content quality is sufficient"
