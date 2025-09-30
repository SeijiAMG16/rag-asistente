# 🚀 RAG ASISTENTE - INICIO COMPLETO UNIFICADO
# ============================================
# 
# Script maestro que ejecuta TODO en un solo comando:
# - Verificación del entorno
# - Configuración de Google Drive (si es necesario)
# - Sincronización de PDFs desde Drive
# - Proceso ETL completo
# - Arranque del servidor backend
# - Apertura del frontend (opcional)
#
# USO:
#   .\INICIAR_RAG_COMPLETO.ps1                    # Inicio normal
#   .\INICIAR_RAG_COMPLETO.ps1 -Setup             # Primera vez / reconfigurar
#   .\INICIAR_RAG_COMPLETO.ps1 -Force             # Forzar ETL completo
#   .\INICIAR_RAG_COMPLETO.ps1 -SkipDrive         # Sin Google Drive
#   .\INICIAR_RAG_COMPLETO.ps1 -NoFrontend        # Solo backend

param(
    [switch]$Setup,             # Ejecutar configuración inicial completa
    [switch]$Force,             # Forzar ETL completo y re-descarga
    [switch]$SkipDrive,         # Omitir sincronización de Google Drive
    [switch]$NoFrontend,        # No abrir frontend automáticamente
    [switch]$NoInteractive,     # Modo no interactivo
    [int]$Port = 8000,          # Puerto para el backend
    [int]$FrontendPort = 3000   # Puerto para el frontend
)

# Configuración de colores y estilo
$Host.UI.RawUI.WindowTitle = "RAG Asistente - Inicio Completo"

Write-Host ""
Write-Host "🚀 RAG ASISTENTE - INICIO COMPLETO UNIFICADO" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "📅 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host ""

# Variables globales
$script:ProjectRoot = Split-Path (Get-Location) -Parent
$script:BackendDir = Get-Location
$script:FrontendDir = Join-Path $ProjectRoot "frontend-react"
$script:DataDir = Join-Path $BackendDir "data"
$script:LogFile = Join-Path $BackendDir "rag_startup.log"

# Funciones auxiliares
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $script:LogFile -Value $logEntry -ErrorAction SilentlyContinue
}

function Write-Step {
    param([int]$Step, [string]$Title, [string]$Description = "")
    Write-Host ""
    Write-Host "📋 PASO $Step`: $Title" -ForegroundColor Cyan
    Write-Host "$(('=' * 50))" -ForegroundColor Cyan
    if ($Description) {
        Write-Host "$Description" -ForegroundColor Yellow
    }
    Write-Host ""
}

function Test-Prerequisites {
    Write-Step 1 "VERIFICANDO REQUISITOS PREVIOS"
    
    $allGood = $true
    
    # Verificar Python
    try {
        $pythonVersion = & python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -ge 3 -and $minor -ge 8) {
                Write-Log "✅ Python $pythonVersion" "SUCCESS"
            } else {
                Write-Log "❌ Python $pythonVersion - Se requiere Python 3.8+" "ERROR"
                $allGood = $false
            }
        }
    } catch {
        Write-Log "❌ Python no encontrado en PATH" "ERROR"
        $allGood = $false
    }
    
    # Verificar pip
    try {
        $pipVersion = & python -m pip --version 2>&1
        if ($pipVersion -match "pip") {
            Write-Log "✅ pip disponible" "SUCCESS"
        }
    } catch {
        Write-Log "❌ pip no disponible" "ERROR"
        $allGood = $false
    }
    
    # Verificar Node.js (para frontend)
    if (-not $NoFrontend) {
        try {
            $nodeVersion = & node --version 2>&1
            if ($nodeVersion -match "v(\d+)") {
                Write-Log "✅ Node.js $nodeVersion" "SUCCESS"
            }
        } catch {
            Write-Log "⚠️ Node.js no encontrado - Frontend no disponible" "WARNING"
        }
    }
    
    # Verificar estructura de directorios
    $requiredDirs = @("api", "core", "utils", "data")
    foreach ($dir in $requiredDirs) {
        if (Test-Path $dir) {
            Write-Log "✅ Directorio $dir" "SUCCESS"
        } else {
            Write-Log "❌ Directorio $dir no encontrado" "ERROR"
            $allGood = $false
        }
    }
    
    # Verificar archivos clave
    $requiredFiles = @("manage.py", "requirements.txt")
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-Log "✅ Archivo $file" "SUCCESS"
        } else {
            Write-Log "❌ Archivo $file no encontrado" "ERROR"
            $allGood = $false
        }
    }
    
    if (-not $allGood) {
        Write-Log "❌ Verificación de requisitos falló" "ERROR"
        Write-Host ""
        Write-Host "🔧 ACCIONES REQUERIDAS:" -ForegroundColor Red
        Write-Host "   1. Asegúrate de estar en el directorio backend/" -ForegroundColor Yellow
        Write-Host "   2. Instala Python 3.8+ si no está disponible" -ForegroundColor Yellow
        Write-Host "   3. Ejecuta desde la raíz del proyecto RAG" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Log "✅ Todos los requisitos verificados" "SUCCESS"
    return $true
}

