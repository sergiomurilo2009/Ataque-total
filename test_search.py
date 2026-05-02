"""Teste rápido de pesquisa"""
import asyncio
from core import SearchCore

async def test():
    core = SearchCore()
    result = await core.search('test', use_cache=False)
    print(f"Resultados: {len(result.get('results', []))}")
    print(f"Engines usadas: {result.get('engines_used', [])}")
    print(f"Tempo: {result.get('search_time', 0):.2f}s")
    
    if result.get('error'):
        print(f"Erro: {result['error']}")
    
    for r in result.get('results', [])[:3]:
        print(f"\n- {r['title']}")
        print(f"  URL: {r['url']}")
        print(f"  Engine: {r['engine']}")

if __name__ == '__main__':
    asyncio.run(test())
