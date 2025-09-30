# 🚀 ARRANQUE RÁPIDO - RAG ASISTENTE
# ==================================
# 
# Script simplificado para arranque diario después de configuración inicial
# Solo verifica sistema y arranca backend/frontend sin configuración
#
# USO:
#   .\ARRANCAR_RAG.ps1                  # Arranque normal
#   .\ARRANCAR_RAG.ps1 -Port 8080       # Puerto personalizado
#   .\ARRANCAR_RAG.ps1 -SoloBackend     # Solo backend, sin frontend
#   .\ARRANCAR_RAG.ps1 -ConSync         # Incluir sincronización Drive

param(
    [int]$Port = 8000,        # Puerto para el backend
    [switch]$SoloBackend,     # Solo arrancar backend
    [switch]$ConSync,         # Incluir sincronización con Drive
    [switch]$Verbose          # Mostrar más detalles
)

$Host.UI.RawUI.WindowTitle = "RAG Asistente - Arranque Rápido"

Write-Host ""
Write-Host "🚀 RAG ASISTENTE - ARRANQUE RÁPIDO" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""

# Variables
$BackendDir = Get-Location
$ProjectRoot = Split-Path $BackendDir -Parent
$FrontendDir = Join-Path $ProjectRoot "frontend-react"

# Función para logging simple
function Write-Status {
    param([string]$Message, [string]$Status = "INFO")
    $icon = switch ($Status) {
        "SUCCESS" { "✅" }
        "ERROR" { "❌" }
        "WARNING" { "⚠️" }
        "INFO" { "🔄" }
        default { "📋" }
    }
    Write-Host "$icon $Message" -ForegroundColor $(switch ($Status) {
        "SUCCESS" { "Green" }
        "ERROR" { "Red" } 
        "WARNING" { "Yellow" }
        default { "White" }
    })
}

# Verificaciones rápidas
Write-Host "📋 Verificaciones rápidas..." -ForegroundColor Cyan
Write-Host ""

# Verificar directorio
if (-not (Test-Path "manage.py")) {
    Write-Status "Error: Ejecuta desde el directorio backend/" "ERROR"
    exit 1
}
Write-Status "Directorio backend correcto" "SUCCESS"

# Verificar Python
try {
    $pythonVersion = & python --version 2>&1
    if ($pythonVersion -match "Python") {
        Write-Status "Python disponible: $pythonVersion" "SUCCESS"
    } else {
        Write-Status "Python no encontrado" "ERROR"
        exit 1
    }
} catch {
    Write-Status "Python no disponible" "ERROR"
    exit 1
}

# Activar entorno virtual si existe
$venvPaths = @(
    ".venv\Scripts\Activate.ps1",
    "venv\Scripts\Activate.ps1",
    "$ProjectRoot\.venv\Scripts\Activate.ps1"
)

foreach ($venvPath in $venvPaths) {
    if (Test-Path $venvPath) {
        Write-Status "Activando entorno virtual..." "INFO"
        try {
            & $venvPath
            Write-Status "Entorno virtual activado" "SUCCESS"
            break
        } catch {
            Write-Status "Error activando entorno virtual" "WARNING"
        }
    }
}

# Verificar base de datos vectorial
if (Test-Path "chroma_db_simple") {
    Write-Status "Base de datos vectorial encontrada" "SUCCESS"
} else {
    Write-Status "Base vectorial no encontrada - ejecuta configuración completa" "WARNING"
    
    $response = Read-Host "¿Quieres ejecutar configuración completa? (s/n)"
    if ($response -match '^[sySí]') {
        Write-Host "🔄 Ejecutando configuración completa..." -ForegroundColor Yellow
        & .\INICIAR_RAG_COMPLETO.ps1 -Setup
        exit $LASTEXITCODE
    }
}

# Sincronización opcional con Google Drive
if ($ConSync) {
    Write-Host ""
    Write-Host "🔄 Sincronizando con Google Drive..." -ForegroundColor Cyan
    
    if (Test-Path "SINCRONIZAR_DRIVE.ps1") {
        try {
            & .\SINCRONIZAR_DRIVE.ps1
            if ($LASTEXITCODE -eq 0) {
                Write-Status "Sincronización completada" "SUCCESS"
            } else {
                Write-Status "Error en sincronización" "WARNING"
            }
        } catch {
            Write-Status "Error ejecutando sincronización" "WARNING"
        }
    } else {
        Write-Status "Script de Google Drive no encontrado" "WARNING"
    }
}

Write-Host ""
Write-Host "🚀 Iniciando servicios..." -ForegroundColor Cyan
Write-Host ""

# Aplicar migraciones rápidas
Write-Status "Aplicando migraciones..." "INFO"
& python manage.py migrate --run-syncdb 2>$null | Out-Null