function Initialize-Environment {
    Write-Step 2 "CONFIGURANDO ENTORNO"
    
    # Buscar y activar entorno virtual
    $venvPaths = @(
        ".venv\Scripts\Activate.ps1",
        "venv\Scripts\Activate.ps1",
        "$script:ProjectRoot\.venv\Scripts\Activate.ps1",
        "$script:ProjectRoot\venv\Scripts\Activate.ps1"
    )
    
    $venvActivated = $false
    foreach ($venvPath in $venvPaths) {
        if (Test-Path $venvPath) {
            Write-Log "🔧 Activando entorno virtual: $venvPath" "INFO"
            try {
                & $venvPath
                Write-Log "✅ Entorno virtual activado" "SUCCESS"
                $venvActivated = $true
                break
            } catch {
                Write-Log "⚠️ Error activando entorno virtual: $_" "WARNING"
            }
        }
    }
    
    if (-not $venvActivated) {
        Write-Log "⚠️ Entorno virtual no encontrado, usando Python del sistema" "WARNING"
    }
    
    # Verificar e instalar dependencias básicas
    Write-Log "📦 Verificando dependencias básicas..." "INFO"
    
    $basicPackages = @("django", "chromadb", "sentence-transformers", "pdfplumber")
    $missingPackages = @()
    
    foreach ($package in $basicPackages) {
        try {
            $checkCmd = "import $($package.Replace('-', '_')); print('OK')"
            $result = & python -c $checkCmd 2>$null
            if ($result -eq "OK") {
                Write-Log "✅ $package disponible" "SUCCESS"
            } else {
                $missingPackages += $package
            }
        } catch {
            $missingPackages += $package
        }
    }
    
    if ($missingPackages.Count -gt 0) {
        Write-Log "📦 Instalando dependencias faltantes: $($missingPackages -join ', ')" "INFO"
        & python -m pip install -r requirements.txt --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Log "⚠️ Error instalando dependencias básicas" "WARNING"
        }
    }
    
    # Crear directorios necesarios
    $requiredDirs = @(
        $script:DataDir,
        (Join-Path $script:DataDir "pdfs"),
        (Join-Path $script:DataDir "texts"),
        (Join-Path $script:DataDir "downloads")
    )
    
    foreach ($dir in $requiredDirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Log "📁 Directorio creado: $dir" "INFO"
        }
    }
    
    Write-Log "✅ Entorno configurado correctamente" "SUCCESS"
}

