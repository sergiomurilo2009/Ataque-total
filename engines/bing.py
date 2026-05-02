"""
Bing Search Engine Parser - Uses BeautifulSoup for robust parsing
"""
from .base import BaseEngine
from typing import List, Dict, Any
import re


class BingEngine(BaseEngine):
    """Bing search engine with BeautifulSoup parsing"""
    
    def __init__(self, enabled: bool = True):
        super().__init__("Bing", "general", enabled)
        self.base_url = "https://www.bing.com/search?q="
        self.page_param = "first"
        
    async def search(self, session, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """Perform Bing search"""
        from aiohttp import ClientError
        import asyncio
        import time
        import random
        
        if not self.enabled:
            return []
        
        # Apply delay
        await self._apply_delay(0.4, 0.8)
        
        # Build URL with pagination
        url = f"{self.base_url}{query}"
        if page > 1:
            offset = (page - 1) * 10 + 1
            url += f"&{self.page_param}={offset}"
        
        headers = self._get_fresh_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
        }, self._get_user_agents())
        
        try:
            timeout = 20
            async with session.get(url, headers=headers, timeout=timeout, ssl=False) as response:
                if response.status == 200:
                    html_content = await response.text()
                    return self.parse_results(html_content, query)
                elif response.status == 429:
                    print(f"[Rate Limit] Bing: Too many requests")
                    return []
                else:
                    print(f"[Error HTTP {response.status}] Bing")
                    return []
        except asyncio.TimeoutError:
            print(f"[Timeout] Bing took too long to respond")
            return []
        except ClientError as e:
            print(f"[Connection Error] Bing: {str(e)[:50]}")
            return []
        except Exception as e:
            print(f"[Error] Bing: {str(e)[:50]}")
            return []
    
    def parse_results(self, html_content: str, query: str) -> List[Dict[str, Any]]:
        """Parse Bing results using BeautifulSoup"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            results = []
            
            # Bing uses li.b_algo for organic results
            for item in soup.select('li.b_algo'):
                title_elem = item.select_one('h2 a')
                url_elem = item.select_one('h2 a')
                snippet_elem = item.select_one('p.b_caption')
                
                if title_elem and url_elem:
                    title = title_elem.get_text(strip=True)
                    url = url_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    
                    # Filter internal Bing links
                    if url and 'bing.com' not in url.split('/')[2] if '/' in url else True:
                        results.append({
                            "title": title or "No title",
                            "url": url,
                            "content": snippet or "No description",
                            "engine": self.name,
                            "category": self.category
                        })
            
            return results
            
        except ImportError:
            # Fallback to regex if BeautifulSoup not available
            return self._parse_bing_regex(html_content, query)
        except Exception as e:
            print(f"[Parse Error] Bing: {str(e)[:50]}")
            return []
    
    def _parse_bing_regex(self, html_content: str, query: str) -> List[Dict[str, Any]]:
        """Fallback regex parser for Bing"""
        results = []
        pattern = r'<li class="b_algo"(.*?)</li>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            title_match = re.search(r'<h2.*?><a href="([^"]+)".*?>(.*?)</a>', match, re.DOTALL)
            snippet_match = re.search(r'<p class="b_caption"[^>]*>(.*?)</p>', match, re.DOTALL)
            
            if title_match:
                url = title_match.group(1)
                title = re.sub(r'<[^>]+>', '', title_match.group(2)).strip()
                snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip() if snippet_match else ""
                
                if 'bing.com' not in url or 'login' not in url:
                    results.append({
                        "title": title or "No title",
                        "url": url,
                        "content": snippet or "No description",
                        "engine": self.name,
                        "category": self.category
                    })
        
        return results
    
    @staticmethod
    def _get_user_agents() -> List[str]:
        """Common user agents for Bing"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        ]
