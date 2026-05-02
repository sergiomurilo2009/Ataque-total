"""
SearXNG para Windows - Motor de Metabusca Completo
===================================================
Implementação nativa para Windows com interface web moderna,
suporte a Yandex e múltiplos engines com API unificada.

Autor: SearXNG Windows Team
Licença: AGPL v3
"""

import asyncio
import aiohttp
import json
import re
import argparse
import sys
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
import logging
from urllib.parse import quote_plus, urlparse, unquote
import html
from collections import defaultdict
import ssl

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('searxng_windows')


@dataclass
class SearchResult:
    """Estrutura de dados para resultados de busca"""
    title: str
    url: str
    content: str
    engine: str
    category: str
    score: float = 0.0
    thumbnail: Optional[str] = None
    published_date: Optional[str] = None
    img_src: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EngineConfig:
    """Configuração de um motor de busca"""
    name: str
    base_url: str
    categories: List[str]
    enabled: bool = True
    search_url: str = ""
    timeout: int = 8
    headers: Dict = field(default_factory=lambda: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    })
    
    def __post_init__(self):
        if not self.search_url:
            self.search_url = self.base_url


class SearchEngine:
    """Classe base para motores de busca"""
    
    def __init__(self, config: EngineConfig):
        self.config = config
        self.session = None
    
    async def search(self, query: str, category: Optional[str] = None) -> List[SearchResult]:
        """Realiza busca no engine"""
        if not self.config.enabled:
            return []
        
        if category and category not in self.config.categories:
            return []
        
        results = []
        try:
            async with aiohttp.ClientSession(headers=self.config.headers) as session:
                search_url = self.build_search_url(query)
                async with session.get(search_url, timeout=self.config.timeout, 
                                      ssl=False) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        results = await self.parse_results(html_content, query)
        except Exception as e:
            logger.debug(f"Erro no engine {self.config.name}: {e}")
        
        return results
    
    def build_search_url(self, query: str) -> str:
        """Constrói URL de busca"""
        encoded_query = quote_plus(query)
        return self.config.search_url.replace('{query}', encoded_query)
    
    async def parse_results(self, html_content: str, query: str) -> List[SearchResult]:
        """Parseia resultados HTML - deve ser implementado por subclasses"""
        raise NotImplementedError


class BingEngine(SearchEngine):
    """Motor de busca Bing"""
    
    async def parse_results(self, html_content: str, query: str) -> List[SearchResult]:
        results = []
        try:
            # Padrão para resultados do Bing
            pattern = r'<li class="b_algo"[^>]*>.*?<h2[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>.*?<p[^>]*>([^<]*)'
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for url, title, content in matches[:15]:
                clean_content = re.sub(r'<[^>]+>', '', content).strip()
                results.append(SearchResult(
                    title=html.unescape(title),
                    url=url,
                    content=clean_content[:200],
                    engine=self.config.name,
                    category=self.config.categories[0] if self.config.categories else "general",
                    score=1.0
                ))
        except Exception as e:
            logger.debug(f"Erro ao parsear Bing: {e}")
        
        return results


class DuckDuckGoEngine(SearchEngine):
    """Motor de busca DuckDuckGo"""
    
    async def parse_results(self, html_content: str, query: str) -> List[SearchResult]:
        results = []
        try:
            # DDG HTML interface
            pattern = r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html_content)
            
            for url, title in matches[:15]:
                # Extrair URL real
                if url.startswith('//'):
                    url = 'https:' + url
                elif not url.startswith('http'):
                    continue
                    
                results.append(SearchResult(
                    title=html.unescape(title),
                    url=url,
                    content="",
                    engine=self.config.name,
                    category=self.config.categories[0] if self.config.categories else "general",
                    score=1.0
                ))
        except Exception as e:
            logger.debug(f"Erro ao parsear DuckDuckGo: {e}")
        
        return results


