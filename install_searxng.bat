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

:: Instalar aiohttp se necessario
echo [INFO] Verificando dependencias...
pip show aiohttp >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Instalando aiohttp...
    pip install aiohttp --quiet
    if %errorlevel% equ 0 (
        echo [OK] aiohttp instalado com sucesso
    ) else (
        echo [ERRO] Falha ao instalar aiohttp
        pause
        exit /b 1
    )
) else (
    echo [OK] aiohttp ja esta instalado
)
echo.

:: Iniciar o servidor
echo ============================================================
echo   Iniciando SearXNG Windows...
echo ============================================================
echo.
echo O navegador sera aberto automaticamente em:
echo http://localhost:8080
echo.
echo Pressione Ctrl+C para parar o servidor
echo ============================================================
echo.

python main.py --web --port 8080

pause
