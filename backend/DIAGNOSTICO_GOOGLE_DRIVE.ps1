# 🔍 DIAGNÓSTICO COMPLETO GOOGLE DRIVE - RAG ASISTENTE
# ====================================================
# 
# Script para diagnosticar y solucionar problemas con Google Drive

param(
    [switch]$Fix,           # Intentar arreglar problemas automáticamente
    [switch]$Setup,         # Configurar desde cero
    [switch]$TestDownload,  # Probar descarga de un archivo
    [switch]$Verbose       # Mostrar información detallada
)

Write-Host "🔍 DIAGNÓSTICO GOOGLE DRIVE - RAG ASISTENTE" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""

$global:issuesFound = @()
$global:criticalIssues = 0

# Función para reportar problemas
function Report-Issue {
    param(
        [string]$Type,      # "CRITICAL", "WARNING", "INFO"
        [string]$Message,
        [string]$Solution = ""
    )
    
    $color = switch ($Type) {
        "CRITICAL" { 
            $global:criticalIssues++
            "Red" 
        }
        "WARNING" { "Yellow" }
        "INFO" { "Cyan" }
        default { "White" }
    }
    
    Write-Host "   [$Type] $Message" -ForegroundColor $color
    
    if ($Solution) {
        Write-Host "     💡 Solución: $Solution" -ForegroundColor Gray
    }
    
    $global:issuesFound += @{
        Type = $Type
        Message = $Message
        Solution = $Solution
    }
}

# Función para verificar Python y dependencias
function Test-PythonSetup {
    Write-Host "🐍 Verificando Python y dependencias..." -ForegroundColor Cyan
    Write-Host ""
    
    # Verificar Python
    try {
        $pythonVersion = & python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $majorVersion = [int]$matches[1]
            $minorVersion = [int]$matches[2]
            
            if ($majorVersion -ge 3 -and $minorVersion -ge 8) {
                Write-Host "   ✅ Python $pythonVersion" -ForegroundColor Green
            } else {
                Report-Issue -Type "CRITICAL" -Message "Python $pythonVersion es muy antiguo (requiere 3.8+)" -Solution "Actualizar Python a 3.8 o superior"
            }
        }
    }
    catch {
        Report-Issue -Type "CRITICAL" -Message "Python no encontrado en PATH" -Solution "Instalar Python 3.8+ y agregarlo al PATH"
        return $false
    }
    
    # Verificar dependencias de Google Drive
    $googleDeps = @(
        "google-api-python-client",
        "google-auth-httplib2", 
        "google-auth-oauthlib",
        "python-dotenv"
    )
    
    Write-Host "   📦 Verificando dependencias de Google Drive:" -ForegroundColor Gray
    
    foreach ($dep in $googleDeps) {
        $depName = $dep.replace('-', '_')
        try {
            $result = & python -c "import $depName; print('OK')" 2>&1
            if ($result -eq "OK") {
                Write-Host "      ✅ $dep" -ForegroundColor Green
            } else {
                Report-Issue -Type "WARNING" -Message "$dep no instalado" -Solution "pip install $dep"
            }
        }
        catch {
            Report-Issue -Type "WARNING" -Message "$dep no instalado o corrupto" -Solution "pip install --upgrade $dep"
        }
    }
    
    return $true
}

# EJECUCIÓN PRINCIPAL
if ($Setup) {
    Write-Host "🚀 Configuración inicial no implementada aún" -ForegroundColor Yellow
    Write-Host "Por ahora usa el test básico:" -ForegroundColor Gray
    Write-Host "python test_drive_download.py" -ForegroundColor Gray
    exit
}

Write-Host "🔍 Ejecutando diagnóstico..." -ForegroundColor Yellow
Write-Host ""

# Ejecutar verificaciones básicas
$pythonOk = Test-PythonSetup

# Verificar archivos de configuración
Write-Host ""
Write-Host "📁 Verificando archivos de configuración..." -ForegroundColor Cyan

if (Test-Path ".env") {
    Write-Host "   ✅ .env encontrado" -ForegroundColor Green
} else {
    Report-Issue -Type "CRITICAL" -Message ".env no encontrado" -Solution "Crear archivo .env"
}

if (Test-Path "credentials.json") {
    Write-Host "   ✅ credentials.json encontrado" -ForegroundColor Green
} else {
    Report-Issue -Type "CRITICAL" -Message "credentials.json no encontrado" -Solution "Descargar desde Google Cloud Console"
}

# Crear directorios necesarios
$dataDir = "data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    Write-Host "   📁 Directorio data creado" -ForegroundColor Yellow
}

$subDirs = @("pdfs", "texts", "downloads")
foreach ($subDir in $subDirs) {
    $fullPath = Join-Path $dataDir $subDir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "   📁 Directorio $fullPath creado" -ForegroundColor Yellow
    } else {
        Write-Host "   ✅ Directorio $fullPath existe" -ForegroundColor Green
    }
}

# Probar descarga si se solicita
if ($TestDownload) {
    Write-Host ""
    Write-Host "🧪 Ejecutando prueba de descarga..." -ForegroundColor Cyan
    & python test_drive_download.py
}

# Mostrar resumen
Write-Host ""
Write-Host "📊 RESUMEN DEL DIAGNÓSTICO" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan

if ($global:criticalIssues -eq 0) {
    Write-Host "✅ No se encontraron problemas críticos" -ForegroundColor Green
} else {
    Write-Host "❌ $($global:criticalIssues) problema(s) crítico(s)" -ForegroundColor Red
}

# Mostrar opciones
Write-Host ""
Write-Host "🔧 OPCIONES DISPONIBLES:" -ForegroundColor Cyan
Write-Host "   .\DIAGNOSTICO_GOOGLE_DRIVE.ps1 -TestDownload  # Probar descarga" -ForegroundColor Gray
Write-Host "   python test_drive_download.py                # Prueba básica Python" -ForegroundColor Gray
Write-Host "   .\SINCRONIZAR_DRIVE.ps1                      # Sincronización completa" -ForegroundColor Gray

Write-Host ""