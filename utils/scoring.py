"""
Scoring and ranking module for search results
Implements intelligent ranking based on engine reliability and cross-engine presence
"""
from typing import List, Dict, Any
from collections import defaultdict


class ResultScorer:
    """Score and rank search results intelligently"""
    
    def __init__(self):
        # Engine reliability weights (higher = more trustworthy)
        self.engine_weights = {
            'Wikipedia': 1.5,
            'Brave': 1.4,
            'GitHub': 1.3,
            'StackOverflow': 1.3,
            'Google': 1.2,
            'Bing': 1.1,
            'DuckDuckGo': 1.1,
            'Yandex': 1.0,
            'Qwant': 1.0,
            'Startpage': 1.1,
            'Reddit': 0.9,
            'YouTube': 1.0,
        }
    
    def score_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score results based on multiple factors:
        - Engine reliability
        - Cross-engine presence (same URL appears in multiple engines)
        - Position in results
        
        Args:
            results: List of result dictionaries with 'engine' field
        
        Returns:
            List of results sorted by score (descending)
        """
        if not results:
            return []
        
        # Count URL occurrences across engines
        url_counts = defaultdict(int)
        url_engines = defaultdict(set)
        
        for result in results:
            url = result.get('url', '')
            engine = result.get('engine', '')
            
            if url:
                url_counts[url] += 1
                url_engines[url].add(engine)
        
        # Score each result
        scored_results = []
        
        for i, result in enumerate(results):
            url = result.get('url', '')
            engine = result.get('engine', '')
            
            # Base score from position (lower position = higher base score)
            position_score = max(0, 100 - i) / 100
            
            # Engine weight
            engine_weight = self.engine_weights.get(engine, 1.0)
            
            # Cross-engine bonus (appearing in multiple engines is a strong signal)
            cross_engine_count = url_counts.get(url, 1)
            cross_engine_bonus = min(cross_engine_count * 0.2, 1.0)  # Cap at 1.0
            
            # Diversity bonus (different engines showing same URL)
            unique_engines = len(url_engines.get(url, set()))
            diversity_bonus = min(unique_engines * 0.15, 0.6)  # Cap at 0.6
            
            # Calculate final score
            final_score = (
                position_score * 0.3 +      # 30% position
                engine_weight * 0.4 +        # 40% engine reliability
                cross_engine_bonus * 0.2 +   # 20% cross-engine presence
                diversity_bonus * 0.1        # 10% diversity
            )
            
            # Add score to result
            result_copy = result.copy()
            result_copy['score'] = round(final_score, 3)
            result_copy['cross_engine_count'] = cross_engine_count
            result_copy['unique_engines'] = unique_engines
            
            scored_results.append(result_copy)
        
        # Sort by score descending
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_results
    
    def rank_by_engine(self, results: List[Dict[str, Any]], 
                       preferred_engines: List[str] = None) -> List[Dict[str, Any]]:
        """
        Rank results giving preference to specific engines
        
        Args:
            results: List of result dictionaries
            preferred_engines: List of engine names to prioritize
        
        Returns:
            List of results sorted by engine preference
        """
        if not results:
            return []
        
        preferred_engines = preferred_engines or ['Wikipedia', 'GitHub', 'StackOverflow']
        
        def sort_key(result):
            engine = result.get('engine', '')
            is_preferred = 1 if engine in preferred_engines else 0
            return (-is_preferred, engine)
        
        return sorted(results, key=sort_key)
    
    def filter_by_min_score(self, results: List[Dict[str, Any]], 
                           min_score: float = 0.3) -> List[Dict[str, Any]]:
        """
        Filter results by minimum score
        
        Args:
            results: List of scored result dictionaries
            min_score: Minimum score threshold
        
        Returns:
            Filtered list of results
        """
        return [r for r in results if r.get('score', 0) >= min_score]
    
    def get_top_results(self, results: List[Dict[str, Any]], 
                       limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get top N results after scoring
        
        Args:
            results: List of result dictionaries
            limit: Maximum number of results to return
        
        Returns:
            Top N scored results
        """
        scored = self.score_results(results)
        return scored[:limit]


def score_and_rank(results: List[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
    """
    Convenience function to score and rank results
    
    Args:
        results: List of result dictionaries
        limit: Maximum number of results to return
    
    Returns:
        Top N scored and ranked results
    """
    scorer = ResultScorer()
    return scorer.get_top_results(results, limit)
