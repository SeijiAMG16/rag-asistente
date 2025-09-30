# 📊 DIAGNÓSTICO RAG ASISTENTE
# ============================
# 
# Script para verificar el estado completo del sistema RAG
# Útil para troubleshooting y verificación post-instalación
#
# USO: .\DIAGNOSTICO_RAG.ps1

Write-Host ""
Write-Host "📊 DIAGNÓSTICO COMPLETO - RAG ASISTENTE" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""
Write-Host "📅 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host ""

# Variables
$BackendDir = Get-Location
$ProjectRoot = Split-Path $BackendDir -Parent
$FrontendDir = Join-Path $ProjectRoot "frontend-react"
$DataDir = Join-Path $BackendDir "data"

# Función de estado
function Test-Component {
    param(
        [string]$Name,
        [scriptblock]$Test,
        [string]$SuccessMessage = "Funcionando",
        [string]$FailureMessage = "No disponible"
    )
    
    try {
        $result = & $Test
        if ($result) {
            Write-Host "   ✅ $Name`: $SuccessMessage" -ForegroundColor Green
            return $true
        } else {
            Write-Host "   ❌ $Name`: $FailureMessage" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "   ❌ $Name`: Error - $_" -ForegroundColor Red
        return $false
    }
}

function Get-FileCount {
    param([string]$Path, [string]$Filter = "*")
    if (Test-Path $Path) {
        return (Get-ChildItem $Path -Filter $Filter -ErrorAction SilentlyContinue).Count
    }
    return 0
}

Write-Host "🔍 VERIFICANDO COMPONENTES DEL SISTEMA" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# 1. Entorno Python
Write-Host ""
Write-Host "🐍 ENTORNO PYTHON:" -ForegroundColor Yellow

Test-Component "Python" {
    $version = & python --version 2>&1
    if ($version -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        return ($major -ge 3 -and $minor -ge 8)
    }
    return $false
} "$(& python --version 2>&1)" "No encontrado o versión incorrecta"

Test-Component "pip" {
    $version = & python -m pip --version 2>&1
    return $version -match "pip"
} "$(& python -m pip --version 2>&1 | Select-String 'pip')" "No disponible"

# Verificar entorno virtual
$venvActive = $env:VIRTUAL_ENV -or $env:CONDA_DEFAULT_ENV
if ($venvActive) {
    Write-Host "   ✅ Entorno virtual: Activo ($env:VIRTUAL_ENV$env:CONDA_DEFAULT_ENV)" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ Entorno virtual: No activo (usando Python del sistema)" -ForegroundColor Yellow
}

# 2. Dependencias críticas
Write-Host ""
Write-Host "📦 DEPENDENCIAS CRÍTICAS:" -ForegroundColor Yellow

$criticalPackages = @(
    "django",
    "chromadb", 
    "sentence_transformers",
    "pdfplumber",
    "openai"
)

foreach ($package in $criticalPackages) {
    Test-Component $package {
        $result = & python -c "import $($package.Replace('-', '_')); print('OK')" 2>$null
        return $result -eq "OK"
    } "Instalado" "No instalado"
}

# 3. Dependencias Google Drive
Write-Host ""
Write-Host "🔄 GOOGLE DRIVE:" -ForegroundColor Yellow

$drivePackages = @(
    "googleapiclient",
    "google.oauth2", 
    "google_auth_oauthlib",
    "dotenv"
)

$driveAvailable = $true
foreach ($package in $drivePackages) {
    $available = Test-Component $package {
        $result = & python -c "import $($package.Replace('-', '_')); print('OK')" 2>$null
        return $result -eq "OK"
    } "Disponible" "No instalado"
    
    if (-not $available) { $driveAvailable = $false }
}

# 4. Archivos de configuración
Write-Host ""
Write-Host "⚙️ CONFIGURACIÓN:" -ForegroundColor Yellow

Test-Component "manage.py" { Test-Path "manage.py" } "Encontrado" "No encontrado"
Test-Component "requirements.txt" { Test-Path "requirements.txt" } "Encontrado" "No encontrado"
Test-Component "settings.py" { Test-Path "core\settings.py" } "Encontrado" "No encontrado"

# Variables de entorno
if (Test-Path ".env") {
    Write-Host "   ✅ .env: Encontrado" -ForegroundColor Green
    
    $envContent = Get-Content ".env" -ErrorAction SilentlyContinue
    
    # Verificar configuraciones clave
    $googleDriveEnabled = $envContent | Where-Object { $_ -match "GOOGLE_DRIVE_ENABLED.*true" }
    $driveFolder = $envContent | Where-Object { $_ -match "DRIVE_FOLDER_ID.*=" }
    $openRouterKey = $envContent | Where-Object { $_ -match "OPENROUTER_API_KEY.*=" }
    
    if ($googleDriveEnabled) {
        Write-Host "     ✅ Google Drive habilitado" -ForegroundColor Green
    } else {
        Write-Host "     ⚠️ Google Drive no habilitado" -ForegroundColor Yellow
    }
    
    if ($driveFolder) {
        Write-Host "     ✅ ID de carpeta Drive configurado" -ForegroundColor Green
    } else {
        Write-Host "     ⚠️ ID de carpeta Drive no configurado" -ForegroundColor Yellow
    }
    
    if ($openRouterKey) {
        Write-Host "     ✅ API Key OpenRouter configurada" -ForegroundColor Green
    } else {
        Write-Host "     ⚠️ API Key OpenRouter no configurada" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ .env: No encontrado" -ForegroundColor Red
}

# Google Drive credentials
if (Test-Path "credentials.json") {
    Write-Host "   ✅ credentials.json: Encontrado" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ credentials.json: No encontrado" -ForegroundColor Yellow
}

# 5. Estructura de datos
Write-Host ""
Write-Host "📁 ESTRUCTURA DE DATOS:" -ForegroundColor Yellow

$pdfCount = Get-FileCount (Join-Path $DataDir "pdfs") "*.pdf"
$txtCount = Get-FileCount (Join-Path $DataDir "texts") "*.txt"

Test-Component "Directorio data" { Test-Path $DataDir } "Existe" "No existe"
Test-Component "Directorio pdfs" { Test-Path (Join-Path $DataDir "pdfs") } "$pdfCount archivos PDF" "No existe"
Test-Component "Directorio texts" { Test-Path (Join-Path $DataDir "texts") } "$txtCount archivos TXT" "No existe"

# 6. Base de datos vectorial
Write-Host ""
Write-Host "🗄️ BASE DE DATOS VECTORIAL:" -ForegroundColor Yellow

$chromaDirs = @("chroma_db_simple", "chroma_db", "chroma_db_advanced")
$chromaFound = $false

foreach ($chromaDir in $chromaDirs) {
    if (Test-Path $chromaDir) {
        $chromaFound = $true
        Write-Host "   ✅ $chromaDir`: Encontrada" -ForegroundColor Green
        
        # Verificar contenido
        $hasData = Test-Path (Join-Path $chromaDir "chroma.sqlite3")
        if ($hasData) {
            Write-Host "     ✅ Contiene datos" -ForegroundColor Green
        } else {
            Write-Host "     ⚠️ Vacía o sin datos" -ForegroundColor Yellow
        }
    }
}

if (-not $chromaFound) {
    Write-Host "   ❌ No se encontraron bases de datos vectoriales" -ForegroundColor Red
}

# 7. Scripts de automatización
Write-Host ""
Write-Host "🔧 SCRIPTS DE AUTOMATIZACIÓN:" -ForegroundColor Yellow

$scripts = @(
    "INICIAR_RAG_COMPLETO.ps1",
    "ARRANCAR_RAG.ps1", 
    "EJECUTAR_ETL.ps1",
    "SINCRONIZAR_DRIVE.ps1",
    "SETUP_RAG_NUEVA_PC.ps1"
)

foreach ($script in $scripts) {
    Test-Component $script { Test-Path $script } "Disponible" "No encontrado"
}

# 8. Frontend React
Write-Host ""
Write-Host "🌐 FRONTEND REACT:" -ForegroundColor Yellow

Test-Component "Directorio frontend" { Test-Path $FrontendDir } "Encontrado" "No encontrado"

if (Test-Path $FrontendDir) {
    Test-Component "package.json" { Test-Path (Join-Path $FrontendDir "package.json") } "Encontrado" "No encontrado"
    Test-Component "node_modules" { Test-Path (Join-Path $FrontendDir "node_modules") } "Instaladas" "No instaladas"
    
    # Verificar Node.js
    try {
        $nodeVersion = & node --version 2>&1
        if ($nodeVersion -match "v\d+") {
            Write-Host "   ✅ Node.js: $nodeVersion" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Node.js: No disponible" -ForegroundColor Red
        }
    } catch {
        Write-Host "   ❌ Node.js: No disponible" -ForegroundColor Red
    }
}

# 9. Conectividad y puertos
Write-Host ""
Write-Host "🌐 CONECTIVIDAD:" -ForegroundColor Yellow

# Verificar puertos comunes
$ports = @(8000, 3000, 8080)
foreach ($port in $ports) {
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($connection) {
            Write-Host "   ⚠️ Puerto $port`: En uso" -ForegroundColor Yellow
        } else {
            Write-Host "   ✅ Puerto $port`: Disponible" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ✅ Puerto $port`: Disponible" -ForegroundColor Green
    }
}

# 10. Estado de Django
Write-Host ""
Write-Host "🎯 DJANGO:" -ForegroundColor Yellow

Test-Component "Migraciones" {
    $result = & python manage.py showmigrations --plan 2>$null
    return $LASTEXITCODE -eq 0
} "Aplicadas" "Pendientes o error"

Test-Component "Base de datos Django" {
    $result = & python -c "import django; django.setup(); from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1'); print('OK')" 2>$null
    return $result -eq "OK"
} "Funcionando" "Error o no configurada"

# 11. RESUMEN FINAL
Write-Host ""
Write-Host "📊 RESUMEN DEL DIAGNÓSTICO" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan

Write-Host ""
Write-Host "📋 ESTADO GENERAL:" -ForegroundColor White
Write-Host "   📄 PDFs: $pdfCount archivos" -ForegroundColor White
Write-Host "   📝 Textos: $txtCount archivos" -ForegroundColor White
Write-Host "   🗄️ Base vectorial: $(if ($chromaFound) { 'Configurada' } else { 'No configurada' })" -ForegroundColor $(if ($chromaFound) { 'Green' } else { 'Red' })
Write-Host "   🔄 Google Drive: $(if ($driveAvailable) { 'Disponible' } else { 'No disponible' })" -ForegroundColor $(if ($driveAvailable) { 'Green' } else { 'Yellow' })

Write-Host ""
Write-Host "💡 RECOMENDACIONES:" -ForegroundColor Cyan

if (-not $chromaFound) {
    Write-Host "   🔧 Ejecutar: .\INICIAR_RAG_COMPLETO.ps1 -Setup" -ForegroundColor Yellow
}

if (-not $driveAvailable) {
    Write-Host "   📦 Instalar Google Drive: .\INSTALAR_GOOGLE_DRIVE.ps1" -ForegroundColor Yellow
}

if ($pdfCount -eq 0) {
    Write-Host "   📄 Agregar PDFs a data/pdfs/ o configurar Google Drive" -ForegroundColor Yellow
}

if (-not (Test-Path ".env")) {
    Write-Host "   ⚙️ Crear archivo .env con configuración" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 PARA INICIAR EL SISTEMA:" -ForegroundColor Cyan
Write-Host "   Arranque completo: .\INICIAR_RAG_COMPLETO.ps1" -ForegroundColor White
Write-Host "   Arranque rápido: .\ARRANCAR_RAG.ps1" -ForegroundColor White
Write-Host "   Doble-click: INICIAR_RAG.bat" -ForegroundColor White

Write-Host ""
Write-Host "✅ Diagnóstico completado" -ForegroundColor Green
Write-Host ""