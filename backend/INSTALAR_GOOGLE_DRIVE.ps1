# 📦 INSTALAR DEPENDENCIAS GOOGLE DRIVE
# ====================================
# 
# Script para instalar todas las dependencias necesarias
# para la integración con Google Drive
#
# USO: .\INSTALAR_GOOGLE_DRIVE.ps1

Write-Host "📦 INSTALANDO DEPENDENCIAS GOOGLE DRIVE" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""

# Verificar que estamos en un entorno virtual
$venvActive = $env:VIRTUAL_ENV -or $env:CONDA_DEFAULT_ENV
if (-not $venvActive) {
    Write-Host "⚠️ No hay entorno virtual activo" -ForegroundColor Yellow
    Write-Host "Recomendado: Activar entorno virtual primero" -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "¿Continuar con instalación global? (s/n)"
    if ($response -notmatch '^[sySí]') {
        Write-Host "❌ Instalación cancelada" -ForegroundColor Red
        exit 1
    }
}

# Lista de dependencias necesarias
$packages = @(
    @{
        name = "google-api-python-client"
        description = "Cliente oficial de Google APIs"
        required = $true
    },
    @{
        name = "google-auth-httplib2"
        description = "Autenticación HTTP para Google APIs"
        required = $true
    },
    @{
        name = "google-auth-oauthlib"
        description = "OAuth 2.0 para Google APIs"
        required = $true
    },
    @{
        name = "python-dotenv"
        description = "Carga variables de entorno desde .env"
        required = $true
    },
    @{
        name = "pdfplumber"
        description = "Extracción de texto de PDFs (ya incluido)"
        required = $false
    },
    @{
        name = "chromadb"
        description = "Base de datos vectorial (ya incluido)"
        required = $false
    }
)

Write-Host "📋 Dependencias a instalar:" -ForegroundColor Cyan
foreach ($package in $packages) {
    $status = if ($package.required) { "[REQUERIDO]" } else { "[OPCIONAL]" }
    Write-Host "   📦 $($package.name) $status" -ForegroundColor White
    Write-Host "      $($package.description)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🚀 Iniciando instalación..." -ForegroundColor Yellow
Write-Host ""

$successCount = 0
$errorCount = 0
$skippedCount = 0

foreach ($package in $packages) {
    Write-Host "📦 Instalando: $($package.name)" -ForegroundColor Cyan
    
    try {
        # Verificar si ya está instalado
        $checkResult = & python -c "import $($package.name.Replace('-', '_')); print('OK')" 2>$null
        
        if ($checkResult -eq "OK") {
            Write-Host "   ✅ Ya está instalado" -ForegroundColor Green
            $skippedCount++
        }
        else {
            # Instalar paquete
            & python -m pip install $package.name --quiet --upgrade
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✅ Instalado exitosamente" -ForegroundColor Green
                $successCount++
            }
            else {
                throw "Error en pip install"
            }
        }
    }
    catch {
        Write-Host "   ❌ Error: $_" -ForegroundColor Red
        
        if ($package.required) {
            $errorCount++
        }
        else {
            Write-Host "   ⚠️ Paquete opcional - continuando..." -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
}

# Resumen de instalación
Write-Host "📊 RESUMEN DE INSTALACIÓN" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host "✅ Instalados: $successCount" -ForegroundColor Green
Write-Host "⏭️ Ya existían: $skippedCount" -ForegroundColor Yellow
Write-Host "❌ Errores: $errorCount" -ForegroundColor Red
Write-Host ""

if ($errorCount -eq 0) {
    Write-Host "🎉 TODAS LAS DEPENDENCIAS INSTALADAS CORRECTAMENTE" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔧 PRÓXIMOS PASOS:" -ForegroundColor Cyan
    Write-Host "1. Configurar Google Drive:" -ForegroundColor White
    Write-Host "   .\SINCRONIZAR_DRIVE.ps1 -Setup" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "2. O configurar todo el sistema:" -ForegroundColor White
    Write-Host "   .\SETUP_RAG_NUEVA_PC.ps1" -ForegroundColor Yellow
    Write-Host ""
    
    # Verificar configuración existente
    if (Test-Path "credentials.json") {
        Write-Host "✅ credentials.json encontrado" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️ credentials.json no encontrado" -ForegroundColor Yellow
        Write-Host "   Necesitarás crear cuenta de servicio de Google" -ForegroundColor Gray
    }
    
    if (Test-Path ".env") {
        $envContent = Get-Content ".env" -ErrorAction SilentlyContinue
        $hasGoogleDrive = $envContent | Where-Object { $_ -match "GOOGLE_DRIVE_ENABLED.*true" }
        
        if ($hasGoogleDrive) {
            Write-Host "✅ Google Drive ya configurado en .env" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️ Google Drive no configurado en .env" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "⚠️ Archivo .env no encontrado" -ForegroundColor Yellow
    }
    
}
else {
    Write-Host "❌ ERRORES EN INSTALACIÓN" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 POSIBLES SOLUCIONES:" -ForegroundColor Cyan
    Write-Host "1. Verificar conexión a internet" -ForegroundColor White
    Write-Host "2. Actualizar pip:" -ForegroundColor White
    Write-Host "   python -m pip install --upgrade pip" -ForegroundColor Yellow
    Write-Host "3. Usar entorno virtual:" -ForegroundColor White
    Write-Host "   python -m venv .venv" -ForegroundColor Yellow
    Write-Host "   .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "4. Instalar manualmente:" -ForegroundColor White
    Write-Host "   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv" -ForegroundColor Yellow
    Write-Host ""
}

# Test final de importación
Write-Host "🧪 VERIFICANDO INSTALACIÓN..." -ForegroundColor Cyan

$testPackages = @(
    "googleapiclient.discovery",
    "google.oauth2.service_account", 
    "google_auth_oauthlib",
    "dotenv"
)

$testSuccess = $true
foreach ($testPkg in $testPackages) {
    try {
        $testResult = & python -c "import $testPkg; print('✅ $testPkg')" 2>$null
        if ($testResult) {
            Write-Host $testResult -ForegroundColor Green
        }
        else {
            Write-Host "❌ $testPkg" -ForegroundColor Red
            $testSuccess = $false
        }
    }
    catch {
        Write-Host "❌ $testPkg - Error: $_" -ForegroundColor Red
        $testSuccess = $false
    }
}

Write-Host ""

if ($testSuccess) {
    Write-Host "🎉 VERIFICACIÓN EXITOSA - GOOGLE DRIVE LISTO" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "❌ VERIFICACIÓN FALLÓ - REVISAR ERRORES" -ForegroundColor Red
    exit 1
}