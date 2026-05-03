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

            # DuckDuckGo HTML uses div.result for organic results
            for item in soup.select('div.result'):
                title_elem = item.select_one('a.result__a')
                url_elem = item.select_one('a.result__a')
                snippet_elem = item.select_one('a.result__snippet')

                if title_elem and url_elem:
                    title = title_elem.get_text(strip=True)
                    raw_url = url_elem.get('href', '')
                    
                    # Extract real URL from DuckDuckGo redirect links
                    real_url = self._extract_real_url(raw_url)
                    
                    # Skip internal DuckDuckGo links and ads
                    if not real_url or 'duckduckgo.com' in real_url or '/y.js' in raw_url:
                        continue
                    
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                    if real_url and real_url.startswith('http'):
                        results.append({
                            "title": title or "No title",
                            "url": real_url,
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
        """Extract the real destination URL from DuckDuckGo redirect links"""
        if not ddg_url or 'duckduckgo.com/l/?uddg=' not in ddg_url:
            # If it's already a direct URL (starts with http), return it
            if ddg_url and ddg_url.startswith('http'):
                return ddg_url
            return ''
        
        try:
            from urllib.parse import unquote, parse_qs, urlparse
            
            # Extract the uddg parameter which contains the encoded URL
            parsed = urlparse(ddg_url)
            params = parse_qs(parsed.query)
            
            if 'uddg' in params:
                encoded_url = params['uddg'][0]
                # URL decode the result
                real_url = unquote(encoded_url)
                return real_url
        except Exception:
            pass
        
        return ''

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