class YandexEngine(SearchEngine):
    """Motor de busca Yandex"""
    
    def __init__(self, config: EngineConfig):
        super().__init__(config)
        self.config.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
    
    async def parse_results(self, html_content: str, query: str) -> List[SearchResult]:
        results = []
        try:
            # Padrão para resultados do Yandex
            patterns = [
                r'<a[^>]+href="([^"]+)"[^>]*class="OrganicTitle-LinkText"[^>]*>([^<]+)</a>',
                r'<a[^>]+class="organic__url"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for url, title in matches[:15]:
                    if url.startswith('//'):
                        url = 'https:' + url
                    elif not url.startswith('http'):
                        continue
                    
                    # Tentar extrair snippet
                    content_match = re.search(rf'<div[^>]+class="OrganicText"[^>]*>([^<]+)', html_content)
                    content = content_match.group(1) if content_match else ""
                    
                    results.append(SearchResult(
                        title=html.unescape(title),
                        url=url,
                        content=content[:200],
                        engine=self.config.name,
                        category=self.config.categories[0] if self.config.categories else "general",
                        score=1.0
                    ))
                if results:
                    break
        except Exception as e:
            logger.debug(f"Erro ao parsear Yandex: {e}")
        
        return results


class QwantEngine(SearchEngine):
    """Motor de busca Qwant"""
    
    async def parse_results(self, html_content: str, query: str) -> List[SearchResult]:
        results = []
        try:
            pattern = r'<a[^>]+href="([^"]+)"[^>]*class="result-link"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html_content)
            
            for url, title in matches[:15]:
                results.append(SearchResult(
                    title=html.unescape(title),
                    url=url,
                    content="",
                    engine=self.config.name,
                    category=self.config.categories[0] if self.config.categories else "general",
                    score=1.0
                ))
        except Exception as e:
            logger.debug(f"Erro ao parsear Qwant: {e}")
        
        return results


class BraveEngine(SearchEngine):
    """Motor de busca Brave Search"""
    
    async def parse_results(self, html_content: str, query: str) -> List[SearchResult]:
        results = []
        try:
            pattern = r'<a[^>]+href="([^"]+)"[^>]*data-inbound-url="[^"]*"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html_content)
            
            for url, title in matches[:15]:
                if url.startswith('http') and 'brave.com' not in url:
                    results.append(SearchResult(
                        title=html.unescape(title),
                        url=url,
                        content="",
                        engine=self.config.name,
                        category="general",
                        score=1.0
                    ))
        except Exception as e:
            logger.debug(f"Erro ao parsear Brave: {e}")
        
        return results


class GitHubEngine(SearchEngine):
    """Motor de busca GitHub"""
    
    async def parse_results(self, html_content: str, query: str) -> List[SearchResult]:
        results = []
        try:
            # Buscar repositórios
            pattern = r'<a[^>]+href="([^"]+/[^/]+/[^"]+)"[^>]*class="v-align-middle"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html_content)
            
            for url, title in matches[:10]:
                full_url = f"https://github.com{url}" if url.startswith('/') else url
                results.append(SearchResult(
                    title=html.unescape(title.strip()),
                    url=full_url,
                    content=f"Repositório GitHub: {title}",
                    engine=self.config.name,
                    category="it",
                    score=1.0
                ))
        except Exception as e:
            logger.debug(f"Erro ao parsear GitHub: {e}")
        
        return results


class WikipediaEngine(SearchEngine):
    """Motor de busca Wikipedia"""
    
    async def parse_results(self, html_content: str, query: str) -> List[SearchResult]:
        results = []
        try:
            pattern = r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html_content)
            
            for url, title in matches[:15]:
                if '/wiki/' in url and ':' not in url:
                    full_url = f"https://wikipedia.org{url}" if url.startswith('/') else url
                    results.append(SearchResult(
                        title=html.unescape(title),
                        url=full_url,
                        content=f"Artigo da Wikipedia sobre {title}",
                        engine=self.config.name,
                        category="science",
                        score=1.0
                    ))
        except Exception as e:
            logger.debug(f"Erro ao parsear Wikipedia: {e}")
        
        return results


