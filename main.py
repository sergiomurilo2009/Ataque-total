import asyncio
import aiohttp
import json
import argparse
import webbrowser
import random
import re
import html
from urllib.parse import quote_plus, urlparse, parse_qs
from datetime import datetime
from pathlib import Path
import time

# Configurações Globais
CONFIG_FILE = Path("searxng_config.json")
PORT = 8080
HOST = "127.0.0.1"

# User Agents extensos para evitar bloqueios - ROTATIVO (80+ user agents)
USER_AGENTS = [
    # Chrome Windows (versões recentes)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    # Chrome Android (mobile)
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    # iPhone Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    # iPad Safari
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    # Opera Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0",
    # Vivaldi Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Vivaldi/6.5",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Vivaldi/6.6",
    # Samsung Internet
    "Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.36",
    # Mi Browser
    "Mozilla/5.0 (Linux; Android 12; M2102J20SG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36 XiaoMi/Mi Browser/1.8",
]

# Headers base mais completos e realistas
BASE_HEADERS = {
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8,en-US;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="124"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

# Headers específicos por engine para evitar bloqueios - OTIMIZADOS
ENGINE_SPECIFIC_HEADERS = {
    "Google": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    },
    "Bing": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
    },
    "DuckDuckGo": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://duckduckgo.com/",
    },
    "Yandex": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    },
    "YouTube": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "X-Client-Data": "CKG1yQE=",
    },
    "Qwant": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.qwant.com/",
    },
    "Startpage": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.startpage.com/",
    },
    "GitHub": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Sec-Fetch-Dest": "document",
    },
    "Wikipedia": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    },
    "StackOverflow": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    },
    "GitLab": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    },
    "Dailymotion": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    },
}

# Delay entre requisições (em segundos) - OTIMIZADO para melhor performance e menos bloqueios
REQUEST_DELAY_MIN = 0.3  # Reduzido para APIs oficiais
REQUEST_DELAY_MAX = 0.8  # Reduzido para melhor performance

# Delay específico por engine (segundos)
ENGINE_DELAYS = {
    "Google": (0.5, 1.0),      # Google tem detecção rigorosa
    "Bing": (0.4, 0.8),
    "DuckDuckGo": (0.3, 0.6),  # DuckDuckGo é mais amigável
    "Yandex": (0.4, 0.8),
    "YouTube": (0.5, 1.0),     # YouTube também tem detecção
    "Qwant": (0.3, 0.6),
    "Startpage": (0.3, 0.6),
    "GitHub": (0.2, 0.4),      # APIs oficiais são mais rápidas
    "GitLab": (0.2, 0.4),
    "Wikipedia": (0.2, 0.4),
    "StackOverflow": (0.2, 0.4),
    "Dailymotion": (0.3, 0.6),
}

# Timeout específico por engine (segundos)
ENGINE_TIMEOUTS = {
    "Google": 25,
    "Bing": 20,
    "DuckDuckGo": 20,
    "Yandex": 20,
    "YouTube": 30,              # YouTube pode demorar mais
    "Qwant": 20,
    "Startpage": 20,
    "GitHub": 15,
    "GitLab": 15,
    "Wikipedia": 15,
    "StackOverflow": 15,
    "Dailymotion": 20,
}

# Limite de conexões simultâneas - Aumentado para melhor throughput
MAX_CONCURRENT_CONNECTIONS = 10

# Retry settings para requisições falhas
MAX_RETRIES = 2
RETRY_DELAY = 1.0

