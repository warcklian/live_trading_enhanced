@echo off
setlocal enabledelayedexpansion
title ACTUALIZADOR DE REPOSITORIO GIT

echo ========================================
echo   ACTUALIZADOR DE REPOSITORIO GIT (.BAT)
echo ========================================

REM === Verifica si Git está instalado
where git >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git no está instalado. Por favor instálalo desde:
    echo https://git-scm.com/downloads
    pause
    exit /b
)

REM === Verifica si ya es un repositorio Git
if not exist ".git" (
    echo [INFO] No es un repositorio Git. Inicializando...
    git init
)

REM === Verifica si hay errores de merge o commit incompleto
if exist ".git\MERGE_HEAD" (
    echo [ERROR] Hay un merge pendiente. Debes resolver conflictos.
    choice /m "¿Quieres cancelar el merge y continuar desde cero?"
    if errorlevel 1 (
        git merge --abort
        echo [OK] Merge cancelado.
    ) else (
        echo [ABORTADO] Revisa manualmente los conflictos.
        pause
        exit /b
    )
)

REM === Verifica si el nombre y correo están configurados
for /f "tokens=* delims=" %%i in ('git config --global user.name') do set USERNAME=%%i
for /f "tokens=* delims=" %%i in ('git config --global user.email') do set USEREMAIL=%%i

if not defined USERNAME (
    set /p GITNAME="Ingresa tu nombre para Git: "
    git config --global user.name "!GITNAME!"
)

if not defined USEREMAIL (
    set /p GITEMAIL="Ingresa tu correo para Git: "
    git config --global user.email "!GITEMAIL!"
)

REM === Configura Git Credential Manager si no está
git config --global credential.helper manager-core >nul 2>&1

REM === Verifica si hay cambios sin agregar
git diff --quiet
if %errorlevel% neq 0 (
    echo [INFO] Tienes cambios sin agregar.
    choice /m "¿Deseas agregarlos automáticamente?"
    if errorlevel 1 (
        git add .
    ) else (
        echo [ABORTADO] No se agregaron cambios.
        pause
        exit /b
    )
)

REM === Quitar este .bat del commit
git reset -- %~nx0 >nul 2>&1

REM === Verifica si hay cambios para commitear
git diff --cached --quiet
if %errorlevel%==0 (
    echo [INFO] No hay cambios nuevos para hacer commit.
    pause
    exit /b
)

REM === Pide mensaje de commit
set /p COMMITMSG="Mensaje para el commit: "
git commit -m "!COMMITMSG!"

REM === Detectar si hay remote 'origin'
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No hay remote 'origin' configurado.
    set /p REMOTEURL="Ingresa la URL del repositorio remoto (HTTPS): "
    git remote add origin "!REMOTEURL!"
)

REM === Detectar rama actual
for /f "tokens=*" %%r in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%r

REM === Hacer push
echo.
echo === Subiendo cambios a la rama "!BRANCH!" ===
git push origin !BRANCH!

if %errorlevel% neq 0 (
    echo [ERROR] Falló el push. Puede ser por:
    echo - Token no configurado
    echo - Acceso denegado al repositorio
    echo - Requiere autenticación
    echo - Branch remoto no existe
    echo.
    choice /m "¿Deseas forzar push creando rama remota si es necesario?"
    if errorlevel 1 (
        git push -u origin !BRANCH!
    ) else (
        echo [ABORTADO] Push cancelado.
        pause
        exit /b
    )
)

echo.
echo ✅ ¡Repositorio actualizado correctamente!
pause
exit /b