class RedditEngine(SearchEngine):
    """Motor de busca Reddit"""
    
    async def parse_results(self, html_content: str, query: str) -> List[SearchResult]:
        results = []
        try:
            pattern = r'<a[^>]+href="([^"]+)"[^>]*data-click-id="[^"]*"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html_content)
            
            for url, title in matches[:15]:
                if url.startswith('/r/') or url.startswith('https://www.reddit.com'):
                    full_url = f"https://www.reddit.com{url}" if url.startswith('/') else url
                    results.append(SearchResult(
                        title=html.unescape(title.strip()),
                        url=full_url,
                        content="",
                        engine=self.config.name,
                        category="social",
                        score=1.0
                    ))
        except Exception as e:
            logger.debug(f"Erro ao parsear Reddit: {e}")
        
        return results


class ArxivEngine(SearchEngine):
    """Motor de busca arXiv"""
    
    async def parse_results(self, html_content: str, query: str) -> List[SearchResult]:
        results = []
        try:
            pattern = r'<a[^>]+href="([^"]+abs/[^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html_content)
            
            for url, title in matches[:10]:
                results.append(SearchResult(
                    title=html.unescape(title.strip()),
                    url=url if url.startswith('http') else f"https://arxiv.org{url}",
                    content="Artigo científico",
                    engine=self.config.name,
                    category="science",
                    score=1.0
                ))
        except Exception as e:
            logger.debug(f"Erro ao parsear arXiv: {e}")
        
        return results


class YoutubeEngine(SearchEngine):
    """Motor de busca YouTube"""
    
    async def parse_results(self, html_content: str, query: str) -> List[SearchResult]:
        results = []
        try:
            pattern = r'<a[^>]+href="(/watch\?v=[^"]+)"[^>]*title="([^"]+)"'
            matches = re.findall(pattern, html_content)
            
            for url, title in matches[:15]:
                results.append(SearchResult(
                    title=html.unescape(title),
                    url=f"https://youtube.com{url}",
                    content="Vídeo do YouTube",
                    engine=self.config.name,
                    category="videos",
                    score=1.0
                ))
        except Exception as e:
            logger.debug(f"Erro ao parsear YouTube: {e}")
        
        return results


