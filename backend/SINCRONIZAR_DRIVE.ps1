# 🔄 SINCRONIZAR GOOGLE DRIVE - RAG ASISTENTE
# =============================================
# 
# Script PowerShell para sincronización automática con Google Drive
# Incluye descarga de PDFs, procesamiento y ingesta en ChromaDB
#
# USO:
#   .\SINCRONIZAR_DRIVE.ps1           # Sincronización básica
#   .\SINCRONIZAR_DRIVE.ps1 -Setup    # Configuración inicial
#   .\SINCRONIZAR_DRIVE.ps1 -Force    # Forzar re-descarga
#   .\SINCRONIZAR_DRIVE.ps1 -Status   # Ver estado

param(
    [switch]$Setup,         # Ejecutar configuración inicial
    [switch]$Force,         # Forzar re-descarga de todos los PDFs
    [switch]$Status,        # Mostrar estado del sistema
    [switch]$Daemon,        # Iniciar daemon de sincronización
    [int]$ChunkSize = 800,  # Tamaño de chunks para ETL
    [int]$Interval = 30     # Intervalo en minutos para daemon
)

Write-Host "🔄 SINCRONIZACIÓN GOOGLE DRIVE - RAG ASISTENTE" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

# Verificar que estamos en el directorio correcto
$currentDir = Get-Location
$backendDir = $currentDir
$projectRoot = Split-Path $backendDir -Parent

if (-not (Test-Path "manage.py")) {
    Write-Host "❌ Error: Ejecuta desde el directorio backend" -ForegroundColor Red
    Write-Host "   Directorio actual: $currentDir" -ForegroundColor Yellow
    exit 1
}

Write-Host "📁 Directorio backend: $backendDir" -ForegroundColor Cyan
Write-Host "📁 Directorio proyecto: $projectRoot" -ForegroundColor Cyan
Write-Host ""

