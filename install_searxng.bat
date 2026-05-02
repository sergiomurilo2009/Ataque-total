@echo off
REM ============================================================
REM SearXNG para Windows - Instalador Automatizado
REM ============================================================
REM Este script instala e inicia o SearXNG automaticamente
REM Fornecendo uma URL local pronta para uso
REM ============================================================

echo.
echo ============================================================
echo   SearXNG para Windows - Instalador Automatizado
echo ============================================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python não encontrado!
    echo.
    echo Por favor, instale o Python em: https://python.org
    echo Marque a opção "Add Python to PATH" durante a instalação.
    pause
    exit /b 1
)

echo [OK] Python detectado
python --version
echo.

REM Instalar dependência aiohttp se necessário
echo [INFO] Verificando dependências...
pip show aiohttp >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Instalando aiohttp...
    pip install aiohttp --quiet
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao instalar aiohttp
        pause
        exit /b 1
    )
    echo [OK] aiohttp instalado com sucesso
) else (
    echo [OK] aiohttp já está instalado
)
echo.

REM Verificar arquivos necessários
if not exist "main.py" (
    echo [ERRO] Arquivo main.py não encontrado!
    echo Certifique-se de estar no diretório correto.
    pause
    exit /b 1
)

if not exist "searxng_config.json" (
    echo [INFO] Criando configuração padrão...
    python main.py --config searxng_config.json 2>nul
)

echo.
echo ============================================================
echo   INICIANDO SERVIDOR SEARXNG
echo ============================================================
echo.

REM Iniciar servidor em background
echo [INFO] Iniciando servidor web na porta 8080...
start /B python main.py --web --port 8080 --host 0.0.0.0

REM Aguardar servidor iniciar
echo [INFO] Aguardando servidor inicializar...
timeout /t 5 /nobreak >nul

echo.
echo ============================================================
echo   ✅ SEARXNG INSTALADO E FUNCIONANDO!
echo ============================================================
echo.
echo   🌐 Acesse no navegador:
echo.
echo      http://localhost:8080
echo.
echo   Ou na rede local:
echo.
echo      http://%COMPUTERNAME%:8080
echo.
echo ============================================================
echo.
echo   🔹 Funcionalidades:
echo      • 12+ motores de busca (Google, Bing, Yandex, etc.)
echo      • Interface moderna igual ao SearXNG original
echo      • Bangs: !yandex, !wiki, !github, !reddit, etc.
echo      • Sem rastreamento de IP ou cookies
echo      • Resultados agrupados por categoria
echo.
echo   🔹 Para parar o servidor:
echo      • Feche a janela do terminal que abriu
echo      • Ou pressione Ctrl+C nela
echo.
echo ============================================================
echo.

REM Abrir navegador automaticamente
echo [INFO] Abrindo navegador...
start http://localhost:8080

echo.
echo Pressione qualquer tecla para fechar este instalador...
pause >nul