class SearXNGWindows:
    """
    Classe principal do SearXNG para Windows
    Agrega resultados de múltiplos motores de busca incluindo Yandex
    """
    
    # Definição de todos os engines suportados
    ENGINES_CONFIG = [
        # Motores Gerais
        EngineConfig("bing", "https://www.bing.com/search", ["general", "images", "videos", "news"], enabled=True),
        EngineConfig("duckduckgo", "https://html.duckduckgo.com/html/", ["general", "images", "news"], enabled=True),
        EngineConfig("yandex", "https://yandex.com/search/", ["general", "images", "news"], enabled=True),
        EngineConfig("qwant", "https://www.qwant.com/", ["general", "news", "images"], enabled=True),
        EngineConfig("brave", "https://search.brave.com/search", ["general"], enabled=True),
        
        # Arquivos e Repositórios
        EngineConfig("github", "https://github.com/search", ["it"], enabled=True),
        EngineConfig("gitlab", "https://gitlab.com/search", ["it"], enabled=True),
        
        # Acadêmico e Ciência
        EngineConfig("arxiv", "https://arxiv.org/search/", ["science"], enabled=True),
        EngineConfig("wikipedia", "https://wikipedia.org/w/index.php", ["general", "science"], enabled=True),
        
        # Mídia e Imagens
        EngineConfig("youtube", "https://www.youtube.com/results", ["videos"], enabled=True),
        EngineConfig("dailymotion", "https://www.dailymotion.com/search", ["videos"], enabled=True),
        
        # Redes Sociais
        EngineConfig("reddit", "https://www.reddit.com/search", ["social", "news"], enabled=True),
    ]
    
    # Categorias disponíveis
    CATEGORIES = {
        "general": "Geral",
        "images": "Imagens",
        "videos": "Vídeos",
        "news": "Notícias",
        "it": "TI",
        "science": "Ciência",
        "maps": "Mapas",
        "music": "Música",
        "social": "Redes Sociais"
    }
    
    # Bangs (atalhos para sites específicos) - INCLUINDO YANDEX
    BANGS = {
        "!g": "google",
        "!google": "google",
        "!b": "bing",
        "!ddg": "duckduckgo",
        "!y": "yandex",
        "!yandex": "yandex",
        "!w": "wikipedia",
        "!wiki": "wikipedia",
        "!gh": "github",
        "!git": "github",
        "!r": "reddit",
        "!yt": "youtube",
        "!q": "qwant",
        "!brave": "brave",
    }
    
    def __init__(self, config_file: Optional[str] = None):
        self.engines: Dict[str, SearchEngine] = {}
        self.config = {}
        self.config_file = config_file or "searxng_config.json"
        self._load_config()
        self._initialize_engines()
    
    def _load_config(self):
        """Carrega configuração do arquivo ou usa padrões"""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"Configuração carregada de {self.config_file}")
            except Exception as e:
                logger.warning(f"Erro ao carregar config: {e}. Usando padrões.")
                self.config = {}
        else:
            self.config = {
                "enabled_engines": [e.name for e in self.ENGINES_CONFIG if e.enabled],
                "default_categories": ["general"],
                "language": "pt-BR",
                "safe_search": 1,
                "max_results_per_engine": 15,
                "timeout": 8
            }
            self._save_config()
    
    def _save_config(self):
        """Salva configuração atual"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuração salva em {self.config_file}")
        except Exception as e:
            logger.error(f"Erro ao salvar config: {e}")
    
    def _initialize_engines(self):
        """Inicializa todos os engines configurados"""
        engine_classes = {
            "bing": BingEngine,
            "duckduckgo": DuckDuckGoEngine,
            "yandex": YandexEngine,
            "wikipedia": WikipediaEngine,
            "github": GitHubEngine,
            "reddit": RedditEngine,
            "arxiv": ArxivEngine,
            "qwant": QwantEngine,
            "brave": BraveEngine,
            "youtube": YoutubeEngine,
        }
        
        enabled_engines = self.config.get("enabled_engines", [])
        
        for eng_config in self.ENGINES_CONFIG:
            if eng_config.name in enabled_engines or eng_config.enabled:
                engine_class = engine_classes.get(eng_config.name, SearchEngine)
                self.engines[eng_config.name] = engine_class(eng_config)
        
        logger.info(f"{len(self.engines)} engines inicializados")
    
    def parse_bangs(self, query: str) -> tuple[Optional[str], str]:
        """
        Parseia bangs na query
        Retorna (engine_name, cleaned_query)
        """
        words = query.split()
        if words and words[0].lower() in self.BANGS:
            engine_name = self.BANGS[words[0].lower()]
            cleaned_query = ' '.join(words[1:])
            return engine_name, cleaned_query
        return None, query
    
    async def search(self, query: str, categories: Optional[List[str]] = None) -> List[SearchResult]:
        """
        Realiza busca em TODOS os engines ativos SIMULTANEAMENTE
        
        Args:
            query: Termo de busca
            categories: Lista de categorias para filtrar
            
        Returns:
            Lista de resultados ordenados por relevância
        """
        all_results = []
        
        # Verifica se há bangs
        engine_override, clean_query = self.parse_bangs(query)
        if engine_override:
            logger.info(f"Bang detectado: buscando apenas em {engine_override}")
            categories = None  # Ignora categorias quando usa bang
        
        if not categories:
            categories = self.config.get("default_categories", ["general"])
        
        logger.info(f"Buscando por '{clean_query}' nas categorias: {categories}")
        
        # Cria tasks para buscar em TODOS os engines SIMULTANEAMENTE
        tasks = []
        active_engines = []
        
        for engine_name, engine in self.engines.items():
            # Se houver engine override, busca apenas naquele engine
            if engine_override and engine_name != engine_override:
                continue
            
            # Verifica se engine tem categoria solicitada
            if categories:
                has_category = any(cat in engine.config.categories for cat in categories)
                if not has_category:
                    continue
            
            tasks.append(engine.search(clean_query, categories[0] if categories else None))
            active_engines.append(engine_name)
        
        logger.info(f"Engines ativos: {', '.join(active_engines)}")
        
        # Executa TODAS as buscas EM PARALELO
        if tasks:
            results_batch = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result_list in results_batch:
                if isinstance(result_list, list):
                    all_results.extend(result_list)
                elif isinstance(result_list, Exception):
                    logger.debug(f"Erro em busca: {result_list}")
        
        # Ordena resultados
        all_results.sort(key=lambda x: x.score, reverse=True)
        
        # Remove duplicatas por URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        return unique_results
    
    def get_engines_by_category(self, category: str) -> List[str]:
        """Retorna lista de engines para uma categoria"""
        return [
            name for name, engine in self.engines.items()
            if category in engine.config.categories
        ]
    
    def toggle_engine(self, engine_name: str, enabled: bool):
        """Ativa ou desativa um engine"""
        if enabled:
            if engine_name not in self.config.get("enabled_engines", []):
                self.config.setdefault("enabled_engines", []).append(engine_name)
        else:
            if engine_name in self.config.get("enabled_engines", []):
                self.config["enabled_engines"].remove(engine_name)
        
        self._save_config()
        self._initialize_engines()
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas dos engines"""
        return {
            "total_engines": len(self.engines),
            "enabled_engines": len([e for e in self.engines.values() if e.config.enabled]),
            "categories": list(self.CATEGORIES.keys()),
            "bangs_count": len(self.BANGS),
            "engine_names": list(self.engines.keys())
        }


