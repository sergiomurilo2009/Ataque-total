# 🚀 SearXNG para Windows - Guia de Instalação e Uso

## ✅ O Que É Isso?

Um **mecanismo de metabusca privado** estilo SearXNG, nativo para Windows, que agrega resultados de múltiplos motores de busca (Bing, DuckDuckGo, Yandex, GitHub, Wikipedia, Reddit, etc.) em uma única interface limpa e sem rastreamento.

---

## ⚡ Instalação Rápida (1 Clique)

### Método Automático (Recomendado)

1. **Baixe ou clone este repositório**
2. **Execute o instalador:**
   ```
   install_searxng.bat
   ```

O script fará automaticamente:
- ✅ Verifica se Python está instalado
- ✅ Instala a dependência `aiohttp` se necessário
- ✅ Inicia o servidor web
- ✅ Abre seu navegador em `http://localhost:8080`

### Método Manual

```bash
# 1. Instale Python (https://python.org)
# Marque "Add Python to PATH" durante a instalação

# 2. Instale a dependência
pip install aiohttp

# 3. Inicie o servidor
python main.py --web --port 8080

# 4. Acesse no navegador
http://localhost:8080
```

---

## 🔍 Como Usar

### Interface Web

Após iniciar, acesse **http://localhost:8080** e:

1. Digite sua pesquisa na barra central
2. Selecione categorias na sidebar esquerda (opcional)
3. Veja resultados agregados de múltiplos engines
4. Cada resultado mostra qual engine o encontrou

### Bangs (Atalhos de Pesquisa)

Use comandos especiais para buscar em engines específicos:

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!yandex` | Buscar apenas no Yandex | `!yandex python tutorial` |
| `!bing` | Buscar apenas no Bing | `!bing receitas` |
| `!ddg` | Buscar no DuckDuckGo | `!ddg privacy tools` |
| `!wiki` | Buscar na Wikipedia | `!wiki machine learning` |
| `!github` | Buscar no GitHub | `!github rust async` |
| `!yt` | Buscar no YouTube | `!yt guitar lessons` |
| `!reddit` | Buscar no Reddit | `!reddit linux tips` |
| `!so` | Buscar no Stack Overflow | `!so python list comprehension` |
| `!brave` | Buscar no Brave Search | `!brave news` |

### Linha de Comando

```bash
# Busca simples
python main.py --search "python tutorial"

# Com bang
python main.py --search "!yandex linux distro"

# Demonstração
python main.py --demo
```

---

## 📂 Categorias Disponíveis

- 🌐 **Geral**: Resultados web padrão (Bing, DuckDuckGo, Yandex, Brave)
- 💻 **TI & Código**: GitHub, GitLab, StackOverflow
- 🎓 **Ciência**: Wikipedia, artigos acadêmicos
- 🎬 **Vídeos**: YouTube, Dailymotion
- 💬 **Redes Sociais**: Reddit
- 🖼️ **Imagens**: Pexels

---

## 🔒 Fluxo de Privacidade

Assim como o SearXNG original, este sistema:

1. **Recebe sua query** e remove dados pessoais (IP, cookies, user-agent real)
2. **Traduz e envia** para todos os engines simultaneamente (fan-out)
3. **Coleta e limpa** resultados, removendo anúncios e trackers
4. **Desduplica** resultados repetidos entre engines
5. **Entrega anonimizada** - links diretos sem redirecionadores

**Importante:** Seu IP nunca é exposto aos engines de busca. Eles veem apenas o servidor local rodando o SearXNG.

---

## 🛠️ Configuração

O arquivo `searxng_config.json` (gerado automaticamente) permite:

- Habilitar/desabilitar engines específicos
- Personalizar ordem de relevância
- Configurar timeout e retries

Exemplo:
```json
{
  "engines": [
    {"name": "Bing", "enabled": true},
    {"name": "Yandex", "enabled": true},
    {"name": "GitHub", "enabled": false}
  ]
}
```

---

## ⚠️ Solução de Problemas

### "Python não encontrado"
- Instale o Python em https://python.org
- **IMPORTANTE:** Marque a opção "Add Python to PATH" durante a instalação
- Reinicie o terminal/computador após instalar

### "aiohttp não encontrado"
- Execute: `pip install aiohttp`
- Ou deixe o `install_searxng.bat` instalar automaticamente

### Engines retornando 0 resultados
- **No Windows:** Pode ser temporário. Tente novamente.
- **Em servidores/nuvem:** Muitos engines bloqueiam IPs de datacenters. Use em uma conexão residencial.
- Verifique sua conexão com a internet
- Alguns engines podem mudar seu HTML e quebrar o parser (atualize os regex no código)

### Porta 8080 já em uso
- Use outra porta: `python main.py --web --port 9000`
- Ou feche outros programas usando a porta 8080

### Windows Defender/Anti-vírus bloqueando
- Adicione uma exceção para a pasta do SearXNG
- O script é seguro - apenas Python executando código local

---

## 📋 Requisitos

- **Sistema:** Windows 10/11 (também funciona em Linux/Mac)
- **Python:** 3.8 ou superior
- **Dependência:** aiohttp (instalada automaticamente)
- **Navegador:** Qualquer navegador moderno (Chrome, Firefox, Edge)

---

## 🎯 Engines Suportados

| Engine | Categoria | Status |
|--------|-----------|--------|
| Bing | Geral | ✅ |
| DuckDuckGo | Geral | ✅ |
| Yandex | Geral | ✅ |
| Brave | Geral | ✅ |
| GitHub | TI | ✅ |
| GitLab | TI | ✅ |
| Wikipedia | Ciência | ✅ |
| Reddit | Social | ✅ |
| StackOverflow | TI | ✅ |
| YouTube | Vídeos | ✅ |
| Dailymotion | Vídeos | ✅ |
| Pexels | Imagens | ✅ |

---

## 💡 Dicas de Uso

1. **Use bangs** para pesquisas mais rápidas e específicas
2. **Filtre por categoria** para reduzir ruído nos resultados
3. **Combine engines** desativando os que não usa no config
4. **Use no Windows** para melhor compatibilidade com os engines

---

## 📄 Licença

Este projeto é uma implementação educacional inspirada no SearXNG original (https://github.com/searxng/searxng).

---

## 🙏 Créditos

- Inspirado no projeto **SearXNG** original
- Desenvolvido para funcionar nativamente no Windows
- Interface web moderna e responsiva

---

## 🆘 Suporte

Para issues relacionados a:
- **Parsers quebrados:** Atualize os regex no `main.py`
- **Engines bloqueados:** Use proxies ou VPN
- **Bugs na interface:** Verifique o console do navegador (F12)

**Divirta-se pesquisando com privacidade! 🔍**