class SearchEngine:
    def __init__(self, name, base_url, search_param, category, enabled=True, api_url=None, page_param=None):
        self.name = name
        self.base_url = base_url
        self.search_param = search_param
        self.category = category
        self.enabled = enabled
        self.api_url = api_url  # URL alternativa para API oficial
        self.page_param = page_param  # Parâmetro de paginação (ex: 'start', 'page')
        self.request_count = 0  # Contador para delays
        self.last_request_time = 0  # Timestamp da última requisição

    def _get_fresh_headers(self):
        """Gera headers completos e rotativos para cada requisição"""
        user_agent = random.choice(USER_AGENTS)
        headers = BASE_HEADERS.copy()
        headers["User-Agent"] = user_agent
        
        # Adiciona headers específicos por engine para evitar bloqueios
        if self.name in ENGINE_SPECIFIC_HEADERS:
            headers.update(ENGINE_SPECIFIC_HEADERS[self.name])
        
        # Se for usar API URL, definir Accept como JSON
        if self.api_url:
            headers["Accept"] = "application/json"
            # Wikipedia requer User-Agent informativo
            if "wikipedia.org" in self.api_url:
                headers["User-Agent"] = "SearchApp/1.0 (contact: info@example.com)"
        
        return headers

    async def _apply_delay(self):
        """Aplica delay aleatório específico por engine para evitar bloqueios"""
        now = time.time()
        elapsed = now - self.last_request_time
        
        # Usa delay específico da engine se disponível
        if self.name in ENGINE_DELAYS:
            min_delay, max_delay = ENGINE_DELAYS[self.name]
        else:
            min_delay, max_delay = REQUEST_DELAY_MIN, REQUEST_DELAY_MAX
        
        if elapsed < min_delay:
            delay = random.uniform(min_delay, max_delay)
            await asyncio.sleep(delay)
        self.last_request_time = time.time()

    async def search(self, session, query, retry_count=0, page=1):
        if not self.enabled:
            return []
        
        # Aplica delay antes da requisição (reduzido para APIs oficiais)
        if self.api_url:
            # APIs oficiais tem delay menor
            await asyncio.sleep(random.uniform(0.15, 0.3))
        else:
            await self._apply_delay()
        
        # Rotação de User-Agent a cada requisição
        headers = self._get_fresh_headers()
        
        # Determina URL (API oficial ou scraping) com paginação
        if self.api_url:
            url = f"{self.api_url}{quote_plus(query)}"
            # Para APIs JSON, usar headers apropriados
            if "api.php" in self.api_url or "/api/" in self.api_url:
                headers["Accept"] = "application/json"
        else:
            # Constrói URL com query - URLs já incluem o separador correto
            url = f"{self.base_url}{quote_plus(query)}"
            # Adiciona paginação se suportado
            if page > 1 and self.page_param:
                # Calcula offset baseado na página (10 resultados por página)
                if self.name == "Google":
                    # Google usa start=0, start=10, start=20...
                    start = (page - 1) * 10
                    url += f"&{self.page_param}={start}"
                elif self.name in ["Bing", "DuckDuckGo", "Yandex"]:
                    # Bing usa first=11, first=21... DuckDuckGo usa s=10, s=20...
                    offset = (page - 1) * 10 + (1 if self.name == "Bing" else 0)
                    url += f"&{self.page_param}={offset}"
                else:
                    # Outros usam page=2, page=3...
                    url += f"&{self.page_param}={page}"
        
        try:
            self.request_count += 1
            # Timeout específico por engine
            timeout = ENGINE_TIMEOUTS.get(self.name, 20 if not self.api_url else 15)
            async with session.get(url, headers=headers, timeout=timeout, ssl=False, allow_redirects=True) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    
                    # Se for API JSON, processar como JSON
                    if 'application/json' in content_type or (self.api_url and ('api.php' in self.api_url or '/api/' in self.api_url)):
                        json_data = await response.json()
                        return self.parse_api_results(json_data, query)
                    else:
                        html_content = await response.text()
                        return self.parse_results(html_content, query)
                elif response.status == 429:
                    print(f"[Rate Limit] {self.name}: Aguardando {RETRY_DELAY}s antes de retry...")
                    if retry_count < MAX_RETRIES:
                        await asyncio.sleep(RETRY_DELAY * (retry_count + 1))
                        return await self.search(session, query, retry_count + 1)
                    print(f"[Bloqueio] {self.name}: Rate limit atingido (429) após {MAX_RETRIES} retries")
                    return []
                elif response.status == 403:
                    # Tenta com outro user agent em caso de 403
                    if retry_count < MAX_RETRIES:
                        print(f"[Tentativa {retry_count + 1}/{MAX_RETRIES}] {self.name}: 403 - Tentando novamente...")
                        await asyncio.sleep(RETRY_DELAY)
                        return await self.search(session, query, retry_count + 1)
                    print(f"[Bloqueio] {self.name}: Acesso negado (403) após {MAX_RETRIES} retries")
                    return []
                elif response.status == 503:
                    print(f"[Serviço Indisponível] {self.name}: 503 - Service Unavailable")
                    return []
                elif response.status == 400:
                    print(f"[Erro HTTP 400] {self.name} - Bad Request (possível bloqueio ou parâmetros inválidos)")
                    return []
                else:
                    print(f"[Erro HTTP {response.status}] {self.name}")
                    return []
        except asyncio.TimeoutError:
            if retry_count < MAX_RETRIES:
                print(f"[Timeout] {self.name}: Tentando novamente ({retry_count + 1}/{MAX_RETRIES})...")
                await asyncio.sleep(RETRY_DELAY)
                return await self.search(session, query, retry_count + 1)
            print(f"[Timeout] {self.name} demorou muito para responder após {MAX_RETRIES} retries")
            return []
        except aiohttp.ClientError as e:
            error_msg = str(e)[:100]
            if retry_count < MAX_RETRIES:
                print(f"[Erro Conexão] {self.name}: {error_msg[:50]} - Retrying...")
                await asyncio.sleep(RETRY_DELAY)
                return await self.search(session, query, retry_count + 1)
            print(f"[Falha Conexão] {self.name}: {error_msg}")
            return []
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"[Falha] {self.name}: {error_msg}")
            return []

    def parse_api_results(self, json_data, query):
        """Processa resultados de APIs oficiais (JSON)"""
        results = []
        
        if self.name == "Wikipedia":
            results = self._parse_wikipedia_api(json_data)
        elif self.name == "GitHub":
            results = self._parse_github_api(json_data)
        elif self.name == "GitLab":
            results = self._parse_gitlab_api(json_data)
        elif self.name == "Reddit":
            results = self._parse_reddit_api(json_data)
        elif self.name == "StackOverflow":
            results = self._parse_stackoverflow_api(json_data)
        else:
            # Fallback para parsing genérico de API JSON
            results = self._parse_generic_api(json_data)
            
        return results

    def _parse_wikipedia_api(self, json_data):
        """Parse da API oficial da Wikipedia"""
        results = []
        try:
            search_results = json_data.get('query', {}).get('search', [])
            for item in search_results:  # Sem limite - retorna todos os resultados
                title = item.get('title', 'Sem título')
                snippet = item.get('snippet', 'Sem descrição')
                # Limpar HTML do snippet da Wikipedia
                snippet = re.sub(r'<[^>]+>', '', snippet)
                results.append({
                    "title": title,
                    "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    "content": snippet,
                    "engine": self.name,
                    "category": self.category
                })
        except Exception as e:
            print(f"[Erro Parse Wikipedia API] {str(e)[:50]}")
        return results

    def _parse_github_api(self, json_data):
        """Parse da API oficial do GitHub"""
        results = []
        try:
            items = json_data.get('items', [])
            for item in items:  # Sem limite - retorna todos os resultados
                title = item.get('full_name', 'Sem título')
                description = item.get('description', 'Sem descrição') or 'Sem descrição'
                html_url = item.get('html_url', '')
                results.append({
                    "title": title,
                    "url": html_url,
                    "content": description,
                    "engine": self.name,
                    "category": self.category
                })
        except Exception as e:
            print(f"[Erro Parse GitHub API] {str(e)[:50]}")
        return results

    def _parse_gitlab_api(self, json_data):
        """Parse da API oficial do GitLab"""
        results = []
        try:
            for item in json_data:  # Sem limite - retorna todos os resultados
                title = item.get('name_with_namespace', 'Sem título')
                description = item.get('description', 'Sem descrição') or 'Sem descrição'
                html_url = item.get('web_url', '')
                results.append({
                    "title": title,
                    "url": html_url,
                    "content": description,
                    "engine": self.name,
                    "category": self.category
                })
        except Exception as e:
            print(f"[Erro Parse GitLab API] {str(e)[:50]}")
        return results

    def _parse_reddit_api(self, json_data):
        """Parse da API oficial do Reddit (JSON)"""
        results = []
        try:
            posts = json_data.get('data', {}).get('children', [])
            for post in posts:  # Sem limite - retorna todos os resultados
                data = post.get('data', {})
                title = data.get('title', 'Sem título')
                subreddit = data.get('subreddit', 'unknown')
                permalink = data.get('permalink', '')
                url = f"https://www.reddit.com{permalink}" if permalink else data.get('url', '')
                content = data.get('selftext', 'Sem descrição') or data.get('title', 'Sem descrição')
                results.append({
                    "title": f"r/{subreddit}: {title}",
                    "url": url,
                    "content": content[:200] if len(content) > 200 else content,
                    "engine": self.name,
                    "category": self.category
                })
        except Exception as e:
            print(f"[Erro Parse Reddit API] {str(e)[:50]}")
        return results

    def _parse_stackoverflow_api(self, json_data):
        """Parse da API oficial do Stack Exchange/StackOverflow"""
        results = []
        try:
            items = json_data.get('items', [])
            for item in items:  # Sem limite - retorna todos os resultados
                title = item.get('title', 'Sem título')
                question_id = item.get('question_id', '')
                link = item.get('link', f'https://stackoverflow.com/questions/{question_id}')
                snippet = item.get('body', 'Sem descrição') or 'Sem descrição'
                # Limpar HTML do snippet
                snippet = re.sub(r'<[^>]+>', '', snippet)
                results.append({
                    "title": title,
                    "url": link,
                    "content": snippet[:200] if len(snippet) > 200 else snippet,
                    "engine": self.name,
                    "category": self.category
                })
        except Exception as e:
            print(f"[Erro Parse StackOverflow API] {str(e)[:50]}")
        return results

    def _parse_generic_api(self, json_data):
        """Parse genérico para APIs JSON"""
        results = []
        # Tenta extrair dados de forma genérica
        try:
            if isinstance(json_data, dict):
                for key, value in json_data.items():
                    if isinstance(value, list):
                        for item in value:  # Sem limite - retorna todos os resultados
                            if isinstance(item, dict):
                                title = item.get('title', item.get('name', 'Resultado'))
                                url = item.get('url', item.get('link', item.get('html_url', '#')))
                                content = item.get('description', item.get('snippet', 'Sem descrição'))
                                results.append({
                                    "title": str(title),
                                    "url": str(url),
                                    "content": str(content),
                                    "engine": self.name,
                                    "category": self.category
                                })
        except Exception as e:
            print(f"[Erro Parse Genérico API] {str(e)[:50]}")
        return results

    def parse_results(self, html_content, query):
        results = []
        
        # Lógica específica por engine
        if self.name == "Bing":
            results = self._parse_bing(html_content)
        elif self.name == "DuckDuckGo":
            results = self._parse_ddg(html_content)
        elif self.name == "Yandex":
            results = self._parse_yandex(html_content)
        elif self.name == "GitHub":
            results = self._parse_github(html_content)
        elif self.name == "Wikipedia":
            results = self._parse_wiki(html_content)
        elif self.name == "Reddit":
            results = self._parse_reddit(html_content)
        elif self.name == "StackOverflow":
            results = self._parse_so(html_content)
        elif self.name == "YouTube":
            results = self._parse_youtube(html_content)
        elif self.name == "Ecosia":
            results = self._parse_ecosia(html_content)
        elif self.name == "Qwant":
            results = self._parse_qwant(html_content)
        else:
            results = self._parse_generic(html_content)
            
        return results

    def _clean_text(self, text):
        if not text: 
            return ""
        # Remove tags HTML e decodifica entidades
        clean = re.sub(r'<[^>]+>', '', text)
        clean = html.unescape(clean)
        return clean.strip()

    def _parse_bing(self, html_content):
        results = []
        # Padrão do Bing para resultados orgânicos
        pattern = r'<li class="b_algo"(.*?)</li>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:  # Sem limite - retorna todos os resultados
            title_match = re.search(r'<h2.*?><a href="([^"]+)".*?>(.*?)</a>', match, re.DOTALL)
            snippet_match = re.search(r'<p class="b_caption"[^>]*>(.*?)</p>', match, re.DOTALL)
            
            if title_match:
                url = title_match.group(1)
                title = self._clean_text(title_match.group(2))
                snippet = self._clean_text(snippet_match.group(1)) if snippet_match else ""
                
                # Filtrar links internos do Bing
                if "bing.com" not in url or "login" not in url:
                    results.append({
                        "title": title if title else "Sem título",
                        "url": url,
                        "content": snippet if snippet else "Sem descrição",
                        "engine": self.name,
                        "category": self.category
                    })
        return results

    def _parse_ddg(self, html_content):
        """Parser para DuckDuckGo HTML - Versão melhorada"""
        results = []
        seen = set()
        
        # DuckDuckGo HTML usa estrutura: div.links_main.result__body
        pattern = r'<div class="links_main links_deep result__body"[^>]*>(.*?)</div>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches[:20]:
            # Extrai titulo e URL do link principal
            title_match = re.search(r'<a rel="nofollow" class="result__a" href="([^"]+)">([^<]+)</a>', match, re.DOTALL)
            snippet_match = re.search(r'<a class="result__snippet"[^>]*>(.*?)</a>', match, re.DOTALL)
            
            if title_match:
                url_raw = title_match.group(1)
                title = self._clean_text(title_match.group(2))
                
                # Decodifica URL do DuckDuckGo (redirect)
                url = url_raw
                if "uddg=" in url_raw:
                    try:
                        from urllib.parse import unquote, parse_qs, urlparse
                        parsed = urlparse(url_raw)
                        params = parse_qs(parsed.query)
                        if 'uddg' in params:
                            url = unquote(params['uddg'][0])
                    except:
                        pass
                
                if url.startswith("//"): 
                    url = "https:" + url
                
                snippet = ""
                if snippet_match:
                    snippet = self._clean_text(snippet_match.group(1))
                
                # Filtra duplicatas e URLs vazias
                if url and len(title) > 3 and url not in seen and "duckduckgo.com" not in url.split('/')[2]:
                    seen.add(url)
                    results.append({
                        "title": title if title else "Sem título",
                        "url": url,
                        "content": snippet if snippet else "Sem descrição",
                        "engine": self.name,
                        "category": self.category
                    })
        
        return results


    def _parse_yandex(self, html_content):
        results = []
        # Yandex - classe serp-item
        pattern = r'<li class="serp-item"(.*?)</li>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:  # Sem limite - retorna todos os resultados
            title_match = re.search(r'<a class="OrganicTitle-LinkText"[^>]*href="([^"]+)".*?>(.*?)</a>', match, re.DOTALL)
            snippet_match = re.search(r'<span class="OrganicText-Content"[^>]*>(.*?)</span>', match, re.DOTALL)
            
            if title_match:
                url = title_match.group(1)
                if url.startswith("/"): 
                    url = "https://yandex.com" + url
                
                title = self._clean_text(title_match.group(2))
                snippet = self._clean_text(snippet_match.group(1)) if snippet_match else ""
                
                # Filtrar anúncios e links internos
                if url and "yandex.com" not in url.split('/')[2] if '/' in url else True:
                    results.append({
                        "title": title if title else "Sem título",
                        "url": url,
                        "content": snippet if snippet else "Sem descrição",
                        "engine": self.name,
                        "category": self.category
                    })
        return results

    def _parse_github(self, html_content):
        results = []
        pattern = r'<li class="repo-list-item"(.*?)</li>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:  # Sem limite - retorna todos os resultados
            title_match = re.search(r'<a href="([^"]+)" class="v-align-middle">.*?<span>(.*?)</span>', match, re.DOTALL)
            snippet_match = re.search(r'<p class="col-9 color-fg-muted my-1 pr-4">(.*?)</p>', match, re.DOTALL)
            
            if title_match:
                url = "https://github.com" + title_match.group(1)
                title = self._clean_text(title_match.group(2))
                snippet = self._clean_text(snippet_match.group(1)) if snippet_match else ""
                
                results.append({
                    "title": title if title else "Sem título",
                    "url": url,
                    "content": snippet if snippet else "Sem descrição",
                    "engine": self.name,
                    "category": self.category
                })
        return results

    def _parse_wiki(self, html_content):
        results = []
        pattern = r'<div class="mw-search-result-heading"(.*?)</div>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:  # Sem limite - retorna todos os resultados
            title_match = re.search(r'<a href="([^"]+)".*?>(.*?)</a>', match, re.DOTALL)
            if title_match:
                url = "https://wikipedia.org" + title_match.group(1)
                title = self._clean_text(title_match.group(2))
                results.append({
                    "title": title if title else "Sem título",
                    "url": url,
                    "content": "Artigo da Wikipedia",
                    "engine": self.name,
                    "category": self.category
                })
        return results

    def _parse_reddit(self, html_content):
        results = []
        # Reddit é complicado pois requer JS, tentaremos pegar links diretos
        pattern = r'<shreddit-post(.*?)</shreddit-post>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        if not matches:
            # Fallback para links genéricos do reddit
            links = re.findall(r'<a href="(https://www\.reddit\.com/r/[^"]+)".*?>([^<]{20,100})</a>', html_content)
            for url, title in links:  # Sem limite - retorna todos os resultados
                results.append({
                    "title": self._clean_text(title),
                    "url": url,
                    "content": "Discussão no Reddit",
                    "engine": self.name,
                    "category": self.category
                })
        else:
            for match in matches:  # Sem limite - retorna todos os resultados
                title_match = re.search(r'slot="title".*?>(.*?)<', match, re.DOTALL)
                link_match = re.search(r'href="([^"]+)"', match)
                if title_match and link_match:
                    results.append({
                        "title": self._clean_text(title_match.group(1)),
                        "url": "https://reddit.com" + link_match.group(1),
                        "content": "Post do Reddit",
                        "engine": self.name,
                        "category": self.category
                    })
        return results

    def _parse_so(self, html_content):
        results = []
        pattern = r'<div class="question-summary"(.*?)</div>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:  # Sem limite - retorna todos os resultados
            title_match = re.search(r'<a class="question-hyperlink" href="([^"]+)".*?>(.*?)</a>', match, re.DOTALL)
            if title_match:
                url = "https://stackoverflow.com" + title_match.group(1)
                title = self._clean_text(title_match.group(2))
                results.append({
                    "title": title if title else "Sem título",
                    "url": url,
                    "content": "Questão no Stack Overflow",
                    "engine": self.name,
                    "category": self.category
                })
        return results

    def _parse_youtube(self, html_content):
        """Parser para YouTube - Versão melhorada com múltiplos padrões"""
        results = []
        seen = set()
        
        # Padrões para extrair vídeos do YouTube (HTML inicial tem dados limitados)
        patterns = [
            # Padrão 1: link completo com title attribute
            r'<a href="(/watch\?v=[^"]+)"[^>]*title="([^"]+)"',
            # Padrão 2: videoId em ytInitialData
            r'"videoId":"([a-zA-Z0-9_-]+)".*?"title":"([^"]+)"',
            # Padrão 3: link simplificado
            r'href="(/watch\?v=[a-zA-Z0-9_-]+)"[^>]*>([^<]{10,100})',
            # Padrão 4: título em h3 ou h2
            r'<a href="(/watch\?v=[a-zA-Z0-9_-]+)".*?><h[23][^>]*>([^<]+)</h[23]>',
        ]
        
        for pattern in patterns:
            try:
                links = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
                for match in links:  # Sem limite - retorna todos os resultados
                    url = match[0]
                    title = match[1] if len(match) > 1 else ""
                    
                    # Limpar título de entidades HTML
                    title = html.unescape(title)
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    
                    # Normalizar URL
                    if not url.startswith('/watch'):
                        url = f"/watch?v={url}"
                    if not url.startswith('http'):
                        full_url = "https://www.youtube.com" + url
                    else:
                        full_url = url
                    
                    # Filtrar duplicatas e títulos vazios
                    if full_url not in seen and len(title) > 5:
                        seen.add(full_url)
                        results.append({
                            "title": title[:100],  # Limitar tamanho do título
                            "url": full_url,
                            "content": "Vídeo no YouTube",
                            "engine": self.name,
                            "category": self.category
                        })
            except Exception:
                continue
        
        return results

    def _parse_ecosia(self, html_content):
        """Parser para Ecosia - motor de busca ecológico"""
        results = []
        # Ecosia usa estrutura similar
        pattern = r'<div class="result__body"(.*?)</div>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:  # Sem limite - retorna todos os resultados
            title_match = re.search(r'<a class="result__link" href="([^"]+)".*?>(.*?)</a>', match, re.DOTALL)
            snippet_match = re.search(r'<p class="result__snippet"[^>]*>(.*?)</p>', match, re.DOTALL)
            
            if title_match:
                url = title_match.group(1)
                title = self._clean_text(title_match.group(2))
                snippet = self._clean_text(snippet_match.group(1)) if snippet_match else ""
                
                if url.startswith("//"):
                    url = "https:" + url
                
                results.append({
                    "title": title if title else "Sem título",
                    "url": url,
                    "content": snippet if snippet else "Resultado do Ecosia",
                    "engine": self.name,
                    "category": self.category
                })
        
        # Fallback para padrão genérico se não encontrar resultados
        if not results:
            results = self._parse_generic(html_content)
        
        return results

    def _parse_qwant(self, html_content):
        """Parser para Qwant - motor de busca europeu"""
        results = []
        # Qwant tem estrutura própria - fallback para genérico
        results = self._parse_generic(html_content)
        return results

    def _parse_generic(self, html_content):
        """Parser genérico melhorado com múltiplos padrões de fallback"""
        results = []
        seen = set()
        
        # Padrão 1: Links com título descritivo (20-150 chars)
        links = re.findall(r'<a href="(https?://[^"]+)"[^>]*>([^<]{20,150})</a>', html_content)
        
        # Padrão 2: Links em divs ou spans de resultado
        if not links:
            links = re.findall(r'<div[^>]*class="[^"]*result[^"]*"[^>]*>.*?<a href="(https?://[^"]+)".*?>([^<]{10,200})</a>', html_content, re.DOTALL)
        
        # Padrão 3: Links em h2/h3 headings
        if not links:
            links = re.findall(r'<h[23][^>]*><a href="(https?://[^"]+)".*?>([^<]{10,150})</a></h[23]>', html_content)
        
        # Padrão 4: Fallback mais amplo
        if not links:
            links = re.findall(r'<a href="(https?://[^"]+)"[^>]*title="([^"]{10,150})"', html_content)
        
        for url, title in links:
            # Limpar título
            title = self._clean_text(title)
            
            # Filtrar URLs indesejadas e duplicatas
            if (url not in seen and 
                len(title) > 10 and 
                'javascript:' not in url and
                '#' not in url.split('/')[0] and
                not url.endswith(('.css', '.js', '.png', '.jpg', '.gif'))):
                
                seen.add(url)
                results.append({
                    "title": title[:150],  # Limitar tamanho
                    "url": url,
                    "content": f"Resultado de {self.name}",
                    "engine": self.name,
                    "category": self.category
                })
        
        return results