function Setup-GoogleDrive {
    Write-Step 3 "CONFIGURACIÓN DE GOOGLE DRIVE" "Configuración automática de sincronización"
    
    if ($SkipDrive) {
        Write-Log "⏭️ Google Drive omitido por parámetro -SkipDrive" "INFO"
        return $true
    }
    
    # Verificar si Google Drive ya está configurado
    $driveConfigured = $false
    if ((Test-Path "credentials.json") -and (Test-Path ".env")) {
        $envContent = Get-Content ".env" -ErrorAction SilentlyContinue
        $hasGoogleDrive = $envContent | Where-Object { $_ -match "GOOGLE_DRIVE_ENABLED.*true" }
        if ($hasGoogleDrive) {
            $driveConfigured = $true
            Write-Log "✅ Google Drive ya está configurado" "SUCCESS"
        }
    }
    
    if (-not $driveConfigured -or $Setup) {
        # Instalar dependencias de Google Drive
        Write-Log "📦 Instalando dependencias de Google Drive..." "INFO"
        
        if (Test-Path "INSTALAR_GOOGLE_DRIVE.ps1") {
            try {
                & .\INSTALAR_GOOGLE_DRIVE.ps1
                if ($LASTEXITCODE -eq 0) {
                    Write-Log "✅ Dependencias de Google Drive instaladas" "SUCCESS"
                } else {
                    Write-Log "⚠️ Error instalando dependencias de Google Drive" "WARNING"
                }
            } catch {
                Write-Log "⚠️ Error ejecutando instalador de Google Drive: $_" "WARNING"
            }
        } else {
            # Instalación manual de dependencias
            $drivePackages = @("google-api-python-client", "google-auth-httplib2", "google-auth-oauthlib", "python-dotenv")
            foreach ($pkg in $drivePackages) {
                & python -m pip install $pkg --quiet
            }
        }
        
        # Configurar Google Drive
        Write-Log "🔧 Configurando Google Drive..." "INFO"
        
        if ($NoInteractive) {
            Write-Log "⚠️ Modo no interactivo: configuración de Google Drive saltada" "WARNING"
        } else {
            if (Test-Path "SINCRONIZAR_DRIVE.ps1") {
                try {
                    & .\SINCRONIZAR_DRIVE.ps1 -Setup
                    if ($LASTEXITCODE -eq 0) {
                        Write-Log "✅ Google Drive configurado exitosamente" "SUCCESS"
                        $driveConfigured = $true
                    }
                } catch {
                    Write-Log "⚠️ Error configurando Google Drive: $_" "WARNING"
                }
            } else {
                Write-Log "⚠️ Script de Google Drive no encontrado" "WARNING"
            }
        }
    }
    
    return $driveConfigured
}

function Sync-DriveFiles {
    param([bool]$DriveConfigured)
    
    Write-Step 4 "SINCRONIZACIÓN CON GOOGLE DRIVE" "Descargando PDFs desde Drive"
    
    if ($SkipDrive -or -not $DriveConfigured) {
        Write-Log "⏭️ Sincronización de Google Drive omitida" "INFO"
        return $true
    }
    
    Write-Log "🔄 Iniciando sincronización con Google Drive..." "INFO"
    
    try {
        if (Test-Path "SINCRONIZAR_DRIVE.ps1") {
            if ($Force) {
                & .\SINCRONIZAR_DRIVE.ps1 -Force
            } else {
                & .\SINCRONIZAR_DRIVE.ps1
            }
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "✅ Sincronización con Google Drive completada" "SUCCESS"
                
                # Mostrar estadísticas
                $pdfCount = 0
                $pdfDir = Join-Path $script:DataDir "pdfs"
                if (Test-Path $pdfDir) {
                    $pdfCount = (Get-ChildItem $pdfDir -Filter "*.pdf" -ErrorAction SilentlyContinue).Count
                }
                Write-Log "📊 PDFs sincronizados: $pdfCount" "INFO"
                
                return $true
            } else {
                Write-Log "⚠️ Error en sincronización con Google Drive" "WARNING"
                return $false
            }
        } else {
            # Fallback a comando Django
            Write-Log "🔄 Usando comando Django para sincronización..." "INFO"
            & python manage.py sync_drive_full $(if ($Force) { "--force" })
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "✅ Sincronización Django completada" "SUCCESS"
                return $true
            } else {
                Write-Log "⚠️ Error en sincronización Django" "WARNING"
                return $false
            }
        }
    } catch {
        Write-Log "❌ Error ejecutando sincronización: $_" "ERROR"
        return $false
    }
}