# Verificar puerto disponible
try {
    $portTest = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($portTest) {
        Write-Status "Puerto $Port ya está en uso" "WARNING"
        $Port = $Port + 1
        Write-Status "Usando puerto $Port en su lugar" "INFO"
    }
} catch {
    # Si Test-NetConnection no está disponible, continuar
}

# Iniciar backend
Write-Status "Iniciando servidor Django en puerto $Port..." "INFO"

if ($SoloBackend) {
    # Solo backend en foreground
    Write-Host ""
    Write-Host "🌐 SERVIDOR BACKEND" -ForegroundColor Green
    Write-Host "   URL: http://localhost:$Port" -ForegroundColor Cyan
    Write-Host "   Admin: http://localhost:$Port/admin" -ForegroundColor Cyan
    Write-Host "   Presiona Ctrl+C para detener" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        & python manage.py runserver "0.0.0.0:$Port"
    } catch {
        Write-Status "Error iniciando servidor" "ERROR"
        exit 1
    }
} else {
    # Backend en background + frontend
    Write-Status "Iniciando backend en background..." "INFO"
    
    $backendProcess = Start-Process python -ArgumentList "manage.py", "runserver", "0.0.0.0:$Port" -PassThru -WindowStyle Hidden
    
    # Esperar a que el servidor esté listo
    Write-Status "Esperando que el servidor esté listo..." "INFO"
    Start-Sleep 3
    
    # Verificar que el backend esté funcionando
    $backendOk = $false
    for ($i = 0; $i -lt 10; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$Port/api/health" -Method GET -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Status "Backend funcionando correctamente" "SUCCESS"
                $backendOk = $true
                break
            }
        } catch {
            Start-Sleep 1
        }
    }
    
    if (-not $backendOk) {
        Write-Status "Backend puede no estar respondiendo correctamente" "WARNING"
    }
    
    # Iniciar frontend si está disponible
    if (Test-Path $FrontendDir) {
        Write-Status "Iniciando frontend React..." "INFO"
        
        Push-Location $FrontendDir
        try {
            # Verificar Node.js
            $nodeVersion = & node --version 2>&1
            if ($nodeVersion -match "v\d+") {
                Write-Status "Node.js $nodeVersion disponible" "SUCCESS"
                
                # Verificar dependencias
                if (-not (Test-Path "node_modules")) {
                    Write-Status "Instalando dependencias de Node.js..." "INFO"
                    & npm install | Out-Null
                }
                
                Write-Host ""
                Write-Host "🌐 SERVIDORES INICIADOS" -ForegroundColor Green
                Write-Host "   Backend: http://localhost:$Port" -ForegroundColor Cyan
                Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Cyan
                Write-Host "   Admin: http://localhost:$Port/admin" -ForegroundColor Cyan
                Write-Host ""
                Write-Host "🔑 Usuario: admin / admin123" -ForegroundColor Yellow
                Write-Host ""
                Write-Host "📱 El navegador se abrirá automáticamente..." -ForegroundColor Green
                Write-Host "   Presiona Ctrl+C para detener ambos servidores" -ForegroundColor Yellow
                Write-Host ""
                
                # Registrar proceso del backend para cleanup
                $cleanup = {
                    if (-not $backendProcess.HasExited) {
                        $backendProcess.Kill()
                        Write-Host "`n🛑 Servidor backend detenido" -ForegroundColor Yellow
                    }
                }
                
                # Registrar evento de salida
                Register-EngineEvent PowerShell.Exiting -Action $cleanup | Out-Null
                
                # Iniciar frontend (foreground)
                & npm start
                
            } else {
                Write-Status "Node.js no disponible - solo backend funcionando" "WARNING"
                Write-Host ""
                Write-Host "🌐 Backend: http://localhost:$Port" -ForegroundColor Cyan
                Write-Host "🔑 Usuario: admin / admin123" -ForegroundColor Yellow
                
                # Mantener backend en foreground
                Wait-Process -Id $backendProcess.Id
            }
        } catch {
            Write-Status "Error iniciando frontend: $_" "ERROR"
        } finally {
            Pop-Location
            # Cleanup backend process
            if ($backendProcess -and -not $backendProcess.HasExited) {
                $backendProcess.Kill()
                Write-Status "Servidor backend detenido" "INFO"
            }
        }
    } else {
        Write-Status "Frontend no encontrado - solo backend" "WARNING"
        Write-Host ""
        Write-Host "🌐 Backend: http://localhost:$Port" -ForegroundColor Cyan
        Write-Host "🔑 Usuario: admin / admin123" -ForegroundColor Yellow
        Write-Host ""
        
        # Mantener backend en foreground
        Wait-Process -Id $backendProcess.Id
    }
}

Write-Host ""
Write-Status "RAG Asistente finalizado" "INFO"