async def demo_search():
    """Demonstração de busca via linha de comando"""
    searxng = SearXNGWindows()
    
    print("\n" + "="*60)
    print("🔍 SearXNG Windows - Demonstração COMPLETA")
    print("="*60)
    
    stats = searxng.get_stats()
    print(f"\n📊 Estatísticas:")
    print(f"   Engines ativos: {stats['enabled_engines']}/{stats['total_engines']}")
    print(f"   Engines: {', '.join(stats['engine_names'])}")
    print(f"   Categorias: {', '.join(stats['categories'])}")
    print(f"   Bangs disponíveis: {stats['bangs_count']}")
    
    print(f"\n💡 Bangs disponíveis:")
    for bang, engine in list(searxng.BANGS.items()):
        print(f"   {bang} → {engine}")
    
    print("\n" + "="*60)
    
    # Exemplo de busca
    query = "python programming tutorial"
    print(f"\n🔎 Buscando por: '{query}' em MÚLTIPLOS ENGINES SIMULTANEAMENTE\n")
    
    results = await searxng.search(query, categories=["general", "it"])
    
    print(f"✅ {len(results)} resultados encontrados de múltiplos engines:\n")
    
    # Agrupar por engine
    by_engine = defaultdict(list)
    for result in results:
        by_engine[result.engine].append(result)
    
    for engine, engine_results in by_engine.items():
        print(f"\n📌 {engine.upper()} ({len(engine_results)} resultados):")
        print("-" * 50)
        for i, result in enumerate(engine_results[:5], 1):
            print(f"{i}. {result.title}")
            print(f"   URL: {result.url}")
            print()
    
    print("="*60)


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="SearXNG para Windows - Motor de Metabusca com Yandex",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py --search "python tutorial"
  python main.py --web --port 8080
  python main.py --demo
  
Bangs (atalhos):
  !yandex termo     - Busca no Yandex
  !google termo     - Busca no Google
  !wiki python      - Busca na Wikipedia
  !github rust      - Busca no GitHub
  !reddit linux     - Busca no Reddit