function Execute-ETL {
    Write-Step 5 "PROCESO ETL COMPLETO" "Extracción, transformación y carga de documentos"
    
    Write-Log "🔄 Iniciando proceso ETL..." "INFO"
    
    # Verificar si hay PDFs para procesar
    $pdfDir = Join-Path $script:DataDir "pdfs"
    $pdfCount = 0
    if (Test-Path $pdfDir) {
        $pdfCount = (Get-ChildItem $pdfDir -Filter "*.pdf" -ErrorAction SilentlyContinue).Count
    }
    
    if ($pdfCount -eq 0 -and -not $Force) {
        Write-Log "⚠️ No se encontraron PDFs para procesar" "WARNING"
        Write-Log "💡 Usa -Force para procesar documentos existentes" "INFO"
        return $true
    }
    
    Write-Log "📊 PDFs a procesar: $pdfCount" "INFO"
    
    # Intentar ETL completo primero
    $etlSuccess = $false
    
    if (Test-Path "EJECUTAR_ETL.ps1") {
        Write-Log "🚀 Ejecutando ETL completo..." "INFO"
        try {
            if ($Force) {
                & .\EJECUTAR_ETL.ps1 -Force
            } else {
                & .\EJECUTAR_ETL.ps1
            }
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "✅ ETL completo ejecutado exitosamente" "SUCCESS"
                $etlSuccess = $true
            } else {
                Write-Log "⚠️ ETL completo falló, intentando alternativas..." "WARNING"
            }
        } catch {
            Write-Log "⚠️ Error ejecutando ETL completo: $_" "WARNING"
        }
    }
    
    # Fallback a ETL directo
    if (-not $etlSuccess -and (Test-Path "etl_rag_complete.py")) {
        Write-Log "🔄 Ejecutando ETL directo..." "INFO"
        try {
            if ($Force) {
                & python etl_rag_complete.py --force
            } else {
                & python etl_rag_complete.py
            }
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "✅ ETL directo completado" "SUCCESS"
                $etlSuccess = $true
            }
        } catch {
            Write-Log "⚠️ Error en ETL directo: $_" "WARNING"
        }
    }
    
    # Fallback a inicialización básica
    if (-not $etlSuccess) {
        Write-Log "🔄 Intentando inicialización básica..." "INFO"
        try {
            & python initialize_rag_system.py
            if ($LASTEXITCODE -eq 0) {
                Write-Log "✅ Inicialización básica completada" "SUCCESS"
                $etlSuccess = $true
            }
        } catch {
            Write-Log "⚠️ Error en inicialización básica: $_" "WARNING"
        }
    }
    
    if ($etlSuccess) {
        # Verificar resultado
        $chromaDir = "chroma_db_simple"
        if (Test-Path $chromaDir) {
            Write-Log "✅ Base de datos vectorial creada/actualizada" "SUCCESS"
        }
        
        $txtDir = Join-Path $script:DataDir "texts"
        if (Test-Path $txtDir) {
            $txtCount = (Get-ChildItem $txtDir -Filter "*.txt" -ErrorAction SilentlyContinue).Count
            Write-Log "📊 Textos procesados: $txtCount" "INFO"
        }
        
        return $true
    } else {
        Write-Log "❌ Todos los métodos de ETL fallaron" "ERROR"
        return $false
    }
}

function Start-Backend {
    Write-Step 6 "INICIANDO SERVIDOR BACKEND" "Django server en puerto $Port"
    
    Write-Log "🔧 Preparando servidor Django..." "INFO"
    
    # Aplicar migraciones
    Write-Log "📦 Aplicando migraciones..." "INFO"
    & python manage.py migrate --run-syncdb 2>$null
    
    # Crear superusuario si no existe (modo no interactivo)
    Write-Log "👤 Verificando superusuario..." "INFO"
    $superuserExists = & python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.filter(is_superuser=True).exists())" 2>$null
    
    if ($superuserExists -eq "False") {
        Write-Log "👤 Creando superusuario por defecto..." "INFO"
        $env:DJANGO_SUPERUSER_USERNAME = "admin"
        $env:DJANGO_SUPERUSER_EMAIL = "admin@ragasistente.com"
        $env:DJANGO_SUPERUSER_PASSWORD = "admin123"
        & python manage.py createsuperuser --noinput 2>$null
    }
    
    # Verificar estado de la base de datos
    Write-Log "🗄️ Verificando base de datos..." "INFO"
    try {
        $dbCheck = & python -c "import django; django.setup(); from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1'); print('OK')" 2>$null
        if ($dbCheck -eq "OK") {
            Write-Log "✅ Base de datos Django funcionando" "SUCCESS"
        }
    } catch {
        Write-Log "⚠️ Advertencia en verificación de base de datos" "WARNING"
    }
    
    # Iniciar servidor
    Write-Log "🚀 Iniciando servidor Django en puerto $Port..." "INFO"
    Write-Host ""
    Write-Host "🌐 SERVIDOR BACKEND INICIANDO..." -ForegroundColor Green
    Write-Host "   URL: http://localhost:$Port" -ForegroundColor Cyan
    Write-Host "   Admin: http://localhost:$Port/admin" -ForegroundColor Cyan
    Write-Host "   Usuario: admin / admin123" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📊 PARA MONITOREAR:" -ForegroundColor Cyan
    Write-Host "   Logs: tail -f rag_startup.log" -ForegroundColor White
    Write-Host "   Status: Ctrl+C para detener" -ForegroundColor White
    Write-Host ""
    
    # Iniciar en background si se solicita frontend
    if (-not $NoFrontend) {
        Write-Log "🔄 Iniciando servidor en background para frontend..." "INFO"
        Start-Process python -ArgumentList "manage.py", "runserver", "0.0.0.0:$Port" -WindowStyle Hidden
        Start-Sleep 3
        
        # Verificar que el servidor esté funcionando
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$Port/api/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Log "✅ Servidor backend funcionando correctamente" "SUCCESS"
                return $true
            }
        } catch {
            Write-Log "⚠️ Advertencia: servidor backend puede no estar respondiendo" "WARNING"
        }
        
        return $true
    } else {
        # Iniciar en foreground
        try {
            & python manage.py runserver "0.0.0.0:$Port"
        } catch {
            Write-Log "❌ Error iniciando servidor: $_" "ERROR"
            return $false
        }
    }
}

