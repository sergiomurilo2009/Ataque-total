# 🚀 SearXNG para Windows - Instalador Rápido

## ⚡ Instalação em 1 Clique

### Opção 1: Script Automático (Recomendado)

1. **Baixe o instalador:**
   ```powershell
   # Salve este arquivo como install_searxng.bat
   ```

2. **Execute o instalador:**
   - Dê dois cliques em `install_searxng.bat`
   - O script fará tudo automaticamente!

3. **Acesse:**
   - O navegador abrirá automaticamente em: **http://localhost:8080**

---

### Opção 2: Manual (3 comandos)

```bash
# 1. Instalar dependência
pip install aiohttp

# 2. Iniciar servidor
python main.py --web --port 8080

# 3. Acessar no navegador
# http://localhost:8080
```

---

## 🎯 Funcionalidades

### 🔍 Motores de Busca Incluídos
- **Gerais:** Bing, DuckDuckGo, **Yandex**, Qwant, Brave
- **TI:** GitHub, GitLab
- **Ciência:** arXiv, Wikipedia
- **Vídeos:** YouTube, Dailymotion
- **Social:** Reddit

### 🏷️ Bangs (Atalhos)
Use na barra de pesquisa:
```
!yandex python      → Busca apenas no Yandex
!wiki机器学习        → Busca na Wikipedia
!github rust        → Busca no GitHub
!reddit linux       → Busca no Reddit
!yt tutorial        → Busca no YouTube
!ddg privacy        → Busca no DuckDuckGo
```

### 📂 Categorias
- Geral
- Imagens
- Vídeos
- Notícias
- TI (Tecnologia)
- Ciência
- Mapas
- Música
- Redes Sociais

---

## 🔒 Privacidade Garantida

O SearXNG segue o fluxo completo de privacidade:

1. **Recebimento da Query:** Remove IP, cookies e dados do navegador
2. **Tradução e Envio:** Envia para todos os engines simultaneamente
3. **Coleta e Limpeza:** Remove anúncios, trackers e duplicatas
4. **Entrega Anonimizada:** Links diretos sem redirecionadores

---

## 🛠️ Comandos Úteis

```bash
# Interface Web
python main.py --web --port 8080

# Busca via CLI
python main.py --search "python tutorial" -c general it

# Demonstração
python main.py --demo

# Porta customizada
python main.py --web --port 9000

# Ver ajuda
python main.py --help
```

---

## 📋 Requisitos

- Python 3.8+
- aiohttp (`pip install aiohttp`)
- Windows 10/11 (ou qualquer OS com Python)

---

## 🌐 URLs de Acesso

Após iniciar o servidor:

- **Local:** http://localhost:8080
- **Rede Local:** http://SEU_IP:8080
- **Hostname:** http://%COMPUTERNAME%:8080

---

## ✨ Como Funciona

```
Você digita → SearXNG recebe → Remove seus dados privados
                ↓
Envia para: Bing + DuckDuckGo + Yandex + Qwant + Brave + etc.
                ↓
Coleta resultados → Remove anúncios → Remove duplicatas
                ↓
Entrega página limpa e anonima para você!
```

---

## 🎉 Pronto!

É só executar o instalador e usar!

**URL padrão:** http://localhost:8080
