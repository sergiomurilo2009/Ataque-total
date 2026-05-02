"""
Bing Search Engine Parser - Uses BeautifulSoup for robust parsing
"""
from .base import BaseEngine
from typing import List, Dict, Any
import re
import base64
from urllib.parse import parse_qs, urlparse


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
                
                # Try alternative snippet selectors
                if not snippet_elem:
                    snippet_elem = item.select_one('.b_snippet')
                if not snippet_elem:
                    snippet_elem = item.select_one('.b_desc')
                if not snippet_elem:
                    # Fallback to any p tag with text content
                    snippet_elem = item.select_one('p')

                if title_elem and url_elem:
                    title = title_elem.get_text(strip=True)
                    raw_url = url_elem.get('href', '')
                    
                    # Extract real URL from Bing redirect links FIRST
                    real_url = self._extract_real_url(raw_url)
                    
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                    # Filter internal Bing links AFTER extracting real URL
                    should_include = False
                    if real_url and '/' in real_url:
                        domain = real_url.split('/')[2]
                        # Include if it's not a bing.com link
                        if 'bing.com' not in domain:
                            should_include = True
                    
                    if should_include:
                        results.append({
                            "title": title or "No title",
                            "url": real_url,
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

    def _extract_real_url(self, bing_url: str) -> str:
        """Extract the real destination URL from Bing redirect links"""
        if 'bing.com/ck/a' not in bing_url and 'bing.com/ac' not in bing_url:
            return bing_url
            
        try:
            parsed = urlparse(bing_url)
            # Bing stores the real URL in the 'u' parameter
            params = parse_qs(parsed.query)
            if 'u' in params:
                encoded_url = params['u'][0]
                
                # Remove 'a1' prefix if present (it's not part of base64)
                if encoded_url.startswith('a1'):
                    encoded_url = encoded_url[2:]
                
                # Add padding if needed for proper base64 decoding
                padding = 4 - len(encoded_url) % 4
                if padding != 4:
                    encoded_url += '=' * padding
                
                # Decode the base64-encoded URL
                decoded = base64.urlsafe_b64decode(encoded_url).decode('utf-8')
                return decoded
        except Exception:
            pass
        
        # Fallback: return original URL if extraction fails
        return bing_url

    def _parse_bing_regex(self, html_content: str, query: str) -> List[Dict[str, Any]]:
        """Fallback regex parser for Bing"""
        results = []
        pattern = r'<li class="b_algo"(.*?)</li>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)

        for match in matches:
            title_match = re.search(r'<h2.*?><a href="([^"]+)".*?>(.*?)</a>', match, re.DOTALL)
            snippet_match = re.search(r'<p[^>]*>(.*?)</p>', match, re.DOTALL)

            if title_match:
                url = title_match.group(1)
                title = re.sub(r'<[^>]+>', '', title_match.group(2)).strip()
                snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip() if snippet_match else ""

                # Extract real URL for regex fallback too
                real_url = self._extract_real_url(url)
                
                if 'bing.com' not in real_url or 'login' not in real_url:
                    results.append({
                        "title": title or "No title",
                        "url": real_url,
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