function Start-Frontend {
    Write-Step 7 "INICIANDO FRONTEND REACT" "React development server en puerto $FrontendPort"
    
    if ($NoFrontend) {
        Write-Log "⏭️ Frontend omitido por parámetro -NoFrontend" "INFO"
        return $true
    }
    
    if (-not (Test-Path $script:FrontendDir)) {
        Write-Log "⚠️ Directorio frontend no encontrado: $script:FrontendDir" "WARNING"
        return $false
    }
    
    Write-Log "📁 Cambiando a directorio frontend..." "INFO"
    Push-Location $script:FrontendDir
    
    try {
        # Verificar Node.js
        $nodeVersion = & node --version 2>&1
        if (-not ($nodeVersion -match "v\d+")) {
            Write-Log "❌ Node.js no disponible" "ERROR"
            return $false
        }
        
        Write-Log "✅ Node.js $nodeVersion disponible" "SUCCESS"
        
        # Verificar package.json
        if (-not (Test-Path "package.json")) {
            Write-Log "❌ package.json no encontrado" "ERROR"
            return $false
        }
        
        # Instalar dependencias si node_modules no existe
        if (-not (Test-Path "node_modules")) {
            Write-Log "📦 Instalando dependencias de Node.js..." "INFO"
            & npm install
            if ($LASTEXITCODE -ne 0) {
                Write-Log "❌ Error instalando dependencias de Node" "ERROR"
                return $false
            }
        }
        
        Write-Log "🚀 Iniciando servidor React..." "INFO"
        Write-Host ""
        Write-Host "🌐 FRONTEND REACT INICIANDO..." -ForegroundColor Green
        Write-Host "   URL: http://localhost:$FrontendPort" -ForegroundColor Cyan
        Write-Host "   Backend API: http://localhost:$Port" -ForegroundColor Cyan
        Write-Host ""
        
        # Configurar puerto del frontend si es diferente del default
        if ($FrontendPort -ne 3000) {
            $env:PORT = $FrontendPort
        }
        
        # Iniciar React
        & npm start
        
    } catch {
        Write-Log "❌ Error iniciando frontend: $_" "ERROR"
        return $false
    } finally {
        Pop-Location
    }
}

