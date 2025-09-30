@echo off
REM 🚀 RAG ASISTENTE - ARRANQUE SIMPLE
REM ==================================
REM Script batch para arranque con doble-click
REM Detecta automáticamente si es primera vez o arranque diario

title RAG Asistente - Arranque Automático

echo.
echo 🚀 RAG ASISTENTE - ARRANQUE AUTOMÁTICO
echo ====================================
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"

REM Verificar si estamos en el directorio correcto
if not exist "manage.py" (
    echo ❌ Error: No se encontró manage.py
    echo    Asegúrate de que el script esté en el directorio backend/
    echo.
    pause
    exit /b 1
)

REM Verificar si el sistema ya está configurado
set CONFIGURED=0

if exist "chroma_db_simple\" (
    if exist ".env" (
        set CONFIGURED=1
    )
)

echo 📋 Detectando estado del sistema...
echo.

if %CONFIGURED%==1 (
    echo ✅ Sistema ya configurado - Arranque rápido
    echo.
    echo 🚀 Iniciando RAG Asistente...
    echo.
    powershell -ExecutionPolicy Bypass -File "ARRANCAR_RAG.ps1"
) else (
    echo ⚙️ Primera vez o configuración incompleta
    echo.
    echo 🔧 Ejecutando configuración completa...
    echo    Esto puede tomar varios minutos la primera vez
    echo.
    powershell -ExecutionPolicy Bypass -File "INICIAR_RAG_COMPLETO.ps1" -Setup
)

echo.
echo 📱 Proceso completado
pause