class SearXNGCore:
    def __init__(self):
        self.engines = []
        self.load_config()
        if not self.engines:
            self.init_default_engines()

    def init_default_engines(self):
        # Lista completa de Engines com URLs otimizadas
        # Priorizando APIs oficiais quando disponíveis para resultados mais confiáveis
        # Estratégia anti-bloqueio: múltiplos fallbacks e rotação de user agents
        
        # Nota: Alguns engines estão desabilitados por padrão devido a bloqueios agressivos
        # Muitos sites usam proteções anti-bot (Cloudflare, Akamai, etc.) que impedem scraping
        
        # APIs Oficiais (prioridade máxima - não requerem scraping, mais estáveis)
        self.engines = [
            # Wikipedia API Oficial - Muito confiável
            SearchEngine(
                "Wikipedia", 
                "https://en.wikipedia.org/w/index.php", 
                "search", 
                "science",
                api_url="https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srprop=snippet|title&srlimit=10&srsearch="
            ),
            # GitHub API Oficial - Resultados precisos
            SearchEngine(
                "GitHub", 
                "https://github.com/search", 
                "q", 
                "it",
                api_url="https://api.github.com/search/repositories?q="
            ),
            # GitLab - API Oficial (public projects endpoint)
            SearchEngine(
                "GitLab", 
                "https://gitlab.com/search", 
                "search", 
                "it",
                api_url="https://gitlab.com/api/v4/projects?search="
            ),
            # StackOverflow - Stack Exchange API Oficial
            SearchEngine(
                "StackOverflow", 
                "https://stackoverflow.com/search", 
                "q", 
                "it",
                api_url="https://api.stackexchange.com/2.3/search?order=desc&sort=relevance&site=stackoverflow&intitle="
            ),
            # Google - Scraping via interface web (requer paginação)
            SearchEngine("Google", "https://www.google.com/search?q=", "q", "general", page_param="start"),
            # DuckDuckGo HTML (não tem API oficial, mas versão HTML é amigável)
            SearchEngine("DuckDuckGo", "https://html.duckduckgo.com/html?q=", "q", "general", page_param="s"),
            # Bing - Scraping com headers melhorados
            SearchEngine("Bing", "https://www.bing.com/search?q=", "q", "general", page_param="first"),
            # Brave Search - DESABILITADO: Proteções anti-bot rigorosas (429/403)
            SearchEngine("Brave", "https://search.brave.com/search?q=", "q", "general", page_param="page", enabled=False),
            # Yandex - DESABILITADO: Requer captcha/verificação humana (redireciona para /showcaptcha)
            SearchEngine("Yandex", "https://yandex.ru/search/?text=", "text", "general", page_param="p", enabled=False),
            # Reddit - DESABILITADO: Requer JavaScript/bot detection (403)
            SearchEngine(
                "Reddit", 
                "https://old.reddit.com/search?q=", 
                "q", 
                "social",
                page_param="page",
                enabled=False
            ),
            # YouTube - Scraping (YouTube Data API v3 requer chave, usando scraping como fallback)
            SearchEngine("YouTube", "https://www.youtube.com/results?search_query=", "search_query", "videos", page_param="page"),
            # Dailymotion - Scraping
            SearchEngine("Dailymotion", "https://www.dailymotion.com/search/", "query", "videos", page_param="page"),
            # Pexels - DESABILITADO: Proteções anti-bot rigorosas (403)
            SearchEngine("Pexels", "https://www.pexels.com/search/", "q", "images", page_param="page", enabled=False),
            # Ecosia - DESABILITADO: Proteções anti-bot rigorosas (403)
            SearchEngine("Ecosia", "https://www.ecosia.org/search?q=", "q", "general", page_param="page", enabled=False),
            # Qwant - Motor de busca europeu focado em privacidade
            SearchEngine("Qwant", "https://www.qwant.com/?q=", "q", "general", page_param="page"),
            # Startpage - Motor de busca focado em privacidade (resultados do Google)
            SearchEngine("Startpage", "https://www.startpage.com/sp/search?query=", "query", "general", page_param="page"),
            # Mojeek - DESABILITADO: Proteções anti-bot (403)
            SearchEngine("Mojeek", "https://www.mojeek.com/search?q=", "q", "general", page_param="page", enabled=False),
            # Metacrawler - DESABILITADO: Proteções anti-bot (403)
            SearchEngine("Metacrawler", "https://www.metacrawler.com/web?q=", "q", "general", page_param="page", enabled=False),
            # Lycos - DESABILITADO: Problemas de conexão DNS
            SearchEngine("Lycos", "https://search.lycos.com/web?q=", "q", "general", page_param="page", enabled=False),
            # AOL Search - DESABILITADO: Retornando 404
            SearchEngine("AOL", "https://search.aol.com/aol/search?q=", "q", "general", page_param="page", enabled=False),
        ]

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print("✓ Configuração carregada.")
            except Exception as e:
                print(f"⚠ Erro ao ler config: {e}")

    def save_config(self):
        data = {"engines": [{"name": e.name, "enabled": e.enabled} for e in self.engines]}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    async def search_all(self, query, categories=None, page=1):
        if not query:
            return []
        
        # Verificar Bangs (!google, !wiki, etc)
        bang_engine = None
        if query.startswith('!'):
            parts = query.split(' ', 1)
            bang_cmd = parts[0].lower()
            remaining_query = parts[1] if len(parts) > 1 else ""
            
            # Mapeamento de Bangs
            bang_map = {
                "!google": "Bing",
                "!bing": "Bing",
                "!ddg": "DuckDuckGo",
                "!wiki": "Wikipedia",
                "!gh": "GitHub",
                "!github": "GitHub",
                "!yt": "YouTube",
                "!reddit": "Reddit",
                "!so": "StackOverflow",
                "!brave": "Brave"
            }
            
            if bang_cmd in bang_map:
                target_name = bang_map[bang_cmd]
                for eng in self.engines:
                    if eng.name == target_name:
                        bang_engine = eng
                        query = remaining_query
                        break
        
        active_engines = []
        if bang_engine:
            active_engines = [bang_engine]
        else:
            for eng in self.engines:
                if eng.enabled:
                    if categories is None or eng.category in categories:
                        active_engines.append(eng)

        if not query:
            return []

        # Configurar Connector com limite de conexões simultâneas
        connector = aiohttp.TCPConnector(
            limit=MAX_CONCURRENT_CONNECTIONS,
            limit_per_host=3,
            ttl_dns_cache=300,
            use_dns_cache=True,
            ssl=False
        )

        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [eng.search(session, query, page=page) for eng in active_engines]
            results_list = await asyncio.gather(*tasks, return_exceptions=True)

        all_results = []
        seen_urls = set()

        for res in results_list:
            if isinstance(res, list):
                for item in res:
                    if isinstance(item, dict) and item.get('url') not in seen_urls:
                        seen_urls.add(item['url'])
                        all_results.append(item)
            elif isinstance(res, Exception):
                print(f"[Erro inesperado] {type(res).__name__}: {str(res)[:100]}")

        return all_results


