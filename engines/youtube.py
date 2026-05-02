"""
YouTube Search Engine - Uses embedded search
"""
from .base import BaseEngine
from typing import List, Dict, Any
import re


class YouTubeEngine(BaseEngine):
    """YouTube search engine"""

    def __init__(self, enabled: bool = True):
        super().__init__("YouTube", "video", enabled)
        self.base_url = "https://www.youtube.com/results?search_query="

    async def search(self, session, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """Search YouTube"""
        from aiohttp import ClientError
        import asyncio

        if not self.enabled:
            return []

        await self._apply_delay(0.5, 1.0)

        # Build URL with pagination (YouTube doesn't have simple page param in HTML)
        url = f"{self.base_url}{query}"

        headers = self._get_fresh_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }, [])

        try:
            timeout = 30
            async with session.get(url, headers=headers, timeout=timeout, ssl=False) as response:
                if response.status == 200:
                    html_content = await response.text()
                    return self.parse_results(html_content, query)
                else:
                    print(f"[Error HTTP {response.status}] YouTube")
                    return []
        except asyncio.TimeoutError:
            print(f"[Timeout] YouTube took too long to respond")
            return []
        except ClientError as e:
            print(f"[Connection Error] YouTube: {str(e)[:50]}")
            return []
        except Exception as e:
            print(f"[Error] YouTube: {str(e)[:50]}")
            return []

    def parse_results(self, html_content: str, query: str) -> List[Dict[str, Any]]:
        """Parse YouTube results from HTML"""
        results = []
        
        try:
            # Look for video data in initial data
            import json
            
            # Try to find ytInitialData in the HTML - improved patterns
            patterns = [
                r'var\s+ytInitialData\s*=\s*(\{.*?\});',
                r'"ytInitialData"\s*:\s*(\{(?:[^{}]|(?1))*\})',
                r'ytInitialData\s*=\s*(\{.*?"trackingParams"[^\}]*\})',
            ]
            
            initial_data = None
            for pattern in patterns:
                match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if match:
                    try:
                        json_str = match.group(1)
                        # Clean up trailing issues
                        if not json_str.strip().endswith('}'):
                            json_str = json_str[:json_str.rfind('}')+1]
                        initial_data = json.loads(json_str)
                        break
                    except Exception as je:
                        continue
            
            if initial_data:
                # Navigate through the data structure
                contents = initial_data.get('contents', {})
                two_column_search = contents.get('twoColumnSearchResultsRenderer', {})
                primary_contents = two_column_search.get('primaryContents', {})
                section_list = primary_contents.get('sectionListRenderer', {})
                contents_list = section_list.get('contents', [])
                
                for section in contents_list:
                    item_section = section.get('itemSectionRenderer', {})
                    section_contents = item_section.get('contents', [])
                    
                    for content in section_contents:
                        video_renderer = content.get('videoRenderer', {})
                        if video_renderer:
                            title_runs = video_renderer.get('title', {}).get('runs', [])
                            title = ''.join([run.get('text', '') for run in title_runs])
                            
                            video_id = video_renderer.get('videoId', '')
                            url = f"https://www.youtube.com/watch?v={video_id}"
                            
                            desc_runs = video_renderer.get('descriptionSnippet', {}).get('runs', [])
                            description = ''.join([run.get('text', '') for run in desc_runs]) or 'No description'
                            
                            if title and video_id:
                                results.append({
                                    "title": f"🎬 {title}",
                                    "url": url,
                                    "content": description[:200],
                                    "engine": self.name,
                                    "category": self.category
                                })
            
            return results[:10]  # Limit to 10 results
            
        except Exception as e:
            print(f"[Parse Error] YouTube: {str(e)[:50]}")
            return []

    @staticmethod
    def _get_user_agents() -> List[str]:
        """Common user agents"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        ]
