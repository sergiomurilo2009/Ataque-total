@echo off
chcp 65001 >nul
echo ============================================================
echo   Ataque-total Search - Instalador e Executor Automatico
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

:: Limpar cache Python antigo e banco de cache
echo [INFO] Limpando cache...
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "engines\__pycache__" rmdir /s /q "engines\__pycache__"
if exist "utils\__pycache__" rmdir /s /q "utils\__pycache__"
if exist "web\__pycache__" rmdir /s /q "web\__pycache__"
if exist "search_cache.db" del /q "search_cache.db"
echo [OK] Cache limpo
echo.

:: Verificar porta 8080
netstat -ano | findstr ":8080" >nul 2>&1
if %errorlevel% equ 0 (
    echo [AVISO] Porta 8080 ja esta em uso!
    echo Deseja continuar mesmo assim? (S/N)
    set /p CONTINUE="Resposta: "
    if /i not "%CONTINUE%"=="S" (
        exit /b 1
    )
)

:: Instalar dependencias rapidamente sem cache
echo [INFO] Instalando/verificando dependencias...
echo [INFO] Isso pode levar alguns segundos na primeira vez...
pip install aiohttp beautifulsoup4 lxml jinja2 --quiet --no-cache-dir --no-warn-script-location
if %errorlevel% equ 0 (
    echo [OK] Dependencias instaladas/verificadas
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

:: Obter IP local da rede
set LOCAL_IP=127.0.0.1
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"Endereco IPv4"') do (
    for %%b in (%%a) do set LOCAL_IP=%%b
    goto :got_ip
)
:got_ip

echo ============================================================
echo   Iniciando Ataque-total Search Server...
echo ============================================================
echo.
echo Servidor disponivel em:
echo   Local: http://127.0.0.1:8080
echo   Rede:  http://%LOCAL_IP%:8080
echo.
echo Cache: DESATIVADO (resultados sempre atualizados)
echo Engines ativos: Bing, DuckDuckGo, Wikipedia, GitHub, StackOverflow
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

:: Iniciar servidor sem cache (HOST 0.0.0.0 para acesso na rede)
python main.py --server --host 0.0.0.0 --port 8080 --no-cache

pause