# Función para verificar si Python está disponible
function Test-PythonEnvironment {
    try {
        $pythonVersion = & python --version 2>&1
        if ($pythonVersion -match "Python") {
            Write-Host "✅ Python disponible: $pythonVersion" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "❌ Python no encontrado en PATH" -ForegroundColor Red
        return $false
    }
}

# Función para activar entorno virtual si existe
function Enable-VirtualEnvironment {
    $venvPaths = @(
        ".venv\Scripts\Activate.ps1",
        "venv\Scripts\Activate.ps1",
        "$projectRoot\.venv\Scripts\Activate.ps1",
        "$projectRoot\venv\Scripts\Activate.ps1"
    )
    
    foreach ($venvPath in $venvPaths) {
        if (Test-Path $venvPath) {
            Write-Host "🔧 Activando entorno virtual: $venvPath" -ForegroundColor Yellow
            try {
                & $venvPath
                Write-Host "✅ Entorno virtual activado" -ForegroundColor Green
                return $true
            }
            catch {
                Write-Host "⚠️ Error activando entorno virtual: $_" -ForegroundColor Yellow
            }
        }
    }
    
    Write-Host "⚠️ Entorno virtual no encontrado, usando Python del sistema" -ForegroundColor Yellow
    return $false
}

# Función para instalar dependencias de Google Drive
function Install-GoogleDriveDependencies {
    Write-Host "📦 Instalando dependencias de Google Drive..." -ForegroundColor Yellow
    
    $packages = @(
        "google-api-python-client",
        "google-auth-httplib2",
        "google-auth-oauthlib",
        "python-dotenv"
    )
    
    foreach ($package in $packages) {
        Write-Host "   📦 Instalando: $package" -ForegroundColor Cyan
        try {
            & python -m pip install $package --quiet
            Write-Host "   ✅ $package instalado" -ForegroundColor Green
        }
        catch {
            Write-Host "   ❌ Error instalando $package`: $_" -ForegroundColor Red
            return $false
        }
    }
    
    Write-Host "✅ Todas las dependencias instaladas" -ForegroundColor Green
    return $true
}

# Función para verificar configuración de Google Drive
function Test-GoogleDriveConfig {
    Write-Host "🔍 Verificando configuración de Google Drive..." -ForegroundColor Yellow
    
    # Verificar archivos necesarios
    $configFiles = @{
        "credentials.json" = "Credenciales de cuenta de servicio"
        ".env" = "Variables de entorno"
    }
    
    $allFilesExist = $true
    foreach ($file in $configFiles.Keys) {
        if (Test-Path $file) {
            Write-Host "   ✅ $file - $($configFiles[$file])" -ForegroundColor Green
        }
        else {
            Write-Host "   ❌ $file - $($configFiles[$file])" -ForegroundColor Red
            $allFilesExist = $false
        }
    }
    
    if (-not $allFilesExist) {
        Write-Host ""
        Write-Host "⚠️ Configuración incompleta. Ejecuta con -Setup para configurar" -ForegroundColor Yellow
        return $false
    }
    
    # Verificar variables de entorno en .env
    if (Test-Path ".env") {
        $envContent = Get-Content ".env" -ErrorAction SilentlyContinue
        $hasGoogleDrive = $envContent | Where-Object { $_ -match "GOOGLE_DRIVE_ENABLED.*true" }
        $hasFolderId = $envContent | Where-Object { $_ -match "DRIVE_FOLDER_ID.*=" }
        
        if ($hasGoogleDrive) {
            Write-Host "   ✅ Google Drive habilitado" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠️ Google Drive no habilitado en .env" -ForegroundColor Yellow
        }
        
        if ($hasFolderId) {
            Write-Host "   ✅ ID de carpeta configurado" -ForegroundColor Green
        }
        else {
            Write-Host "   ❌ ID de carpeta no configurado" -ForegroundColor Red
            return $false
        }
    }
    
    Write-Host "✅ Configuración básica correcta" -ForegroundColor Green
    return $true
}

# Función principal para setup
function Invoke-GoogleDriveSetup {
    Write-Host "🔧 CONFIGURACIÓN INICIAL DE GOOGLE DRIVE" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Instalar dependencias
    if (-not (Install-GoogleDriveDependencies)) {
        Write-Host "❌ Error instalando dependencias" -ForegroundColor Red
        return $false
    }
    
    Write-Host ""
    Write-Host "🚀 Ejecutando configurador automático..." -ForegroundColor Yellow
    
    try {
        & python setup_google_drive.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Configuración completada exitosamente" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ Error en configuración automática" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Error ejecutando configurador: $_" -ForegroundColor Red
        return $false
    }
}

# Función para mostrar estado
function Show-GoogleDriveStatus {
    Write-Host "📊 ESTADO DEL SISTEMA GOOGLE DRIVE" -ForegroundColor Cyan
    Write-Host "===================================" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        & python manage.py start_drive_sync --action status
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✅ Estado obtenido exitosamente" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️ Error obteniendo estado" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "❌ Error ejecutando comando de estado: $_" -ForegroundColor Red
    }
}

# Función para sincronización completa
function Invoke-DriveSync {
    param([bool]$ForceDownload = $false)
    
    Write-Host "🔄 INICIANDO SINCRONIZACIÓN COMPLETA" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Construir comando
    $syncCommand = "python manage.py sync_drive_full --chunk-size $ChunkSize"
    
    if ($ForceDownload) {
        $syncCommand += " --force"
        Write-Host "🔥 Modo FORZADO: Re-descargando todos los PDFs" -ForegroundColor Yellow
    }
    
    Write-Host "📋 Ejecutando: $syncCommand" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        # Ejecutar sincronización
        Invoke-Expression $syncCommand
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✅ Sincronización completada exitosamente" -ForegroundColor Green
            
            # Mostrar resumen de archivos
            Write-Host ""
            Write-Host "📊 RESUMEN POST-SINCRONIZACIÓN:" -ForegroundColor Cyan
            
            $dataDir = "data"
            if (Test-Path "$dataDir\pdfs") {
                $pdfCount = (Get-ChildItem "$dataDir\pdfs" -Filter "*.pdf" -ErrorAction SilentlyContinue).Count
                Write-Host "   📄 PDFs descargados: $pdfCount" -ForegroundColor Green
            }
            
            if (Test-Path "$dataDir\texts") {
                $txtCount = (Get-ChildItem "$dataDir\texts" -Filter "*.txt" -ErrorAction SilentlyContinue).Count
                Write-Host "   📝 Textos extraídos: $txtCount" -ForegroundColor Green
            }
            
            # Verificar ChromaDB
            $chromaDbPath = "chroma_db_simple"
            if (Test-Path $chromaDbPath) {
                Write-Host "   🗄️ Base vectorial: ✅ Actualizada" -ForegroundColor Green
            }
            else {
                Write-Host "   🗄️ Base vectorial: ⚠️ No encontrada" -ForegroundColor Yellow
            }
            
            return $true
        }
        else {
            Write-Host ""
            Write-Host "❌ Error en sincronización (código: $LASTEXITCODE)" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Error ejecutando sincronización: $_" -ForegroundColor Red
        return $false
    }
}

