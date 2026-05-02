import asyncio
import aiohttp
import json
from urllib.parse import quote_plus

# Teste individual das APIs
async def test_api(name, url, parse_func):
    """Testa uma API específica"""
    print(f"\n{'='*60}")
    print(f"Testando: {name}")
    print(f"URL: {url}")
    print('='*60)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json" if "api" in url.lower() else "text/html",
    }
    
    # Wikipedia requer header Accept específico e User-Agent informativo
    if "wikipedia.org" in url:
        headers["Accept"] = "application/json"
        headers["User-Agent"] = "TestSearchApp/1.0 (contact: test@example.com)"
    
    # Reddit requer User-Agent específico (não pode ser genérico ou vazio)
    if "reddit.com" in url:
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        headers["Accept"] = "application/json"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15, ssl=False) as response:
                print(f"Status: {response.status}")
                content_type = response.headers.get('Content-Type', '')
                print(f"Content-Type: {content_type}")
                
                if response.status == 200:
                    if 'application/json' in content_type:
                        data = await response.json()
                        results = parse_func(data)
                        print(f"✓ Resultados encontrados: {len(results)}")
                        if results:
                            print(f"\nPrimeiro resultado:")
                            print(f"  Título: {results[0].get('title', 'N/A')}")
                            print(f"  URL: {results[0].get('url', 'N/A')}")
                            print(f"  Conteúdo: {results[0].get('content', 'N/A')[:100]}...")
                        return len(results) > 0
                    else:
                        html = await response.text()
                        print(f"Tamanho do HTML: {len(html)} bytes")
                        return len(html) > 0
                elif response.status == 429:
                    print("✗ Rate limit (429)")
                    return False
                elif response.status == 403:
                    print("✗ Acesso negado (403)")
                    return False
                else:
                    print(f"✗ Erro HTTP {response.status}")
                    return False
                    
    except asyncio.TimeoutError:
        print("✗ Timeout")
        return False
    except Exception as e:
        print(f"✗ Erro: {str(e)[:100]}")
        return False

# Funções de parse
def parse_wikipedia(json_data):
    results = []
    try:
        search_results = json_data.get('query', {}).get('search', [])
        for item in search_results[:10]:
            title = item.get('title', 'Sem título')
            snippet = item.get('snippet', 'Sem descrição')
            import re
            snippet = re.sub(r'<[^>]+>', '', snippet)
            results.append({
                "title": title,
                "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                "content": snippet,
            })
    except Exception as e:
        print(f"Erro no parse: {e}")
    return results

def parse_github(json_data):
    results = []
    try:
        items = json_data.get('items', [])
        for item in items[:10]:
            title = item.get('full_name', 'Sem título')
            description = item.get('description', 'Sem descrição') or 'Sem descrição'
            html_url = item.get('html_url', '')
            results.append({
                "title": title,
                "url": html_url,
                "content": description,
            })
    except Exception as e:
        print(f"Erro no parse: {e}")
    return results

def parse_gitlab(json_data):
    results = []
    try:
        for item in json_data[:10]:
            title = item.get('name_with_namespace', 'Sem título')
            description = item.get('description', 'Sem descrição') or 'Sem descrição'
            html_url = item.get('web_url', '')
            results.append({
                "title": title,
                "url": html_url,
                "content": description,
            })
    except Exception as e:
        print(f"Erro no parse: {e}")
    return results

def parse_reddit(json_data):
    results = []
    try:
        posts = json_data.get('data', {}).get('children', [])
        for post in posts[:10]:
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
            })
    except Exception as e:
        print(f"Erro no parse: {e}")
    return results

def parse_stackoverflow(json_data):
    results = []
    try:
        items = json_data.get('items', [])
        for item in items[:10]:
            title = item.get('title', 'Sem título')
            question_id = item.get('question_id', '')
            link = item.get('link', f'https://stackoverflow.com/questions/{question_id}')
            snippet = item.get('body', 'Sem descrição') or 'Sem descrição'
            import re
            snippet = re.sub(r'<[^>]+>', '', snippet)
            results.append({
                "title": title,
                "url": link,
                "content": snippet[:200] if len(snippet) > 200 else snippet,
            })
    except Exception as e:
        print(f"Erro no parse: {e}")
    return results

async def main():
    query = "python"
    print(f"Query de teste: '{query}'\n")
    
    tests = [
        ("Wikipedia API", 
         f"https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srprop=snippet|title&srlimit=10&srsearch={quote_plus(query)}",
         parse_wikipedia),
        
        ("GitHub API", 
         f"https://api.github.com/search/repositories?q={quote_plus(query)}",
         parse_github),
        
        ("GitLab API", 
         f"https://gitlab.com/api/v4/projects?search={quote_plus(query)}",
         parse_gitlab),
        
        ("Reddit API", 
         f"https://old.reddit.com/search.json?q={quote_plus(query)}&limit=10",
         parse_reddit),
        
        ("StackOverflow API", 
         f"https://api.stackexchange.com/2.3/search?order=desc&sort=relevance&site=stackoverflow&intitle={quote_plus(query)}",
         parse_stackoverflow),
    ]
    
    results = {}
    for name, url, parse_func in tests:
        success = await test_api(name, url, parse_func)
        results[name] = "✓ FUNCIONANDO" if success else "✗ FALHOU"
        await asyncio.sleep(1)  # Delay entre testes
    
    print(f"\n{'='*60}")
    print("RESUMO DOS TESTES")
    print('='*60)
    for name, status in results.items():
        print(f"{name}: {status}")
    
    success_count = sum(1 for v in results.values() if "✓" in v)
    total = len(results)
    print(f"\nTotal: {success_count}/{total} APIs funcionando")

if __name__ == "__main__":
    asyncio.run(main())
