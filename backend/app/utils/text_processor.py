"""
Text processing utilities for content cleaning and chunking.
"""

import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup


class TextProcessor:
    """Handles text cleaning, chunking, and preprocessing for AI processing."""
    
    def __init__(self, max_chunk_size: int = 1000, chunk_overlap: int = 200):
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        
        # Remove multiple consecutive punctuation
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        return text.strip()
    
    def extract_structured_content(self, html_content: str) -> Dict[str, Any]:
        """
        Extract structured content from HTML.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Dict with structured content sections
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extract different content types
        content = {
            "title": self._extract_title(soup),
            "headings": self._extract_headings(soup),
            "paragraphs": self._extract_paragraphs(soup),
            "lists": self._extract_lists(soup),
            "links": self._extract_links(soup),
            "full_text": self._extract_full_text(soup)
        }
        
        return content
    
    def chunk_text(self, text: str, chunk_type: str = "paragraph") -> List[Dict[str, Any]]:
        """
        Split text into chunks for processing.
        
        Args:
            text: Text to chunk
            chunk_type: Type of chunking strategy
            
        Returns:
            List of text chunks with metadata
        """
        if not text or len(text) <= self.max_chunk_size:
            return [{
                "text": text,
                "chunk_type": chunk_type,
                "chunk_index": 0,
                "start_pos": 0,
                "end_pos": len(text)
            }]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.max_chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 200 characters
                search_start = max(start, end - 200)
                sentence_end = text.rfind('.', search_start, end)
                if sentence_end > search_start:
                    end = sentence_end + 1
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "chunk_type": chunk_type,
                    "chunk_index": chunk_index,
                    "start_pos": start,
                    "end_pos": end
                })
                chunk_index += 1
            
            # Move start position with overlap
            start = max(start + 1, end - self.chunk_overlap)
        
        return chunks
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else ""
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[str]:
        """Extract all headings (h1-h6)."""
        headings = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = tag.get_text().strip()
            if text:
                headings.append(text)
        return headings
    
    def _extract_paragraphs(self, soup: BeautifulSoup) -> List[str]:
        """Extract paragraph text."""
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 20:  # Filter out very short paragraphs
                paragraphs.append(text)
        return paragraphs
    
    def _extract_lists(self, soup: BeautifulSoup) -> List[str]:
        """Extract list items."""
        list_items = []
        for ul in soup.find_all(['ul', 'ol']):
            for li in ul.find_all('li'):
                text = li.get_text().strip()
                if text:
                    list_items.append(text)
        return list_items
    
    def _extract_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract links with text and href."""
        links = []
        for a in soup.find_all('a', href=True):
            text = a.get_text().strip()
            href = a.get('href', '')
            if text and href:
                links.append({"text": text, "href": href})
        return links
    
    def _extract_full_text(self, soup: BeautifulSoup) -> str:
        """Extract all text content."""
        return soup.get_text()