# Función para iniciar daemon
function Start-SyncDaemon {
    Write-Host "🔄 INICIANDO DAEMON DE SINCRONIZACIÓN" -ForegroundColor Cyan
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "⏱️ Intervalo configurado: $Interval minutos" -ForegroundColor Yellow
    Write-Host "🔄 Sincronización automática iniciándose..." -ForegroundColor Yellow
    Write-Host ""
    
    try {
        & python manage.py start_drive_sync --action start --interval $Interval
        
        Write-Host ""
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Daemon iniciado exitosamente" -ForegroundColor Green
        }
        else {
            Write-Host "❌ Error iniciando daemon" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Error ejecutando daemon: $_" -ForegroundColor Red
    }
}

# LÓGICA PRINCIPAL
# ================

# Verificar Python
if (-not (Test-PythonEnvironment)) {
    Write-Host "❌ Python no disponible. Instala Python 3.8+ y asegúrate que esté en PATH" -ForegroundColor Red
    exit 1
}

# Activar entorno virtual
Enable-VirtualEnvironment | Out-Null

Write-Host ""

# Procesar parámetros
if ($Setup) {
    # Ejecutar configuración inicial
    $setupSuccess = Invoke-GoogleDriveSetup
    if (-not $setupSuccess) {
        Write-Host ""
        Write-Host "❌ Error en configuración inicial" -ForegroundColor Red
        exit 1
    }
}
elseif ($Status) {
    # Mostrar estado
    Show-GoogleDriveStatus
}
elseif ($Daemon) {
    # Iniciar daemon
    if (-not (Test-GoogleDriveConfig)) {
        Write-Host "❌ Configuración incompleta. Ejecuta con -Setup primero" -ForegroundColor Red
        exit 1
    }
    Start-SyncDaemon
}
else {
    # Sincronización normal
    if (-not (Test-GoogleDriveConfig)) {
        Write-Host "❌ Configuración incompleta. Ejecuta con -Setup primero" -ForegroundColor Red
        Write-Host ""
        Write-Host "💡 Para configurar: .\SINCRONIZAR_DRIVE.ps1 -Setup" -ForegroundColor Yellow
        exit 1
    }
    
    $syncSuccess = Invoke-DriveSync -ForceDownload $Force
    if (-not $syncSuccess) {
        Write-Host ""
        Write-Host "❌ Error en sincronización" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🎉 Proceso completado exitosamente" -ForegroundColor Green
Write-Host ""
Write-Host "💡 COMANDOS ÚTILES:" -ForegroundColor Cyan
Write-Host "   .\SINCRONIZAR_DRIVE.ps1           # Sincronización normal" -ForegroundColor White
Write-Host "   .\SINCRONIZAR_DRIVE.ps1 -Force    # Forzar re-descarga" -ForegroundColor White
Write-Host "   .\SINCRONIZAR_DRIVE.ps1 -Status   # Ver estado" -ForegroundColor White
Write-Host "   .\SINCRONIZAR_DRIVE.ps1 -Daemon   # Iniciar automático" -ForegroundColor White
Write-Host ""