function Show-Summary {
    Write-Host ""
    Write-Host "🎉 RAG ASISTENTE - INICIO COMPLETADO" -ForegroundColor Green
    Write-Host "====================================" -ForegroundColor Green
    Write-Host ""
    
    # URLs de acceso
    Write-Host "🌐 URLS DE ACCESO:" -ForegroundColor Cyan
    Write-Host "   Backend API: http://localhost:$Port" -ForegroundColor White
    Write-Host "   Admin Django: http://localhost:$Port/admin" -ForegroundColor White
    if (-not $NoFrontend) {
        Write-Host "   Frontend React: http://localhost:$FrontendPort" -ForegroundColor White
    }
    Write-Host ""
    
    # Credenciales
    Write-Host "🔑 CREDENCIALES POR DEFECTO:" -ForegroundColor Cyan
    Write-Host "   Usuario: admin" -ForegroundColor White
    Write-Host "   Contraseña: admin123" -ForegroundColor White
    Write-Host ""
    
    # Estadísticas
    Write-Host "📊 ESTADO DEL SISTEMA:" -ForegroundColor Cyan
    
    # Contar archivos
    $pdfDir = Join-Path $script:DataDir "pdfs"
    $txtDir = Join-Path $script:DataDir "texts"
    $pdfCount = 0
    $txtCount = 0
    
    if (Test-Path $pdfDir) {
        $pdfCount = (Get-ChildItem $pdfDir -Filter "*.pdf" -ErrorAction SilentlyContinue).Count
    }
    if (Test-Path $txtDir) {
        $txtCount = (Get-ChildItem $txtDir -Filter "*.txt" -ErrorAction SilentlyContinue).Count
    }
    
    Write-Host "   📄 PDFs procesados: $pdfCount" -ForegroundColor White
    Write-Host "   📝 Textos extraídos: $txtCount" -ForegroundColor White
    
    # Base de datos vectorial
    if (Test-Path "chroma_db_simple") {
        Write-Host "   🗄️ Base vectorial: ✅ Activa" -ForegroundColor Green
    } else {
        Write-Host "   🗄️ Base vectorial: ❌ No encontrada" -ForegroundColor Red
    }
    
    # Google Drive
    if (Test-Path ".env") {
        $envContent = Get-Content ".env" -ErrorAction SilentlyContinue
        $hasGoogleDrive = $envContent | Where-Object { $_ -match "GOOGLE_DRIVE_ENABLED.*true" }
        if ($hasGoogleDrive) {
            Write-Host "   🔄 Google Drive: ✅ Configurado" -ForegroundColor Green
        } else {
            Write-Host "   🔄 Google Drive: ❌ No configurado" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "💡 COMANDOS ÚTILES:" -ForegroundColor Cyan
    Write-Host "   Reconfigurar: .\INICIAR_RAG_COMPLETO.ps1 -Setup" -ForegroundColor White
    Write-Host "   ETL forzado: .\INICIAR_RAG_COMPLETO.ps1 -Force" -ForegroundColor White
    Write-Host "   Solo backend: .\INICIAR_RAG_COMPLETO.ps1 -NoFrontend" -ForegroundColor White
    Write-Host "   Sin Drive: .\INICIAR_RAG_COMPLETO.ps1 -SkipDrive" -ForegroundColor White
    Write-Host ""
    
    Write-Host "📝 Log completo en: $script:LogFile" -ForegroundColor Gray
    Write-Host ""
}

# ================================
# LÓGICA PRINCIPAL
# ================================

# Inicializar log
"" | Set-Content $script:LogFile -ErrorAction SilentlyContinue
Write-Log "🚀 Iniciando RAG Asistente completo..." "INFO"

try {
    # Verificar directorio correcto
    if (-not (Test-Path "manage.py")) {
        Write-Host "❌ Error: Este script debe ejecutarse desde el directorio backend/" -ForegroundColor Red
        Write-Host "   Directorio actual: $(Get-Location)" -ForegroundColor Yellow
        Write-Host "   Comando: cd backend; .\INICIAR_RAG_COMPLETO.ps1" -ForegroundColor Yellow
        exit 1
    }
    
    # Ejecutar pasos secuenciales
    if (-not (Test-Prerequisites)) { exit 1 }
    
    Initialize-Environment
    
    $driveConfigured = Setup-GoogleDrive
    
    Sync-DriveFiles -DriveConfigured $driveConfigured
    
    if (-not (Execute-ETL)) {
        Write-Log "⚠️ ETL falló, pero continuando con servidor..." "WARNING"
    }
    
    if ($NoFrontend) {
        # Solo backend
        Start-Backend
    } else {
        # Backend + Frontend
        if (Start-Backend) {
            Start-Frontend
        }
    }
    
} catch {
    Write-Log "❌ Error crítico: $_" "ERROR"
    Write-Host ""
    Write-Host "❌ ERROR CRÍTICO EN INICIO" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "📝 Revisa el log: $script:LogFile" -ForegroundColor Yellow
    exit 1
} finally {
    Show-Summary
}