"""
StackOverflow Search Engine - Uses official API
"""
from .base import BaseEngine
from typing import List, Dict, Any


class StackOverflowEngine(BaseEngine):
    """StackOverflow search using official API"""

    def __init__(self, enabled: bool = True):
        super().__init__("StackOverflow", "software", enabled)
        self.api_url = "https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance&q="

    async def search(self, session, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """Search StackOverflow via API"""
        from aiohttp import ClientError
        import asyncio

        if not self.enabled:
            return []

        await self._apply_delay(0.2, 0.4)

        # Build API URL with pagination
        url = f"{self.api_url}{query}&site=stackoverflow&page={page}&pagesize=10"

        headers = self._get_fresh_headers({
            "Accept": "application/json",
            "User-Agent": "AtaqueTotal-Search/1.0",
        }, self._get_user_agents())

        try:
            timeout = 15
            async with session.get(url, headers=headers, timeout=timeout, ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_results(data, query)
                else:
                    print(f"[Error HTTP {response.status}] StackOverflow")
                    return []
        except asyncio.TimeoutError:
            print(f"[Timeout] StackOverflow took too long to respond")
            return []
        except ClientError as e:
            print(f"[Connection Error] StackOverflow: {str(e)[:50]}")
            return []
        except Exception as e:
            print(f"[Error] StackOverflow: {str(e)[:50]}")
            return []

    def parse_results(self, data: dict, query: str) -> List[Dict[str, Any]]:
        """Parse StackOverflow API results"""
        results = []
        
        try:
            items = data.get('items', [])
            
            for item in items:
                title = item.get('title', 'No title')
                url = item.get('link', '')
                score = item.get('score', 0)
                
                # Get snippet from body if available
                body = item.get('body', '')
                import re
                clean_body = re.sub(r'<[^>]+>', '', body)[:200] if body else 'No description'
                
                results.append({
                    "title": f"👍 {score} - {title}",
                    "url": url,
                    "content": clean_body,
                    "engine": self.name,
                    "category": self.category
                })
            
            return results
            
        except Exception as e:
            print(f"[Parse Error] StackOverflow: {str(e)[:50]}")
            return []

    @staticmethod
    def _get_user_agents() -> List[str]:
        """Common user agents"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        ]
