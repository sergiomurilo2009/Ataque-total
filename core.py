"""
Core module - Main search logic and aggregation
Handles query parsing, engine coordination, caching, and result ranking
"""
import asyncio
import aiohttp
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import quote_plus

# Import utilities
from utils.cache import Cache
from utils.dedup import Deduplicator
from utils.scoring import ResultScorer


class SearchCore:
    """Main search orchestrator"""
    
    def __init__(self, config_path: str = "config/default.json"):
        self.config = self._load_config(config_path)
        self.cache = None
        self.deduplicator = Deduplicator()
        self.scorer = ResultScorer()
        
        # Initialize cache if enabled
        cache_config = self.config.get('cache', {})
        if cache_config.get('enabled', True):
            self.cache = Cache(
                cache_file=cache_config.get('file', 'search_cache.db'),
                ttl_seconds=cache_config.get('ttl_seconds', 900)
            )
        
        # Load bangs configuration
        self.bangs = self.config.get('bangs', {})
        
        # Engine configurations
        self.engine_configs = self.config.get('engines', {})
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[Config] Warning: {config_path} not found, using defaults")
            return self._default_config()
        except json.JSONDecodeError as e:
            print(f"[Config] Error parsing {config_path}: {e}")
            return self._default_config()
    
    def _default_config(self) -> dict:
        """Default configuration"""
        return {
            'engines': {
                'Bing': {'enabled': True, 'category': 'general', 'weight': 1.1},
                'DuckDuckGo': {'enabled': True, 'category': 'general', 'weight': 1.1},
                'Wikipedia': {'enabled': True, 'category': 'general', 'weight': 1.5},
            },
            'cache': {'enabled': True, 'ttl_seconds': 900},
            'limits': {
                'max_results_per_engine': 50,
                'max_total_results': 200,
                'max_concurrent_connections': 10
            }
        }
    
    def parse_query(self, query: str) -> Tuple[str, Optional[str], List[str]]:
        """
        Parse query for bangs and modifiers
        
        Returns:
            Tuple of (clean_query, target_engine, enabled_engines_override)
        """
        query = query.strip()
        parts = query.split()
        
        # Check for bang at the beginning
        if parts and parts[0].startswith('!'):
            bang = parts[0].lower()
            clean_query = ' '.join(parts[1:]) if len(parts) > 1 else ''
            
            # Check if it's a known bang
            if bang in self.bangs:
                target_engine = self.bangs[bang]
                return clean_query, target_engine, [target_engine]
        
        return query, None, []
    
    async def search(self, query: str, category: str = "general", 
                    page: int = 1, use_cache: bool = True) -> Dict[str, Any]:
        """
        Perform search across enabled engines
        
        Args:
            query: Search query
            category: Result category filter
            page: Page number
            use_cache: Whether to use cached results
        
        Returns:
            Dictionary with results, metadata, and stats
        """
        start_time = time.time()
        
        # Parse query for bangs
        clean_query, target_engine, engine_override = self.parse_query(query)
        
        if not clean_query and target_engine:
            return {
                'results': [],
                'query': query,
                'error': 'Please provide a search term after the bang',
                'engines_used': [],
                'search_time': 0
            }
        
        # Check cache first
        if use_cache and self.cache:
            cached = self.cache.get(clean_query, category, page)
            if cached:
                return {
                    'results': cached,
                    'query': clean_query,
                    'cached': True,
                    'engines_used': ['Cache'],
                    'search_time': 0
                }
        
        # Get enabled engines for this category
        enabled_engines = self._get_enabled_engines(category, engine_override)
        
        if not enabled_engines:
            return {
                'results': [],
                'query': clean_query,
                'error': 'No engines available',
                'engines_used': [],
                'search_time': 0
            }
        
        # If targeting specific engine, only use that one
        if target_engine:
            enabled_engines = [e for e in enabled_engines if e == target_engine]
        
        # Perform search across all engines
        results = await self._search_all_engines(clean_query, enabled_engines, page)
        
        # Deduplicate results
        unique_results = self.deduplicator.deduplicate(results)
        
        # Score and rank results
        limits = self.config.get('limits', {})
        max_results = limits.get('max_total_results', 200)
        scored_results = self.scorer.score_results(unique_results)[:max_results]
        
        # Cache results
        if use_cache and self.cache:
            self.cache.set(clean_query, scored_results, category, page)
        
        search_time = time.time() - start_time
        
        return {
            'results': scored_results,
            'query': clean_query,
            'original_query': query,
            'target_engine': target_engine,
            'category': category,
            'page': page,
            'total_results': len(scored_results),
            'engines_used': list(set(r['engine'] for r in scored_results)),
            'search_time': search_time,
            'cached': False
        }
    
    def _get_enabled_engines(self, category: str, override: List[str] = None) -> List[str]:
        """Get list of enabled engines for a category"""
        if override:
            return override
        
        enabled = []
        for name, config in self.engine_configs.items():
            if config.get('enabled', True):
                eng_category = config.get('category', 'general')
                if category == 'all' or eng_category == category or eng_category == 'general':
                    enabled.append(name)
        
        return enabled
    
    async def _search_all_engines(self, query: str, engines: List[str], 
                                  page: int = 1) -> List[Dict[str, Any]]:
        """Search across multiple engines concurrently"""
        import importlib
        
        # Map engine names to their module classes
        engine_map = {
            'Bing': ('engines.bing', 'BingEngine'),
            'DuckDuckGo': ('engines.duckduckgo', 'DuckDuckGoEngine'),
            'Yandex': ('engines.yandex', 'YandexEngine'),
            'Qwant': ('engines.qwant', 'QwantEngine'),
            'Startpage': ('engines.startpage', 'StartpageEngine'),
            'Wikipedia': ('engines.wikipedia', 'WikipediaEngine'),
            'GitHub': ('engines.github', 'GitHubEngine'),
            'GitLab': ('engines.gitlab', 'GitLabEngine'),
            'StackOverflow': ('engines.stackoverflow', 'StackOverflowEngine'),
            'Reddit': ('engines.reddit', 'RedditEngine'),
            'YouTube': ('engines.youtube', 'YouTubeEngine'),
        }
        
        all_results = []
        
        # Create aiohttp session with proper limits
        max_connections = self.config.get('limits', {}).get('max_concurrent_connections', 10)
        connector = aiohttp.TCPConnector(limit=max_connections, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Create tasks for each engine
            tasks = []
            for engine_name in engines:
                if engine_name in engine_map:
                    try:
                        module_name, class_name = engine_map[engine_name]
                        module = importlib.import_module(module_name)
                        engine_class = getattr(module, class_name)
                        engine_config = self.engine_configs.get(engine_name, {})
                        engine = engine_class(enabled=engine_config.get('enabled', True))
                        tasks.append(engine.search(session, query, page))
                    except Exception as e:
                        print(f"[Error] Failed to load engine {engine_name}: {e}")
            
            if tasks:
                # Execute with timeout
                try:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, list):
                            all_results.extend(result)
                        elif isinstance(result, Exception):
                            print(f"[Error] Engine failed: {result}")
                
                except asyncio.TimeoutError:
                    print("[Timeout] Search timed out")
                except Exception as e:
                    print(f"[Error] Search failed: {e}")
        
        return all_results
    
    def get_categories(self) -> List[str]:
        """Get available search categories"""
        categories = set()
        for config in self.engine_configs.values():
            categories.add(config.get('category', 'general'))
        return sorted(list(categories))
    
    def get_available_engines(self) -> List[Dict[str, Any]]:
        """Get list of available engines with their status"""
        engines = []
        for name, config in self.engine_configs.items():
            engines.append({
                'name': name,
                'enabled': config.get('enabled', True),
                'category': config.get('category', 'general'),
                'weight': config.get('weight', 1.0)
            })
        return engines
    
    def clear_cache(self):
        """Clear search cache"""
        if self.cache:
            self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.cache:
            return self.cache.get_stats()
        return {'enabled': False}


# Convenience function for simple searches
async def search(query: str, **kwargs) -> Dict[str, Any]:
    """Simple search function"""
    core = SearchCore()
    return await core.search(query, **kwargs)
