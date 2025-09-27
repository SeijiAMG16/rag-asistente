# 🚀 RAG ASISTENTE - INICIO AUTOMÁTICO
# Ejecuta todo el sistema RAG automáticamente

Write-Host "🚀 INICIANDO RAG ASISTENTE" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

# Cambiar al directorio backend
$backendDir = Join-Path $PSScriptRoot "."
Set-Location $backendDir

Write-Host "📁 Directorio: $backendDir" -ForegroundColor Blue

# Verificar si Python está instalado
try {
    $pythonVersion = python --version 2>$null
    Write-Host "🐍 Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no está instalado o no está en PATH" -ForegroundColor Red
    Write-Host "Por favor instala Python desde https://www.python.org/downloads/" -ForegroundColor Yellow
    pause
    exit 1
}

# Ejecutar script maestro de Python
Write-Host "`n🎯 Ejecutando script maestro..." -ForegroundColor Blue
Write-Host "=" * 50 -ForegroundColor Blue

try {
    python start_rag.py
} catch {
    Write-Host "❌ Error ejecutando el script maestro" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host "`n👋 Presiona cualquier tecla para cerrar..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")