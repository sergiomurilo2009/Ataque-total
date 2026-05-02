"""
Web routes for Ataque-total Search Engine
Uses aiohttp web framework with Jinja2 templates
"""
import json
import time
from pathlib import Path
from aiohttp import web
from jinja2 import Environment, FileSystemLoader


def create_app(core):
    """Create and configure the web application"""
    app = web.Application()
    
    # Store core in app state
    app['core'] = core
    
    # Setup Jinja2 environment
    template_dir = Path(__file__).parent / 'templates'
    app['jinja_env'] = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=True
    )
    
    # Add routes
    app.router.add_get('/', handle_search)
    app.router.add_get('/search', handle_search)
    app.router.add_get('/health', handle_health)
    app.router.add_get('/api/search', handle_api_search)
    app.router.add_get('/api/engines', handle_api_engines)
    app.router.add_post('/api/cache/clear', handle_cache_clear)
    
    return app


async def render_template(request, template_name: str, **kwargs):
    """Render a Jinja2 template"""
    env = request.app['jinja_env']
    template = env.get_template(template_name)
    html = template.render(**kwargs)
    return web.Response(text=html, content_type='text/html')


async def handle_search(request):
    """Handle web search requests"""
    core = request.app['core']
    
    query = request.query.get('q', '')
    category = request.query.get('category', 'general')
    page = int(request.query.get('page', 1))
    
    if not query:
        # Show homepage
        return await render_template(
            request, 
            'search.html',
            query='',
            results=[],
            engines_used=[],
            search_time=0,
            categories=core.get_categories(),
            current_category=category,
            error=None
        )
    
    try:
        start_time = time.time()
        result = await core.search(query, category=category, page=page)
        search_time = time.time() - start_time
        
        return await render_template(
            request,
            'search.html',
            query=query,
            results=result.get('results', []),
            engines_used=result.get('engines_used', []),
            search_time=search_time,
            categories=core.get_categories(),
            current_category=category,
            error=result.get('error')
        )
        
    except Exception as e:
        return await render_template(
            request,
            'search.html',
            query=query,
            results=[],
            engines_used=[],
            search_time=0,
            categories=core.get_categories(),
            current_category=category,
            error=str(e)
        )


async def handle_health(request):
    """Health check endpoint"""
    core = request.app['core']
    
    stats = core.get_cache_stats()
    engines = core.get_available_engines()
    
    health_data = {
        'status': 'healthy',
        'timestamp': time.time(),
        'cache': stats,
        'engines': {
            'total': len(engines),
            'enabled': sum(1 for e in engines if e['enabled'])
        },
        'categories': core.get_categories()
    }
    
    return web.json_response(health_data)


async def handle_api_search(request):
    """API search endpoint - returns JSON"""
    core = request.app['core']
    
    query = request.query.get('q', '')
    category = request.query.get('category', 'general')
    page = int(request.query.get('page', 1))
    use_cache = request.query.get('cache', 'true').lower() == 'true'
    
    if not query:
        return web.json_response({
            'error': 'Query parameter "q" is required'
        }, status=400)
    
    try:
        result = await core.search(
            query, 
            category=category, 
            page=page,
            use_cache=use_cache
        )
        return web.json_response(result)
        
    except Exception as e:
        return web.json_response({
            'error': str(e)
        }, status=500)


async def handle_api_engines(request):
    """API endpoint to list available engines"""
    core = request.app['core']
    
    engines = core.get_available_engines()
    categories = core.get_categories()
    bangs = core.bangs
    
    return web.json_response({
        'engines': engines,
        'categories': categories,
        'bangs': bangs
    })


async def handle_cache_clear(request):
    """API endpoint to clear cache"""
    core = request.app['core']
    core.clear_cache()
    
    return web.json_response({
        'status': 'success',
        'message': 'Cache cleared'
    })
