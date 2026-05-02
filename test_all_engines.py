#!/usr/bin/env python3
"""
Script de teste para todas as APIs e engines de busca
"""
import asyncio
import aiohttp
import json
import random
from urllib.parse import quote_plus
import time

# User Agents extensos para evitar bloqueios - ROTATIVO
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
]

BASE_HEADERS = {
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8,en-US;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# Configuração de todas as engines
ENGINES = [
    # APIs Oficiais
    {"name": "GitHub API", "url": "https://api.github.com/search/repositories?q=", "type": "json", "headers_type": "json"},
    {"name": "GitLab API", "url": "https://gitlab.com/api/v4/projects?search=", "type": "json", "headers_type": "json"},
    {"name": "StackOverflow API", "url": "https://api.stackexchange.com/2.3/search?order=desc&sort=relevance&site=stackoverflow&intitle=", "type": "json", "headers_type": "json"},
    {"name": "Wikipedia API", "url": "https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srprop=snippet|title&srlimit=10&srsearch=", "type": "json", "headers_type": "json"},
    
    # Scraping HTML
    {"name": "DuckDuckGo", "url": "https://html.duckduckgo.com/html?q=", "type": "html", "headers_type": "html"},
    {"name": "Bing", "url": "https://www.bing.com/search?q=", "type": "html", "headers_type": "html"},
    {"name": "Brave Search", "url": "https://search.brave.com/search?q=", "type": "html", "headers_type": "html"},
    {"name": "Yandex", "url": "https://yandex.ru/search/?text=", "type": "html", "headers_type": "html"},
    {"name": "YouTube", "url": "https://www.youtube.com/results?search_query=", "type": "html", "headers_type": "html"},
    {"name": "Reddit (old)", "url": "https://old.reddit.com/search?q=", "type": "html", "headers_type": "html"},
    {"name": "StackOverflow HTML", "url": "https://stackoverflow.com/search?q=", "type": "html", "headers_type": "html"},
    {"name": "GitHub HTML", "url": "https://github.com/search?q=", "type": "html", "headers_type": "html"},
    {"name": "Wikipedia HTML", "url": "https://en.wikipedia.org/w/index.php?search=", "type": "html", "headers_type": "html"},
]

async def test_engine(session, engine, query="python"):
    """Testa uma engine específica"""
    url = f"{engine['url']}{quote_plus(query)}"
    
    # Headers apropriados
    user_agent = random.choice(USER_AGENTS)
    headers = BASE_HEADERS.copy()
    headers["User-Agent"] = user_agent
    
    if engine["headers_type"] == "json":
        headers["Accept"] = "application/json"
        if "wikipedia.org" in url:
            headers["User-Agent"] = "SearchApp/1.0 (contact: info@example.com)"
    else:
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    
    try:
        async with session.get(url, headers=headers, timeout=15, ssl=False, allow_redirects=True) as response:
            status = response.status
            content_type = response.headers.get('Content-Type', '')
            
            if status == 200:
                if engine["type"] == "json" or 'application/json' in content_type:
                    try:
                        data = await response.json()
                        # Verifica se tem resultados
                        if isinstance(data, dict):
                            items = data.get('items', []) or data.get('query', {}).get('search', [])
                            count = len(items)
                        elif isinstance(data, list):
                            count = len(data)
                        else:
                            count = 0
                        
                        return {
                            "name": engine["name"],
                            "status": "✓ FUNCIONANDO",
                            "results": count,
                            "status_code": status,
                            "content_type": content_type[:50] if content_type else "N/A"
                        }
                    except Exception as e:
                        return {
                            "name": engine["name"],
                            "status": "⚠ ERRO JSON",
                            "error": str(e)[:100],
                            "status_code": status
                        }
                else:
                    html = await response.text()
                    # Conta links ou elementos como indicador de sucesso
                    link_count = html.count('<a href')
                    return {
                        "name": engine["name"],
                        "status": "✓ FUNCIONANDO" if link_count > 5 else "⚠ POUCOS RESULTADOS",
                        "links_found": link_count,
                        "status_code": status,
                        "content_length": len(html),
                        "content_type": content_type[:50] if content_type else "N/A"
                    }
            elif status == 429:
                return {"name": engine["name"], "status": "❌ RATE LIMIT (429)", "status_code": status}
            elif status == 403:
                return {"name": engine["name"], "status": "❌ BLOQUEADO (403)", "status_code": status}
            elif status == 404:
                return {"name": engine["name"], "status": "❌ NÃO ENCONTRADO (404)", "status_code": status}
            else:
                return {"name": engine["name"], "status": f"❌ ERRO HTTP {status}", "status_code": status}
                
    except asyncio.TimeoutError:
        return {"name": engine["name"], "status": "❌ TIMEOUT", "error": "Demorou muito"}
    except Exception as e:
        return {"name": engine["name"], "status": "❌ ERRO CONEXÃO", "error": str(e)[:100]}

async def main():
    print("=" * 80)
    print("TESTE COMPLETO DE TODAS AS APIS E ENGINES DE BUSCA")
    print("=" * 80)
    print(f"\nQuery de teste: 'python'\n")
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for engine in ENGINES:
            task = test_engine(session, engine)
            tasks.append(task)
            await asyncio.sleep(0.5)  # Delay entre requisições
        
        # Executa todos os testes
        results = await asyncio.gather(*tasks)
    
    # Organiza resultados
    print("\n" + "=" * 80)
    print("RESULTADOS:")
    print("=" * 80)
    
    working = []
    blocked = []
    errors = []
    
    for result in results:
        name = result["name"]
        status = result["status"]
        
        if "✓" in status:
            working.append(result)
        elif "❌" in status or "⚠" in status:
            if "BLOQUEADO" in status or "RATE LIMIT" in status:
                blocked.append(result)
            else:
                errors.append(result)
        
        print(f"\n{name}:")
        print(f"  Status: {status}")
        for key, value in result.items():
            if key not in ["name", "status"]:
                print(f"  {key}: {value}")
    
    print("\n" + "=" * 80)
    print("RESUMO:")
    print("=" * 80)
    print(f"✓ Funcionando: {len(working)}/{len(results)}")
    print(f"❌ Bloqueadas: {len(blocked)}/{len(results)}")
    print(f"⚠ Erros: {len(errors)}/{len(results)}")
    
    if working:
        print("\nEngines funcionando:")
        for r in working:
            print(f"  - {r['name']}")
    
    if blocked:
        print("\nEngines bloqueadas:")
        for r in blocked:
            print(f"  - {r['name']}: {r['status']}")
    
    if errors:
        print("\nEngines com erros:")
        for r in errors:
            print(f"  - {r['name']}: {r.get('error', 'Erro desconhecido')}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
