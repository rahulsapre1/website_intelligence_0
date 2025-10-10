"""
Focused crawler to fetch a small set of in-domain pages relevant to user questions.
"""

import logging
from typing import List, Dict, Any, Set, Tuple
from urllib.parse import urlparse, urljoin
import asyncio
import httpx
from bs4 import BeautifulSoup

from app.core.config import settings

logger = logging.getLogger(__name__)


class FocusedCrawler:
    """Crawl a limited set of relevant in-domain pages asynchronously."""

    def __init__(self):
        self.timeout = settings.scraping_timeout
        self.max_pages = getattr(settings, "crawl_max_pages", 6)
        self.max_depth = getattr(settings, "crawl_max_depth", 1)
        # Keywords to prioritize in links
        self.default_keywords = [
            "pricing", "plans", "features", "product", "solutions", "services",
            "about", "company", "team", "contact", "support",
            "case-studies", "customers", "testimonials", "security", "docs"
        ]

    def _extract_links(self, base_url: str, html: str) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        base = urlparse(base_url)
        links: Set[str] = set()
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if href.startswith('#') or href.lower().startswith('mailto:') or href.lower().startswith('tel:'):
                continue
            absolute = urljoin(base_url, href)
            parsed = urlparse(absolute)
            # In-domain only
            if parsed.netloc and parsed.netloc == base.netloc:
                links.add(absolute.split('#')[0])
        return list(links)

    def _score_link(self, url: str, questions: List[str]) -> int:
        score = 0
        lower = url.lower()
        for kw in self.default_keywords:
            if kw in lower:
                score += 3
        if questions:
            # Light heuristic: boost if question words appear in path
            for q in questions:
                for token in q.lower().split():
                    if len(token) >= 4 and token in lower:
                        score += 1
        return score

    async def _fetch(self, client: httpx.AsyncClient, url: str) -> Tuple[str, str]:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            return url, resp.text
        except Exception as e:
            logger.debug(f"Crawler fetch failed for {url}: {e}")
            return url, ""

    async def crawl(self, base_url: str, homepage_html: str, questions: List[str]) -> List[Dict[str, Any]]:
        """
        Crawl up to max_pages in-domain links prioritized by relevance to questions.
        Returns list of {url, html, text_length}.
        """
        links = self._extract_links(base_url, homepage_html)
        # Rank links by heuristic score
        ranked = sorted(links, key=lambda u: self._score_link(u, questions), reverse=True)
        selected = ranked[: self.max_pages]

        results: List[Dict[str, Any]] = []
        if not selected:
            return results

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = [self._fetch(client, u) for u in selected]
            for coro in asyncio.as_completed(tasks):
                url, html = await coro
                if not html:
                    continue
                try:
                    soup = BeautifulSoup(html, 'html.parser')
                    text = soup.get_text(" ", strip=True)
                except Exception:
                    text = html
                results.append({
                    "url": url,
                    "html": html,
                    "full_text": text,
                    "text_length": len(text)
                })

        return results