# Template HTML Embutido (Single File Application)
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SearXNG Windows</title>
    <style>
        :root {
            --bg-color: #f5f5f5;
            --card-bg: #ffffff;
            --primary: #3b82f6;
            --text-main: #1f2937;
            --text-sec: #6b7280;
            --accent: #10b981;
        }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: var(--bg-color); margin: 0; padding: 0; color: var(--text-main); }
        .header { background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 2rem 1rem; text-align: center; color: white; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .logo { font-size: 2.5rem; font-weight: bold; margin-bottom: 1rem; display: block; }
        .search-container { max-width: 700px; margin: -25px auto 20px; position: relative; z-index: 10; padding: 0 1rem; }
        .search-box { display: flex; background: white; border-radius: 50px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); overflow: hidden; border: 1px solid #e5e7eb; }
        .search-input { flex: 1; border: none; padding: 1.2rem 1.5rem; font-size: 1.1rem; outline: none; }
        .search-btn { background: var(--primary); color: white; border: none; padding: 0 2rem; cursor: pointer; font-weight: 600; transition: background 0.2s; }
        .search-btn:hover { background: #2563eb; }
        
        .container { max-width: 1000px; margin: 2rem auto; padding: 0 1rem; display: grid; grid-template-columns: 250px 1fr; gap: 2rem; }
        @media(max-width: 768px) { .container { grid-template-columns: 1fr; } .sidebar { display: none; } }
        
        .sidebar { background: var(--card-bg); padding: 1.5rem; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); height: fit-content; }
        .sidebar h3 { margin-top: 0; color: var(--text-sec); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; }
        .category-list { list-style: none; padding: 0; }
        .category-item { margin-bottom: 0.5rem; }
        .category-link { display: block; padding: 0.5rem 0.75rem; border-radius: 6px; text-decoration: none; color: var(--text-main); font-weight: 500; transition: background 0.2s; }
        .category-link:hover, .category-link.active { background: #eff6ff; color: var(--primary); }
        
        .results-area { min-height: 400px; }
        .result-card { background: var(--card-bg); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; box-shadow: 0 1px 2px rgba(0,0,0,0.05); transition: transform 0.2s; border-left: 4px solid transparent; }
        .result-card:hover { transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .result-card.engine-bing { border-left-color: #0080cc; }
        .result-card.engine-yandex { border-left-color: #fc3f1d; }
        .result-card.engine-duckduckgo { border-left-color: #de5833; }
        .result-card.engine-github { border-left-color: #24292e; }
        .result-card.engine-wikipedia { border-left-color: #000000; }
        .result-card.engine-reddit { border-left-color: #ff4500; }
        .result-card.engine-youtube { border-left-color: #ff0000; }
        
        .result-title { font-size: 1.25rem; margin: 0 0 0.5rem 0; }
        .result-title a { text-decoration: none; color: #1a0dab; }
        .result-title a:hover { text-decoration: underline; }
        .result-url { font-size: 0.85rem; color: #202124; margin-bottom: 0.5rem; display: block; word-break: break-all; }
        .result-snippet { font-size: 0.95rem; line-height: 1.5; color: #4b5563; }
        .badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; margin-top: 0.5rem; margin-right: 0.5rem; background: #f3f4f6; color: #4b5563; }
        
        .loading { text-align: center; padding: 3rem; color: var(--text-sec); display: none; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid var(--primary); border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .footer { text-align: center; padding: 2rem; color: var(--text-sec); font-size: 0.9rem; margin-top: 2rem; border-top: 1px solid #e5e7eb; }
        
        .no-results { text-align: center; padding: 3rem; color: #666; }
        .stats { color: #666; margin-bottom: 1rem; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="header">
        <span class="logo">🔍 SearXNG Windows</span>
        <p>Metabusca Privada e Descentralizada</p>
    </div>

    <div class="search-container">
        <form class="search-box" action="/" method="GET">
            <input type="text" name="q" class="search-input" placeholder="Pesquise... (use !wiki, !github para bangs)" value="{{query}}" autofocus>
            <button type="submit" class="search-btn">Buscar</button>
        </form>
    </div>

    <div class="container">
        <aside class="sidebar">
            <h3>Categorias</h3>
            <ul class="category-list">
                <li class="category-item"><a href="/?q={{query}}&cat=general" class="category-link {{cat_general}}">🌐 Geral</a></li>
                <li class="category-item"><a href="/?q={{query}}&cat=it" class="category-link {{cat_it}}">💻 TI & Código</a></li>
                <li class="category-item"><a href="/?q={{query}}&cat=science" class="category-link {{cat_science}}">🎓 Ciência</a></li>
                <li class="category-item"><a href="/?q={{query}}&cat=videos" class="category-link {{cat_videos}}">🎬 Vídeos</a></li>
                <li class="category-item"><a href="/?q={{query}}&cat=social" class="category-link {{cat_social}}">💬 Redes Sociais</a></li>
                <li class="category-item"><a href="/?q={{query}}&cat=images" class="category-link {{cat_images}}">🖼️ Imagens</a></li>
            </ul>
            <div style="margin-top: 2rem; font-size: 0.8rem; color: #666;">
                <strong>Bangs Disponíveis:</strong><br>
                !bing, !ddg, !wiki, !github, !yt, !reddit
            </div>
        </aside>

        <main class="results-area">
            {{results_content}}
            
            <!-- Paginação -->
            {% if query %}
            <div class="pagination" style="display: flex; justify-content: center; gap: 1rem; margin-top: 2rem; padding: 1rem;">
                {% if has_prev %}
                <a href="/?q={{query}}{% if cat_general %}&cat=general{% endif %}{% if cat_it %}&cat=it{% endif %}{% if cat_science %}&cat=science{% endif %}{% if cat_videos %}&cat=videos{% endif %}{% if cat_social %}&cat=social{% endif %}{% if cat_images %}&cat=images{% endif %}&page={{current_page|minus:1}}" 
                   style="padding: 0.75rem 1.5rem; background: var(--primary); color: white; text-decoration: none; border-radius: 8px; font-weight: 600;">← Anterior</a>
                {% else %}
                <span style="padding: 0.75rem 1.5rem; background: #e5e7eb; color: #9ca3af; border-radius: 8px; font-weight: 600; cursor: not-allowed;">← Anterior</span>
                {% endif %}
                
                <span style="padding: 0.75rem 1.5rem; background: white; border: 2px solid var(--primary); color: var(--primary); border-radius: 8px; font-weight: 600;">
                    Página {{current_page}}
                </span>
                
                {% if has_next %}
                <a href="/?q={{query}}{% if cat_general %}&cat=general{% endif %}{% if cat_it %}&cat=it{% endif %}{% if cat_science %}&cat=science{% endif %}{% if cat_videos %}&cat=videos{% endif %}{% if cat_social %}&cat=social{% endif %}{% if cat_images %}&cat=images{% endif %}&page={{current_page|plus:1}}" 
                   style="padding: 0.75rem 1.5rem; background: var(--primary); color: white; text-decoration: none; border-radius: 8px; font-weight: 600;">Próxima →</a>
                {% else %}
                <span style="padding: 0.75rem 1.5rem; background: #e5e7eb; color: #9ca3af; border-radius: 8px; font-weight: 600; cursor: not-allowed;">Próxima →</span>
                {% endif %}
            </div>
            {% endif %}
        </main>
    </div>

    <div class="footer">
        <p>SearXNG Windows Edition • Privacidade por Design • Sem Rastreamento</p>
    </div>
</body>
</html>'''


def render_template(template_str, **kwargs):
    """Renderizador de template simples com suporte a filtros básicos"""
    result = template_str
    
    # Substituir variáveis simples
    for key, value in kwargs.items():
        placeholder = "{{" + key + "}}"
        if placeholder in result:
            result = result.replace(placeholder, str(value) if value is not None else "")
    
    # Processar filtros |plus:1 e |minus:1
    import re
    
    # Filtro plus:1 (adicionar 1)
    plus_pattern = r'\{\{(\w+)\|plus:(\d+)\}\}'
    for match in re.finditer(plus_pattern, result):
        var_name = match.group(1)
        add_value = int(match.group(2))
        if var_name in kwargs:
            try:
                current_val = int(kwargs[var_name])
                result = result.replace(match.group(0), str(current_val + add_value))
            except (ValueError, TypeError):
                result = result.replace(match.group(0), str(add_value))
    
    # Filtro minus:1 (subtrair 1)
    minus_pattern = r'\{\{(\w+)\|minus:(\d+)\}\}'
    for match in re.finditer(minus_pattern, result):
        var_name = match.group(1)
        sub_value = int(match.group(2))
        if var_name in kwargs:
            try:
                current_val = int(kwargs[var_name])
                result = result.replace(match.group(0), str(current_val - sub_value))
            except (ValueError, TypeError):
                result = result.replace(match.group(0), str(-sub_value))
    
    # Processar condicionais {% if var %}...{% endif %}
    if_pattern = r'\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}'
    while True:
        match = re.search(if_pattern, result, re.DOTALL)
        if not match:
            break
        var_name = match.group(1)
        content = match.group(2)
        var_value = kwargs.get(var_name, False)
        # Considera verdadeiro se não for False, None, 0, ou string vazia
        is_truthy = var_value and var_value not in [False, None, 0, '0', '']
        if is_truthy:
            result = result.replace(match.group(0), content)
        else:
            result = result.replace(match.group(0), '')
    
    return result


def generate_results_html(results, count, time_taken, query, category, page=1):
    """Gera o HTML dos resultados"""
    
    # Categorias ativas
    cats = {
        'general': 'active' if category == 'general' else '',
        'it': 'active' if category == 'it' else '',
        'science': 'active' if category == 'science' else '',
        'videos': 'active' if category == 'videos' else '',
        'social': 'active' if category == 'social' else '',
        'images': 'active' if category == 'images' else ''
    }
    
    if not query:
        # Página inicial
        results_html = '<div class="no-results"><h2>Bem-vindo ao SearXNG Windows</h2><p>Digite sua pesquisa acima para começar.</p></div>'
        stats_html = ''
    elif results:
        # Resultados encontrados
        results_html = ""
        for res in results:
            engine_class = res['engine'].lower().replace(" ", "").replace(".", "")
            results_html += f'''
            <article class="result-card engine-{engine_class}">
                <h2 class="result-title"><a href="{res['url']}" target="_blank" rel="noopener">{res['title']}</a></h2>
                <span class="result-url">{res['url']}</span>
                <p class="result-snippet">{res['content']}</p>
                <span class="badge">{res['engine']}</span>
                <span class="badge">{res['category']}</span>
            </article>
            '''
        stats_html = f'<p class="stats">{count} resultados encontrados em {time_taken}s (Página {page})</p>'
    else:
        # Sem resultados
        results_html = '<div class="no-results"><h2>Nenhum resultado encontrado</h2><p>Tente outro termo ou verifique sua conexão.</p></div>'
        stats_html = ''
    
    return results_html, stats_html, cats


async def handle_request(request):
    from aiohttp import web
    
    core = request.app['core']
    query = request.query.get('q', '')
    category = request.query.get('cat', None)
    page = request.query.get('page', '1')
    
    try:
        page = int(page)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    
    if not query:
        # Página inicial
        results_html, stats_html, cats = generate_results_html([], 0, 0, "", None, page=1)
        html_content = render_template(
            HTML_TEMPLATE,
            query="",
            results_content=results_html,
            cat_general=cats['general'],
            cat_it=cats['it'],
            cat_science=cats['science'],
            cat_videos=cats['videos'],
            cat_social=cats['social'],
            cat_images=cats['images'],
            current_page=1,
            has_next=False,
            has_prev=False
        )
        return web.Response(text=html_content, content_type='text/html')

    # Processar busca
    start_time = datetime.now()
    categories = [category] if category else None
    results = await core.search_all(query, categories, page=page)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    results_html, stats_html, cats = generate_results_html(
        results, len(results), f"{duration:.2f}", query, category, page=page
    )
    
    full_content = stats_html + results_html
    
    # Determinar se há páginas anterior/próxima
    has_prev = page > 1
    has_next = True  # Assume que sempre há próxima página para navegação infinita

    html_content = render_template(
        HTML_TEMPLATE,
        query=query,
        results_content=full_content,
        cat_general=cats['general'],
        cat_it=cats['it'],
        cat_science=cats['science'],
        cat_videos=cats['videos'],
        cat_social=cats['social'],
        cat_images=cats['images'],
        current_page=page,
        has_next=has_next,
        has_prev=has_prev
    )
    return web.Response(text=html_content, content_type='text/html')


async def main_server():
    from aiohttp import web
    
    core = SearXNGCore()
    app = web.Application()
    app['core'] = core
    app.router.add_get('/', handle_request)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    
    url = f"http://{HOST}:{PORT}"
    print(f"\n{'='*60}")
    print(f"✅ SearXNG Windows rodando com sucesso!")
    print(f"{'='*60}")
    print(f"🌐 URL de acesso: {url}")
    print(f"🚀 Abrindo navegador automaticamente...")
    print(f"{'='*60}")
    print(f"📦 Engines ativos: {len(core.engines)}")
    for eng in core.engines:
        status = "✓" if eng.enabled else "✗"
        print(f"   {status} {eng.name} ({eng.category})")
    print(f"{'='*60}")
    print(f"💡 Dicas:")
    print(f"   • Use !wiki python para buscar na Wikipedia")
    print(f"   • Use !github rust para buscar no GitHub")
    print(f"   • Pressione Ctrl+C para parar o servidor")
    print(f"{'='*60}\n")
    
    webbrowser.open(url)
    
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\n⏹️  Servidor encerrado pelo usuário.")
    finally:
        await runner.cleanup()


def main():
    parser = argparse.ArgumentParser(description="SearXNG Windows - Metabusca Privada")
    parser.add_argument('--web', action='store_true', help='Iniciar interface web')
    parser.add_argument('--port', type=int, default=8080, help='Porta do servidor web')
    parser.add_argument('--search', type=str, help='Buscar via linha de comando')
    parser.add_argument('--demo', action='store_true', help='Executar demonstração')
    
    args = parser.parse_args()
    
    if args.web or not any([args.search, args.demo]):
        global PORT
        PORT = args.port
        asyncio.run(main_server())
    elif args.search:
        core = SearXNGCore()
        results = asyncio.run(core.search_all(args.search))
        print(f"\n📊 {len(results)} resultados encontrados:\n")
        for i, res in enumerate(results, 1):  # Sem limite - mostra todos os resultados
            print(f"{i}. [{res['engine']}] {res['title']}")
            print(f"   {res['url']}")
            print(f"   {res['content'][:100]}...\n")
    elif args.demo:
        print("🧪 Executando demonstração do SearXNG Windows...\n")
        core = SearXNGCore()
        test_queries = ["python tutorial", "!wiki artificial intelligence", "!github python"]
        for q in test_queries:
            print(f"🔍 Buscando por: {q}")
            results = asyncio.run(core.search_all(q))
            print(f"   ✓ {len(results)} resultados\n")
        print("✅ Demonstração concluída!")


if __name__ == "__main__":
    # Verificar dependências
    try:
        import aiohttp
    except ImportError:
        print("⚠️  Dependência aiohttp não encontrada.")
        print("📦 Instalando automaticamente...\n")
        import subprocess
        subprocess.check_call(["pip", "install", "aiohttp", "-q"])
        print("✅ Instalação concluída!\n")
    
    main()
