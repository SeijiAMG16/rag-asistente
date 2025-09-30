# =============================================================================
# SINCRONIZACIÓN GOOGLE DRIVE - RAG ASISTENTE
# =============================================================================

param(
    [switch]$Force,
    [switch]$SkipETL,
    [switch]$DiagnosticsOnly
)

Write-Host ""
Write-Host "🔄 SINCRONIZACIÓN GOOGLE DRIVE - RAG ASISTENTE" -ForegroundColor Magenta
Write-Host ("=" * 55) -ForegroundColor Magenta
Write-Host ""

# Verificar Python
Write-Host "🐍 Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = & python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Python no encontrado" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error verificando Python: $_" -ForegroundColor Red
    exit 1
}

# Instalar dependencias
Write-Host "📦 Instalando dependencias..." -ForegroundColor Yellow
$packages = @("google-api-python-client", "google-auth-httplib2", "google-auth-oauthlib", "python-dotenv")

foreach ($package in $packages) {
    Write-Host "   📦 Instalando: $package" -ForegroundColor Cyan
    try {
        & python -m pip install $package --quiet
        Write-Host "   ✅ $package instalado" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Error instalando $package" -ForegroundColor Red
    }
}

# Verificar configuración
Write-Host "🔍 Verificando configuración..." -ForegroundColor Yellow
$configOK = $true

if (Test-Path "credentials.json") {
    Write-Host "✅ credentials.json encontrado" -ForegroundColor Green
} else {
    Write-Host "❌ credentials.json no encontrado" -ForegroundColor Red
    $configOK = $false
}

if (Test-Path ".env") {
    Write-Host "✅ .env encontrado" -ForegroundColor Green
} else {
    Write-Host "❌ .env no encontrado" -ForegroundColor Red
    $configOK = $false
}

if (-not $configOK) {
    Write-Host "❌ Configuración incompleta" -ForegroundColor Red
    exit 1
}

# Ejecutar sincronización
Write-Host ""
Write-Host "🚀 Iniciando sincronización..." -ForegroundColor Magenta

if ($DiagnosticsOnly) {
    Write-Host "🔍 Ejecutando diagnósticos..." -ForegroundColor Yellow
    & python "verificar_drive.py"
} else {
    Write-Host "📥 Ejecutando sincronización completa..." -ForegroundColor Yellow
    & python "run_sync.py"
    
    if ($LASTEXITCODE -eq 0 -and -not $SkipETL) {
        Write-Host ""
        Write-Host "🧠 Procesando documentos con ETL..." -ForegroundColor Yellow
        & python "ingest_documents.py"
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 ¡Proceso completado exitosamente!" -ForegroundColor Green
    Write-Host "🚀 El sistema RAG está listo para usar" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Proceso completado con errores" -ForegroundColor Red
}