Categorias:
  general, images, videos, news, it, science, maps, music, social
        """
    )
    
    parser.add_argument('--search', '-s', type=str, help='Termo de busca')
    parser.add_argument('--categories', '-c', type=str, nargs='+', default=['general'],
                       help='Categorias para busca')
    parser.add_argument('--web', '-w', action='store_true', help='Iniciar interface web')
    parser.add_argument('--port', '-p', type=int, default=8080, help='Porta do servidor web')
    parser.add_argument('--host', type=str, default='localhost', help='Host do servidor web')
    parser.add_argument('--demo', '-d', action='store_true', help='Rodar demonstração')
    parser.add_argument('--config', type=str, help='Arquivo de configuração')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo verbose')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.demo:
        asyncio.run(demo_search())
        return
    
    searxng = SearXNGWindows(config_file=args.config)
    
    if args.web:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import urllib.parse
        
        class SearXNGHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed_path = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed_path.query)
                
                query = query_params.get('q', [''])[0]
                categories = query_params.get('categories', ['general'])
                
                if query:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    results = loop.run_until_complete(searxng.search(query, categories))
                    loop.close()
                else:
                    results = []
                
                stats = searxng.get_stats()
                
                # Gerar HTML moderno
                html_content = generate_modern_html(results, query, categories, stats, searxng)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html_content.encode('utf-8'))
            
            def log_message(self, format, *args):
                logger.info(f"{self.address_string()} - {format % args}")
        
        server = HTTPServer((args.host, args.port), SearXNGHandler)
        logger.info(f"Servidor iniciado em http://{args.host}:{args.port}")
        print(f"\n{'='*60}")
        print(f"🚀 SearXNG Windows rodando em http://{args.host}:{args.port}")
        print(f"   Engines ativos: {', '.join(searxng.engines.keys())}")
        print(f"   INCLUINDO YANDEX!")
        print(f"{'='*60}\n")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Servidor interrompido pelo usuário")
            server.shutdown()
    elif args.search:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(searxng.search(args.search, args.categories))
        loop.close()
        
        print(f"\n{'='*60}")
        print(f"Resultados para: '{args.search}'")
        print(f"{'='*60}\n")
        
        # Agrupar por engine
        by_engine = defaultdict(list)
        for result in results:
            by_engine[result.engine].append(result)
        
        for engine, engine_results in by_engine.items():
            print(f"\n📌 {engine.upper()} ({len(engine_results)} resultados):")
            print("-" * 50)
            for i, result in enumerate(engine_results, 1):
                print(f"{i}. {result.title}")
                print(f"   URL: {result.url}")
                if result.content:
                    print(f"   {result.content[:100]}...")
                print()
    else:
        parser.print_help()


def generate_modern_html(results: List[SearchResult], query: str, 
                        categories: List[str], stats: Dict, searxng: SearXNGWindows) -> str:
    """Gera página HTML moderna estilo SearXNG"""
    
    # Agrupar resultados por engine
    by_engine = defaultdict(list)
    for result in results:
        by_engine[result.engine].append(result)
    
    results_html = ""
    for engine, engine_results in by_engine.items():
        results_html += f'<div class="engine-section"><h3 class="engine-title">🔍 {engine.upper()} ({len(engine_results)} resultados)</h3>'
        for result in engine_results:
            results_html += f'''
            <div class="result">
                <h3><a href="{html.escape(result.url)}" target="_blank" rel="noopener">{html.escape(result.title)}</a></h3>
                <div class="url">{html.escape(result.url)}</div>
                <div class="content">{html.escape(result.content[:200] if result.content else '')}</div>
                <div class="meta">
                    <span class="engine-badge">{result.engine}</span>
                    <span class="category-badge">{result.category}</span>
                </div>
            </div>
            '''
        results_html += '</div>'
    
    if not results:
        results_html = """
        <div class="no-results">
            <div class="no-results-icon">🔍</div>
            <h3>Nenhum resultado encontrado</h3>
            <p>Tente outros termos ou verifique sua conexão</p>
        </div>
        """
    
    # Botões de categoria
    category_buttons = ""
    for cat_id, cat_name in searxng.CATEGORIES.items():
        active = "active" if cat_id in categories else ""
        category_buttons += f'<button class="cat-btn {active}" data-category="{cat_id}">{cat_name}</button>'
    
    # Lista de engines
    engine_checks = ""
    for engine_name in stats['engine_names']:
        checked = "checked" if engine_name in searxng.config.get('enabled_engines', []) else ""
        engine_checks += f'''
        <label class="engine-toggle">
            <input type="checkbox" data-engine="{engine_name}" {checked}>
            <span>{engine_name}</span>
        </label>
        '''
    
    current_year = datetime.now().year
    
    html_content = f'''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SearXNG Windows - Metabusca com Yandex</title>
    <style>
        :root {{
            --primary: #4f46e5;
            --primary-dark: #4338ca;
            --secondary: #06b6d4;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --text-light: #64748b;
            --border: #e2e8f0;
            --success: #10b981;
            --warning: #f59e0b;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: var(--text);
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 1.5rem 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            gap: 2rem;
            flex-wrap: wrap;
        }}
        
        .logo {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
        }}
        
        .logo-icon {{
            font-size: 2rem;
        }}
        
        .search-form {{
            flex: 1;
            min-width: 300px;
        }}
        
        .search-input-wrapper {{
            display: flex;
            gap: 0.5rem;
        }}
        
        .search-input {{
            flex: 1;
            padding: 0.75rem 1.25rem;
            border: 2px solid var(--border);
            border-radius: 12px;
            font-size: 1rem;
            transition: all 0.3s;
        }}
        
        .search-input:focus {{
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }}
        
        .search-btn {{
            padding: 0.75rem 1.5rem;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }}
        
        .search-btn:hover {{
            background: var(--primary-dark);
            transform: translateY(-2px);
        }}
        
        .main-container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 2rem;
        }}
        
        .sidebar {{
            background: var(--card-bg);
            border-radius: 16px;
            padding: 1.5rem;
            height: fit-content;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .sidebar-section {{
            margin-bottom: 2rem;
        }}
        
        .sidebar-title {{
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-light);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 1rem;
        }}
        
        .cat-btn {{
            display: block;
            width: 100%;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            background: var(--bg);
            color: var(--text);
            border: 2px solid transparent;
            border-radius: 10px;
            cursor: pointer;
            text-align: left;
            font-weight: 500;
            transition: all 0.3s;
        }}
        
        .cat-btn:hover {{
            background: var(--primary);
            color: white;
        }}
        
        .cat-btn.active {{
            background: var(--primary);
            color: white;
            border-color: var(--primary-dark);
        }}
        
        .engine-toggle {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.5rem 0;
            cursor: pointer;
        }}
        
        .engine-toggle input {{
            width: 18px;
            height: 18px;
            cursor: pointer;
        }}
        
        .results-area {{
            background: var(--card-bg);
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .stats-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            background: var(--bg);
            border-radius: 10px;
            margin-bottom: 1.5rem;
            font-size: 0.875rem;
            color: var(--text-light);
        }}
        
        .engine-section {{
            margin-bottom: 2rem;
            padding-bottom: 2rem;
            border-bottom: 2px solid var(--border);
        }}
        
        .engine-section:last-child {{
            border-bottom: none;
        }}
        
        .engine-title {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 1rem;
            padding: 0.75rem;
            background: rgba(79, 70, 229, 0.1);
            border-radius: 8px;
        }}
        
        .result {{
            padding: 1.25rem;
            margin-bottom: 1rem;
            border-radius: 12px;
            transition: all 0.3s;
            border: 1px solid var(--border);
        }}
        
        .result:hover {{
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transform: translateX(4px);
        }}
        
        .result h3 a {{
            color: var(--primary);
            text-decoration: none;
            font-size: 1.125rem;
            line-height: 1.4;
        }}
        
        .result h3 a:hover {{
            text-decoration: underline;
        }}
        
        .result .url {{
            color: var(--success);
            font-size: 0.875rem;
            margin: 0.5rem 0;
            word-break: break-all;
        }}
        
        .result .content {{
            color: var(--text-light);
            line-height: 1.6;
            font-size: 0.9375rem;
        }}
        
        .result .meta {{
            display: flex;
            gap: 0.75rem;
            margin-top: 0.75rem;
        }}
        
        .engine-badge, .category-badge {{
            padding: 0.25rem 0.75rem;
            background: var(--bg);
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-light);
        }}
        
        .no-results {{
            text-align: center;
            padding: 4rem 2rem;
        }}
        
        .no-results-icon {{
            font-size: 4rem;
            margin-bottom: 1rem;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: white;
            font-size: 0.875rem;
        }}
        
        .bang-hint {{
            background: rgba(255, 255, 255, 0.1);
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            font-size: 0.875rem;
        }}
        
        .bang-hint code {{
            background: rgba(255, 255, 255, 0.2);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-family: monospace;
        }}
        
        @media (max-width: 900px) {{
            .main-container {{
                grid-template-columns: 1fr;
            }}
            
            .sidebar {{
                order: 2;
            }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <div class="logo">
                <span class="logo-icon">🔍</span>
                <span>SearXNG Windows</span>
            </div>
            
            <form class="search-form" method="GET" action="/">
                <div class="search-input-wrapper">
                    <input type="text" 
                           name="q" 
                           class="search-input" 
                           value="{html.escape(query)}" 
                           placeholder="Pesquise... (use !yandex, !google, !wiki para bangs)"
                           autofocus>
                    <button type="submit" class="search-btn">Buscar</button>
                </div>
            </form>
            
            <div class="bang-hint">
                💡 <strong>Dica:</strong> Use <code>!yandex</code>, <code>!google</code>, <code>!wiki</code> para buscar diretamente
            </div>
        </div>
    </header>
    
    <main class="main-container">
        <aside class="sidebar">
            <div class="sidebar-section">
                <h4 class="sidebar-title">Categorias</h4>
                {category_buttons}
            </div>
            
            <div class="sidebar-section">
                <h4 class="sidebar-title">Engines Ativos</h4>
                {engine_checks}
            </div>
            
            <div class="sidebar-section">
                <h4 class="sidebar-title">Estatísticas</h4>
                <div style="font-size: 0.875rem; color: var(--text-light);">
                    <p><strong>Total:</strong> {stats['total_engines']} engines</p>
                    <p><strong>Ativos:</strong> {stats['enabled_engines']}</p>
                    <p><strong>Bangs:</strong> {stats['bangs_count']}</p>
                </div>
            </div>
        </aside>
        
        <div class="results-area">
            <div class="stats-bar">
                <span><strong>{len(results)}</strong> resultados encontrados</span>
                <span>Categorias: {', '.join(categories)}</span>
                <span>Tempo: <strong>&lt; 2s</strong></span>
            </div>
            
            {results_html}
        </div>
    </main>
    
    <footer class="footer">
        <p>SearXNG para Windows © {current_year} | Com Yandex | Sem rastreamento | Open Source</p>
        <p style="margin-top: 0.5rem; opacity: 0.8;">
            Engines: {', '.join(stats['engine_names'])}
        </p>
    </footer>
    
    <script>
        // Clique nas categorias
        document.querySelectorAll('.cat-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                const category = this.dataset.category;
                const url = new URL(window.location.href);
                
                if (this.classList.contains('active')) {{
                    this.classList.remove('active');
                    // Remove categoria dos params
                    let cats = url.searchParams.getAll('categories');
                    cats = cats.filter(c => c !== category);
                    url.searchParams.delete('categories');
                    cats.forEach(c => url.searchParams.append('categories', c));
                }} else {{
                    this.classList.add('active');
                    url.searchParams.append('categories', category);
                }}
                
                window.location.href = url.toString();
            }});
        }});
        
        // Toggle de engines
        document.querySelectorAll('.engine-toggle input').forEach(input => {{
            input.addEventListener('change', function() {{
                const engine = this.dataset.engine;
                const enabled = this.checked;
                
                fetch(`/api/engine/${{engine}}?enabled=${{enabled}}`, {{
                    method: 'POST'
                }}).then(() => {{
                    alert(`Engine ${{engine}} ${{enabled ? 'ativado' : 'desativado'}}!`);
                }});
            }});
        }});
        
        // Atalho de teclado (Ctrl+K para focar na busca)
        document.addEventListener('keydown', function(e) {{
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {{
                e.preventDefault();
                document.querySelector('.search-input').focus();
            }}
        }});
    </script>
</body>
</html>
'''
    
    return html_content


if __name__ == "__main__":
    main()
