"""
DuckDuckGo Search Engine Parser
Uses HTML parsing for results
"""
from .base import BaseEngine
from typing import List, Dict, Any
import re


class DuckDuckGoEngine(BaseEngine):
    """DuckDuckGo search engine"""

    def __init__(self, enabled: bool = True):
        super().__init__("DuckDuckGo", "general", enabled)
        self.base_url = "https://html.duckduckgo.com/html/?q="
        self.page_param = "s"

    async def search(self, session, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """Perform DuckDuckGo search"""
        from aiohttp import ClientError
        import asyncio

        if not self.enabled:
            return []

        await self._apply_delay(0.3, 0.6)

        # Build URL with pagination
        url = f"{self.base_url}{query}"
        if page > 1:
            offset = (page - 1) * 10
            url += f"&{self.page_param}={offset}"

        headers = self._get_fresh_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }, self._get_user_agents())

        try:
            timeout = 20
            async with session.get(url, headers=headers, timeout=timeout, ssl=False) as response:
                if response.status == 200:
                    html_content = await response.text()
                    return self.parse_results(html_content, query)
                elif response.status == 403:
                    print(f"[Forbidden] DuckDuckGo blocked the request")
                    return []
                else:
                    print(f"[Error HTTP {response.status}] DuckDuckGo")
                    return []
        except asyncio.TimeoutError:
            print(f"[Timeout] DuckDuckGo took too long to respond")
            return []
        except ClientError as e:
            print(f"[Connection Error] DuckDuckGo: {str(e)[:50]}")
            return []
        except Exception as e:
            print(f"[Error] DuckDuckGo: {str(e)[:50]}")
            return []

    def parse_results(self, html_content: str, query: str) -> List[Dict[str, Any]]:
        """Parse DuckDuckGo results"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            results = []

            # DuckDuckGo HTML uses div.results div.result for organic results
            for item in soup.select('div.results div.result, div.result'):
                title_elem = item.select_one('a.result__a')
                url_elem = item.select_one('a.result__a')
                snippet_elem = item.select_one('a.result__snippet')
                
                # Alternative snippet selector
                if not snippet_elem:
                    snippet_elem = item.select_one('div.result__body')

                if title_elem and url_elem:
                    title = title_elem.get_text(strip=True)
                    raw_url = url_elem.get('href', '')
                    
                    # Handle DuckDuckGo redirect URLs
                    url = self._extract_real_url(raw_url)
                    
                    # Skip internal DDG links
                    if not url or url.startswith('//') or 'duckduckgo.com' in url:
                        continue
                    
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    
                    # Clean up snippet (remove extra spaces and newlines)
                    if snippet:
                        snippet = ' '.join(snippet.split())

                    if url and url.startswith('http'):
                        results.append({
                            "title": title or "No title",
                            "url": url,
                            "content": snippet or "No description",
                            "engine": self.name,
                            "category": self.category
                        })

            return results

        except ImportError:
            return self._parse_ddg_regex(html_content, query)
        except Exception as e:
            print(f"[Parse Error] DuckDuckGo: {str(e)[:50]}")
            return []
    
    def _extract_real_url(self, ddg_url: str) -> str:
        """Extract real URL from DuckDuckGo redirect links"""
        if not ddg_url:
            return ""
        
        # If it's already a real URL, return it
        if ddg_url.startswith('http') and 'duckduckgo.com' not in ddg_url:
            return ddg_url
        
        # DuckDuckGo usesudd parameter for real URLs
        try:
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(ddg_url)
            
            # Check for uddg parameter (DDG's redirect parameter)
            params = parse_qs(parsed.query)
            if 'uddg' in params:
                return params['uddg'][0]
            
            # Check for the URL itself in path
            if parsed.path and parsed.path.startswith('/'):
                # Sometimes the URL is encoded in the path
                pass
                
        except Exception:
            pass
        
        return ddg_url

    def _parse_ddg_regex(self, html_content: str, query: str) -> List[Dict[str, Any]]:
        """Fallback regex parser"""
        results = []
        pattern = r'<a class="result__a" href="([^"]+)".*?>(.*?)</a>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)

        for url, title_html in matches:
            if 'duckduckgo.com' not in url and url.startswith('http'):
                title = re.sub(r'<[^>]+>', '', title_html).strip()
                results.append({
                    "title": title or "No title",
                    "url": url,
                    "content": "No description",
                    "engine": self.name,
                    "category": self.category
                })

        return results

    @staticmethod
    def _get_user_agents() -> List[str]:
        """Common user agents"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        ]
