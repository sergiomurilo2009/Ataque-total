"""
Deduplication module for search results
Uses URL hashing to remove duplicates across engines
"""
import hashlib
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


class Deduplicator:
    """Remove duplicate results based on normalized URLs"""
    
    def __init__(self):
        self.seen_urls = set()
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize URL by removing tracking parameters and standardizing format
        
        Removes common tracking params: utm_*, fbclid, gclid, ref, source, etc.
        """
        try:
            parsed = urlparse(url)
            
            # Remove common tracking parameters
            tracking_params = [
                'utm_source', 'utm_medium', 'utm_campaign', 
                'utm_term', 'utm_content', 'fbclid', 'gclid',
                'ref', 'source', 'medium', 'campaign', 'cid',
                'wt_mc_o', 'pk_campaign', 'mbid'
            ]
            
            qs = parse_qs(parsed.query, keep_blank_values=True)
            filtered_qs = {k: v for k, v in qs.items() if k not in tracking_params}
            
            # Rebuild URL without tracking params
            normalized = urlunparse((
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip('/'),
                parsed.params,
                urlencode(filtered_qs, doseq=True),
                parsed.fragment
            ))
            
            # Remove trailing ? if query is empty
            return normalized.rstrip('?&')
            
        except Exception:
            # If parsing fails, return original URL
            return url
    
    def _generate_hash(self, url: str) -> str:
        """Generate MD5 hash of normalized URL"""
        normalized = self.normalize_url(url)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def deduplicate(self, results: List[Dict[str, Any]], reset: bool = True) -> List[Dict[str, Any]]:
        """
        Remove duplicate results based on URL hash
        
        Args:
            results: List of result dictionaries
            reset: Clear seen URLs before processing (default: True)
        
        Returns:
            List of unique results
        """
        if reset:
            self.seen_urls = set()
        
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if not url:
                continue
            
            url_hash = self._generate_hash(url)
            
            if url_hash not in self.seen_urls:
                self.seen_urls.add(url_hash)
                unique_results.append(result)
        
        return unique_results
    
    def is_duplicate(self, url: str) -> bool:
        """Check if URL is a duplicate without adding to seen set"""
        url_hash = self._generate_hash(url)
        return url_hash in self.seen_urls
    
    def add_url(self, url: str) -> bool:
        """
        Add URL to seen set
        
        Returns:
            True if URL was new, False if it was already seen
        """
        url_hash = self._generate_hash(url)
        
        if url_hash in self.seen_urls:
            return False
        
        self.seen_urls.add(url_hash)
        return True
    
    def clear(self):
        """Clear all seen URLs"""
        self.seen_urls = set()
    
    def get_count(self) -> int:
        """Get count of unique URLs seen"""
        return len(self.seen_urls)


def deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function to deduplicate results
    
    Args:
        results: List of result dictionaries
    
    Returns:
        List of unique results
    """
    dedup = Deduplicator()
    return dedup.deduplicate(results)
