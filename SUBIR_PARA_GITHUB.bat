@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Subir projeto para o GitHub
echo ========================================
echo.

cd /d "%~dp0"

where git >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Git não está instalado.
    echo.
    echo Baixe e instale o Git em: https://git-scm.com/download/win
    echo Depois execute este script novamente.
    echo.
    pause
    exit /b 1
)

if not exist ".git" (
    echo Inicializando repositório...
    git init
    git branch -M main
    echo.
)

echo Adicionando arquivos...
git add .
echo.

echo Fazendo commit...
git commit -m "Upload inicial - Dashboard de Metas Top Estética Bucal"
echo.

set /p REPO_URL="Cole a URL do seu repositório (ex: https://github.com/SEU_USUARIO/dashboard-metas.git): "

if "%REPO_URL%"=="" (
    echo URL não informada. Configure manualmente:
    echo   git remote add origin SUA_URL
    echo   git push -u origin main
    pause
    exit /b 0
)

git remote remove origin 2>nul
git remote add origin %REPO_URL%
echo.
echo Enviando para o GitHub...
git push -u origin main

if errorlevel 1 (
    echo.
    echo Se pedir login, use seu usuário e senha do GitHub.
    echo Ou crie um Personal Access Token em: https://github.com/settings/tokens
    echo.
)

echo.
echo Pronto!
pause
