# Ataque-total Search Engine

Modern, privacy-focused meta-search engine with modular architecture.

## 🚀 Key Features

- **Robust HTML Parsing**: Uses BeautifulSoup4 + lxml instead of fragile regex
- **Jinja2 Templates**: Professional template engine replacing custom regex-based rendering
- **Modular Architecture**: Separate engines/, utils/, web/ directories
- **Caching**: File-based caching (shelve) with configurable TTL
- **Intelligent Ranking**: Cross-engine scoring and deduplication
- **Bang Support**: `!wiki`, `!gh`, `!so`, `!yt`, `!r` for direct engine search
- **Rate Limiting**: Configurable delays per engine to avoid bans
- **User-Agent Rotation**: 80+ user agents rotated per request
- **SSL Option**: Configurable SSL verification (fallback mode available)
- **JSON API**: Full REST API for programmatic access
- **CLI & Web UI**: Both command-line and browser interfaces

## 📁 Project Structure

```
Ataque-total/
├── engines/           # Search engine implementations
│   ├── __init__.py
│   ├── base.py        # Abstract base class
│   └── bing.py        # Bing engine (example)
├── utils/             # Utility modules
│   ├── __init__.py
│   ├── cache.py       # Caching system
│   ├── dedup.py       # Deduplication
│   └── scoring.py     # Result ranking
├── web/               # Web interface
│   ├── __init__.py
│   ├── routes.py      # aiohttp routes
│   └── templates/
│       └── search.html
├── config/            # Configuration files
│   └── default.json
├── core.py            # Main search orchestration
├── main.py            # Entry point
└── requirements.txt   # Dependencies
```

## 🔧 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or manually
pip install aiohttp beautifulsoup4 lxml jinja2 pyyaml structlog
```

## 💻 Usage

### CLI Mode

```bash
# Basic search
python main.py --cli "python tutorial"

# JSON output
python main.py --json "api development"

# Bang search (specific engine)
python main.py --cli '!wiki python'
python main.py --cli '!gh machine learning'
python main.py --cli '!so async await'

# List engines
python main.py --engines

# Health check
python main.py --health

# Clear cache
python main.py --clear-cache
```

### Web Server

```bash
# Start server
python main.py --server --port 8080

# Custom host/port
python main.py --server --host 0.0.0.0 --port 9000
```

Then open: http://127.0.0.1:8080

### API Endpoints

```bash
# Search API
curl "http://127.0.0.1:8080/api/search?q=python+tutorial"

# List engines
curl "http://127.0.0.1:8080/api/engines"

# Health check
curl "http://127.0.0.1:8080/health"

# Clear cache
curl -X POST "http://127.0.0.1:8080/api/cache/clear"
```

## ⚙️ Configuration

Edit `config/default.json`:

```json
{
  "engines": {
    "Bing": {
      "enabled": true,
      "category": "general",
      "weight": 1.1,
      "timeout": 20,
      "delay_min": 0.4,
      "delay_max": 0.8
    }
  },
  "bangs": {
    "!wiki": "Wikipedia",
    "!gh": "GitHub",
    "!so": "StackOverflow"
  },
  "cache": {
    "enabled": true,
    "ttl_seconds": 900
  }
}
```

## 🎯 Supported Bangs

| Bang | Engine |
|------|--------|
| `!wiki`, `!w` | Wikipedia |
| `!gh`, `!git` | GitHub |
| `!so` | StackOverflow |
| `!yt` | YouTube |
| `!r`, `!reddit` | Reddit |
| `!g` | Google |
| `!b` | Bing |
| `!d` | DuckDuckGo |

## 🔒 Privacy & Security

- No query logging (or anonymized only)
- Referer header removal option
- Random X-Forwarded-For headers
- Optional proxy support
- SSL verification toggle

## 🏗️ Architecture Improvements

### Before (Problems Fixed)
- ❌ Pure regex scraping (fragile)
- ❌ `ssl=False` everywhere (insecure)
- ❌ No rate limiting (bans)
- ❌ Custom template engine (buggy)
- ❌ Monolithic code

### After (Solutions)
- ✅ BeautifulSoup + lxml parsing
- ✅ Configurable SSL verification
- ✅ Rate limiting + UA rotation
- ✅ Jinja2 templates
- ✅ Modular architecture

## 📊 Scoring System

Results are ranked by:
1. **Engine reliability** (Wikipedia > Reddit)
2. **Cross-engine presence** (same URL in multiple engines)
3. **Position** in original results
4. **Diversity** of sources

## 🧪 Testing

```bash
# Test all engines
python test_all_engines.py

# Test APIs
python test_apis.py
```

## 📝 TODO

- [ ] Implement more engines (Yandex, Qwant, etc.)
- [ ] Add image search support
- [ ] Redis cache option
- [ ] Proxy rotation
- [ ] Unit tests for parsers
- [ ] Docker container
- [ ] Browser extension

## 📄 License

MIT License

## 🤝 Contributing

1. Create engine in `engines/` extending `BaseEngine`
2. Add config in `config/default.json`
3. Test with `python main.py --engines`

---

**Built with**: Python 3.8+, aiohttp, BeautifulSoup4, lxml, Jinja2
