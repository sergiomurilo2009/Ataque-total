"""
Cache module for search results
Uses shelve for simple file-based caching (can be upgraded to Redis later)
"""
import shelve
import hashlib
import time
from typing import Optional, Dict, Any, List
from pathlib import Path


class Cache:
    """Simple cache implementation using shelve"""
    
    def __init__(self, cache_file: str = "search_cache.db", ttl_seconds: int = 900):
        """
        Initialize cache
        
        Args:
            cache_file: Path to the cache database file
            ttl_seconds: Time-to-live for cache entries (default: 15 minutes)
        """
        self.cache_file = Path(cache_file)
        self.ttl_seconds = ttl_seconds
    
    def _generate_key(self, query: str, category: str = "general", page: int = 1) -> str:
        """Generate a unique cache key for query + category + page"""
        key_string = f"{query}:{category}:{page}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query: str, category: str = "general", page: int = 1) -> Optional[List[Dict[str, Any]]]:
        """Get cached results if available and not expired"""
        try:
            with shelve.open(str(self.cache_file)) as cache:
                key = self._generate_key(query, category, page)
                if key in cache:
                    data = cache[key]
                    timestamp = data.get('timestamp', 0)
                    
                    # Check if cache is still valid
                    if time.time() - timestamp < self.ttl_seconds:
                        return data.get('results', [])
                    else:
                        # Expired, delete it
                        del cache[key]
                        
                return None
        except Exception as e:
            print(f"[Cache Error] Failed to get from cache: {str(e)[:50]}")
            return None
    
    def set(self, query: str, results: List[Dict[str, Any]], category: str = "general", page: int = 1):
        """Store results in cache"""
        try:
            with shelve.open(str(self.cache_file)) as cache:
                key = self._generate_key(query, category, page)
                cache[key] = {
                    'results': results,
                    'timestamp': time.time(),
                    'query': query,
                    'category': category,
                    'page': page
                }
        except Exception as e:
            print(f"[Cache Error] Failed to store in cache: {str(e)[:50]}")
    
    def clear(self):
        """Clear all cached data"""
        try:
            with shelve.open(str(self.cache_file)) as cache:
                cache.clear()
            print("[Cache] Cleared all cached data")
        except Exception as e:
            print(f"[Cache Error] Failed to clear cache: {str(e)[:50]}")
    
    def cleanup_expired(self):
        """Remove expired entries from cache"""
        try:
            with shelve.open(str(self.cache_file)) as cache:
                expired_keys = []
                
                for key in cache:
                    data = cache[key]
                    timestamp = data.get('timestamp', 0)
                    
                    if time.time() - timestamp >= self.ttl_seconds:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del cache[key]
                    
                if expired_keys:
                    print(f"[Cache] Cleaned up {len(expired_keys)} expired entries")
                    
        except Exception as e:
            print(f"[Cache Error] Failed to cleanup cache: {str(e)[:50]}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            with shelve.open(str(self.cache_file)) as cache:
                total_entries = len(cache)
                now = time.time()
                valid_entries = 0
                expired_entries = 0
                
                for key in cache:
                    data = cache[key]
                    timestamp = data.get('timestamp', 0)
                    
                    if now - timestamp < self.ttl_seconds:
                        valid_entries += 1
                    else:
                        expired_entries += 1
                
                return {
                    'total_entries': total_entries,
                    'valid_entries': valid_entries,
                    'expired_entries': expired_entries,
                    'ttl_seconds': self.ttl_seconds,
                    'cache_file': str(self.cache_file)
                }
        except Exception as e:
            return {'error': str(e)}
