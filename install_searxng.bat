@echo off
chcp 65001 >nul
echo ============================================================
echo   SearXNG Windows - Instalador e Executor Automatico
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

:: Atualizar pip rapidamente
echo [INFO] Atualizando pip...
python -m pip install --upgrade pip --quiet --no-warn-script-location
echo [OK] Pip atualizado
echo.

:: Limpar cache Python antigo
echo [INFO] Limpando cache...
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "search_cache.db" del /q "search_cache.db"
echo [OK] Cache limpo
echo.

:: Instalar dependencias rapidamente sem cache
echo [INFO] Instalando dependencias necessarias...
echo [INFO] Isso pode levar alguns segundos na primeira vez...
pip install aiohttp beautifulsoup4 lxml jinja2 --quiet --no-cache-dir --no-warn-script-location
if %errorlevel% equ 0 (
    echo [OK] Dependencias instaladas com sucesso
) else (
    echo [ERRO] Falha ao instalar dependencias
    pause
    exit /b 1
)
echo.

:: Verificar se o arquivo main.py existe
if not exist "main.py" (
    echo [ERRO] Arquivo main.py nao encontrado!
    echo Certifique-se de que esta executando o instalador no diretorio correto.
    pause
    exit /b 1
)

:: Obter IP local
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    for %%b in (%%a) do set LOCAL_IP=%%b
)
if "%LOCAL_IP%"=="" set LOCAL_IP=127.0.0.1

echo ============================================================
echo   Iniciando SearXNG Server...
echo ============================================================
echo.
echo Servidor disponivel em:
echo   Local: http://127.0.0.1:8080
echo   Rede:  http://%LOCAL_IP%:8080
echo.
echo Cache: DESATIVADO (resultados sempre atualizados)
echo.
echo Abrindo navegador em 3 segundos...
echo.
echo Pressione Ctrl+C para parar o servidor
echo ============================================================
echo.

:: Aguardar 3 segundos antes de abrir o navegador
timeout /t 3 /nobreak >nul

:: Tentar abrir Chrome, se nao existir tenta Edge ou navegador padrao
start chrome.exe http://127.0.0.1:8080 2>nul || start microsoft-edge:http://127.0.0.1:8080 2>nul || start http://127.0.0.1:8080

:: Iniciar servidor sem cache
python main.py --server --port 8080 --no-cache

pause
