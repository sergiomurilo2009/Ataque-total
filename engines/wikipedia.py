"""
Wikipedia Search Engine - Uses official API
"""
from .base import BaseEngine
from typing import List, Dict, Any


class WikipediaEngine(BaseEngine):
    """Wikipedia search using official API"""

    def __init__(self, enabled: bool = True):
        super().__init__("Wikipedia", "general", enabled)
        self.api_url = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch="

    async def search(self, session, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """Search Wikipedia via API"""
        from aiohttp import ClientError
        import asyncio

        if not self.enabled:
            return []

        await self._apply_delay(0.2, 0.4)

        # Build API URL - use HTTPS properly
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&srlimit=10&srprop=snippet"
        if page > 1:
            sroffset = (page - 1) * 10
            url += f"&sroffset={sroffset}"

        headers = {
            "Accept": "application/json",
            "User-Agent": "AtaqueTotal-Search/1.0 (contact: ataque-total@example.com)",
        }

        try:
            timeout = 15
            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_results(data, query)
                else:
                    print(f"[Error HTTP {response.status}] Wikipedia")
                    return []
        except asyncio.TimeoutError:
            print(f"[Timeout] Wikipedia took too long to respond")
            return []
        except ClientError as e:
            print(f"[Connection Error] Wikipedia: {str(e)[:50]}")
            return []
        except Exception as e:
            print(f"[Error] Wikipedia: {str(e)[:50]}")
            return []

    def parse_results(self, data: dict, query: str) -> List[Dict[str, Any]]:
        """Parse Wikipedia API results"""
        results = []
        
        try:
            search_data = data.get('query', {}).get('search', [])
            
            for item in search_data:
                title = item.get('title', 'No title')
                snippet = item.get('snippet', '')
                
                # Remove HTML tags from snippet
                import re
                clean_snippet = re.sub(r'<[^>]+>', '', snippet)
                
                # Build Wikipedia URL
                url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                
                results.append({
                    "title": title,
                    "url": url,
                    "content": clean_snippet or "No description",
                    "engine": self.name,
                    "category": self.category
                })
            
            return results
            
        except Exception as e:
            print(f"[Parse Error] Wikipedia: {str(e)[:50]}")
            return []

    @staticmethod
    def _get_user_agents() -> List[str]:
        """Common user agents"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        ]
