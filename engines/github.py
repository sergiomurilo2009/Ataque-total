"""
GitHub Search Engine - Uses official API
"""
from .base import BaseEngine
from typing import List, Dict, Any


class GitHubEngine(BaseEngine):
    """GitHub search using official API"""

    def __init__(self, enabled: bool = True):
        super().__init__("GitHub", "software", enabled)
        self.api_url = "https://api.github.com/search/repositories?q="

    async def search(self, session, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """Search GitHub via API"""
        from aiohttp import ClientError
        import asyncio

        if not self.enabled:
            return []

        await self._apply_delay(0.2, 0.4)

        # Build API URL with pagination
        url = f"{self.api_url}{query}&sort=stars&order=desc&per_page=10&page={page}"

        headers = self._get_fresh_headers({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AtaqueTotal-Search/1.0",
        }, self._get_user_agents())

        try:
            timeout = 15
            async with session.get(url, headers=headers, timeout=timeout, ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_results(data, query)
                elif response.status == 403:
                    print(f"[Rate Limit] GitHub API rate limited")
                    return []
                else:
                    print(f"[Error HTTP {response.status}] GitHub")
                    return []
        except asyncio.TimeoutError:
            print(f"[Timeout] GitHub took too long to respond")
            return []
        except ClientError as e:
            print(f"[Connection Error] GitHub: {str(e)[:50]}")
            return []
        except Exception as e:
            print(f"[Error] GitHub: {str(e)[:50]}")
            return []

    def parse_results(self, data: dict, query: str) -> List[Dict[str, Any]]:
        """Parse GitHub API results"""
        results = []
        
        try:
            items = data.get('items', [])
            
            for item in items:
                title = item.get('full_name', 'No title')
                description = item.get('description', '') or 'No description'
                url = item.get('html_url', '')
                stars = item.get('stargazers_count', 0)
                
                results.append({
                    "title": f"⭐ {stars} - {title}",
                    "url": url,
                    "content": description,
                    "engine": self.name,
                    "category": self.category
                })
            
            return results
            
        except Exception as e:
            print(f"[Parse Error] GitHub: {str(e)[:50]}")
            return []

    @staticmethod
    def _get_user_agents() -> List[str]:
        """Common user agents"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        ]
