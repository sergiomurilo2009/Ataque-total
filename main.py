"""
Ataque-total Search Engine - Main Entry Point
Modern, modular architecture with:
- BeautifulSoup + lxml for robust HTML parsing
- Jinja2 template engine
- Configurable engines via JSON
- Caching, deduplication, and intelligent scoring
- Bang support (!wiki, !gh, !so, etc.)
- Rate limiting and User-Agent rotation
"""
import asyncio
import json
import argparse
import sys
from pathlib import Path

# Import core components
from core import SearchCore
from web.routes import create_app


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Ataque-total Search Engine - Privacy-focused meta-search',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --cli "python tutorial"
  python main.py --server --port 8080
  python main.py --cli "!wiki python"     # Search only Wikipedia
  python main.py --cli "!gh machine learning"  # Search only GitHub
  python main.py --json "api development"
  
Supported Bangs:
  !wiki, !w     - Wikipedia
  !gh, !git     - GitHub
  !so           - StackOverflow
  !yt           - YouTube
  !r, !reddit   - Reddit
  !g            - Google
  !b            - Bing
  !d            - DuckDuckGo
        """
    )
    
    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('--cli', '-c', action='store_true', 
                       help='Run in CLI mode (text output)')
    parser.add_argument('--json', '-j', action='store_true',
                       help='Output results as JSON')
    parser.add_argument('--server', '-s', action='store_true',
                       help='Start web server')
    parser.add_argument('--host', default='0.0.0.0',
                       help='Server host (default: 0.0.0.0)')
    parser.add_argument('--port', '-p', type=int, default=8080,
                       help='Server port (default: 8080)')
    parser.add_argument('--config', default='config/default.json',
                       help='Path to config file')
    parser.add_argument('--category', default='general',
                       help='Search category (default: general)')
    parser.add_argument('--no-cache', action='store_true',
                       help='Disable caching')
    parser.add_argument('--clear-cache', action='store_true',
                       help='Clear cache and exit')
    parser.add_argument('--engines', action='store_true',
                       help='List available engines')
    parser.add_argument('--health', action='store_true',
                       help='Health check endpoint')
    
    return parser.parse_args()


async def run_cli_search(core: SearchCore, query: str, args):
    """Run search in CLI mode"""
    result = await core.search(
        query,
        category=args.category,
        use_cache=not args.no_cache
    )
    
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Text output
        if result.get('error'):
            print(f"Error: {result['error']}")
            return
        
        # Check for missing fields
        if 'total_results' not in result:
            result['total_results'] = len(result.get('results', []))
        if 'engines_used' not in result:
            result['engines_used'] = list(set(r.get('engine', 'Unknown') for r in result.get('results', [])))
        if 'search_time' not in result:
            result['search_time'] = 0
        
        print(f"\n{'='*60}")
        print(f"Query: {result.get('original_query', query)}")
        if result.get('target_engine'):
            print(f"Engine: {result['target_engine']}")
        print(f"Results: {result['total_results']} from {len(result['engines_used'])} engines")
        print(f"Time: {result['search_time']:.2f}s")
        print(f"{'='*60}\n")
        
        for i, r in enumerate(result['results'], 1):
            print(f"{i}. {r['title']}")
            print(f"   URL: {r['url']}")
            print(f"   {r['content'][:200]}...")
            print(f"   [{r['engine']}] Score: {r.get('score', 'N/A')}")
            print()


async def async_main(args):
    """Async main entry point"""
    # Desabilitar cache se solicitado
    if args.no_cache:
        import os
        os.environ['SEARCH_NO_CACHE'] = '1'
    
    core = SearchCore(config_path=args.config)
    
    # Se no-cache estiver ativado, desabilitar cache do core
    if args.no_cache and core.cache:
        core.cache = None
    
    # Handle commands
    if args.clear_cache:
        core.clear_cache()
        print("Cache cleared successfully")
        return
    
    if args.engines:
        engines = core.get_available_engines()
        print("\nAvailable Engines:")
        print("-" * 40)
        for eng in engines:
            status = "✓" if eng['enabled'] else "✗"
            print(f"  [{status}] {eng['name']:15} Category: {eng['category']}, Weight: {eng['weight']}")
        print()
        return
    
    if args.health:
        stats = core.get_cache_stats()
        print(json.dumps({
            'status': 'healthy',
            'cache': stats,
            'engines': len(core.get_available_engines())
        }, indent=2))
        return
    
    if args.server:
        # Start web server
        app = create_app(core)
        
        # Get local IP for display
        import socket
        local_ip = "127.0.0.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            pass
        
        print(f"\n🚀 Starting Ataque-total Search Server")
        print(f"   📍 URL Local: http://127.0.0.1:{args.port}")
        print(f"   🌐 URL Rede: http://{local_ip}:{args.port}")
        print(f"   🔓 Cache: {'DESATIVADO' if args.no_cache else 'ATIVADO'}")
        print(f"   🛑 Pressione Ctrl+C para parar\n")
        
        # Use aiohttp to run server
        from aiohttp import web
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, args.host, args.port)
        await site.start()
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            print("\nShutting down...")
            await runner.cleanup()
        return
    
    # CLI search
    if args.query:
        await run_cli_search(core, args.query, args)
    else:
        # Interactive mode
        print("\nAtaque-total Search Engine")
        print("=" * 40)
        print("Type your query (or 'quit' to exit)")
        print("Use bangs: !wiki, !gh, !so, !yt, !r\n")
        
        while True:
            try:
                query = input("> ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                if not query:
                    continue
                
                await run_cli_search(core, query, args)
                
            except KeyboardInterrupt:
                print("\n")
                break
            except EOFError:
                break


def main():
    """Main entry point"""
    args = parse_args()
    
    try:
        asyncio.run(async_main(args))
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
