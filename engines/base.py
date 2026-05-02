"""
Base Engine - Abstract base class for all search engines
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import asyncio
import time
import random


class BaseEngine(ABC):
    """Abstract base class for all search engines"""
    
    def __init__(self, name: str, category: str, enabled: bool = True):
        self.name = name
        self.category = category
        self.enabled = enabled
        self.request_count = 0
        self.last_request_time = 0
        
    @abstractmethod
    async def search(self, session, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """Perform search and return list of results"""
        pass
    
    @abstractmethod
    def parse_results(self, html_content: str, query: str) -> List[Dict[str, Any]]:
        """Parse HTML content and extract results"""
        pass
    
    def parse_api_results(self, json_data: Any, query: str) -> List[Dict[str, Any]]:
        """Parse API JSON response (optional override)"""
        return []
    
    async def _apply_delay(self, min_delay: float = 0.3, max_delay: float = 0.8):
        """Apply rate limiting delay"""
        now = time.time()
        elapsed = now - self.last_request_time
        
        if elapsed < min_delay:
            delay = random.uniform(min_delay, max_delay)
            await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
    
    def _get_fresh_headers(self, base_headers: Dict[str, str], user_agents: List[str]) -> Dict[str, str]:
        """Generate fresh headers with rotating User-Agent"""
        headers = base_headers.copy()
        headers["User-Agent"] = random.choice(user_agents)
        return headers
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL by removing tracking parameters"""
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed = urlparse(url)
        
        # Remove common tracking parameters
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 
                          'utm_term', 'utm_content', 'fbclid', 'gclid',
                          'ref', 'source', 'medium', 'campaign']
        
        qs = parse_qs(parsed.query, keep_blank_values=True)
        filtered_qs = {k: v for k, v in qs.items() if k not in tracking_params}
        
        # Rebuild URL without tracking params
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(filtered_qs, doseq=True),
            parsed.fragment
        ))
        
        return normalized.rstrip('?&')
