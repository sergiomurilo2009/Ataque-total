@echo off
chcp 65001 >nul
echo ============================================================
echo   SearXNG Windows - Instalador Automatico
echo ============================================================
echo.

:: Verificar se Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Por favor, instale o Python em: https://python.org
    echo Marque a opcao "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

echo [OK] Python detectado
python --version
echo.

:: Instalar todas as dependencias do requirements.txt
echo [INFO] Verificando e instalando dependencias...
echo.

:: Lista de todas as dependencias necessarias
echo [INFO] Instalando aiohttp...
pip install aiohttp>=3.9.0 --quiet
if %errorlevel% equ 0 (
    echo [OK] aiohttp instalado
) else (
    echo [ERRO] Falha ao instalar aiohttp
    pause
    exit /b 1
)

echo [INFO] Instalando aiohttp-socks...
pip install aiohttp-socks>=0.8.0 --quiet
if %errorlevel% equ 0 (
    echo [OK] aiohttp-socks instalado
) else (
    echo [AVISO] Falha ao instalar aiohttp-socks (opcional)
)

echo [INFO] Instalando beautifulsoup4...
pip install beautifulsoup4>=4.12.0 --quiet
if %errorlevel% equ 0 (
    echo [OK] beautifulsoup4 instalado
) else (
    echo [ERRO] Falha ao instalar beautifulsoup4
    pause
    exit /b 1
)

echo [INFO] Instalando lxml...
pip install lxml>=5.0.0 --quiet
if %errorlevel% equ 0 (
    echo [OK] lxml instalado
) else (
    echo [ERRO] Falha ao instalar lxml
    pause
    exit /b 1
)

echo [INFO] Instalando jinja2...
pip install jinja2>=3.1.0 --quiet
if %errorlevel% equ 0 (
    echo [OK] jinja2 instalado
) else (
    echo [ERRO] Falha ao instalar jinja2
    pause
    exit /b 1
)

echo [INFO] Instalando pyyaml...
pip install pyyaml>=6.0 --quiet
if %errorlevel% equ 0 (
    echo [OK] pyyaml instalado
) else (
    echo [AVISO] Falha ao instalar pyyaml (opcional)
)

echo [INFO] Instalando structlog...
pip install structlog>=24.0.0 --quiet
if %errorlevel% equ 0 (
    echo [OK] structlog instalado
) else (
    echo [AVISO] Falha ao instalar structlog (opcional)
)

echo [INFO] Instalando python-dateutil...
pip install python-dateutil>=2.8.0 --quiet
if %errorlevel% equ 0 (
    echo [OK] python-dateutil instalado
) else (
    echo [AVISO] Falha ao instalar python-dateutil (opcional)
)

echo.
echo [OK] Todas as dependencias foram verificadas/instaladas
echo.

:: Atualizar pip antes de continuar (opcional, mas recomendado)
echo [INFO] Atualizando pip...
python -m pip install --upgrade pip --quiet
echo.

:: Verificar se o arquivo main.py existe
if not exist "main.py" (
    echo [ERRO] Arquivo main.py nao encontrado!
    echo Certifique-se de que esta executando o instalador no diretorio correto.
    pause
    exit /b 1
)

:: Verificar se o diretorio config existe
if not exist "config\" (
    echo [AVISO] Diretorio config nao encontrado, criando...
    mkdir config
)

:: Iniciar o servidor
echo ============================================================
echo   Iniciando SearXNG Windows...
echo ============================================================
echo.
echo Servidor web disponivel em:
echo http://localhost:8080
echo http://127.0.0.1:8080
echo.
echo Endpoints disponiveis:
echo   - Homepage: http://localhost:8080/
echo   - API Search: http://localhost:8080/api/search?q=seu_termo
echo   - API Engines: http://localhost:8080/api/engines
echo   - Health Check: http://localhost:8080/health
echo.
echo Pressione Ctrl+C para parar o servidor
echo ============================================================
echo.

python main.py --server --port 8080

pause
