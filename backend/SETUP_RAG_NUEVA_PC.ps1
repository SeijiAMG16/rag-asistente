# 🚀 SCRIPT DE INICIALIZACIÓN RAG PARA NUEVA PC
# ================================================
# 
# Este script configura completamente el sistema RAG en una nueva PC
# Ejecuta todas las configuraciones necesarias automáticamente
#
# USO: .\SETUP_RAG_NUEVA_PC.ps1

Write-Host "🚀 CONFIGURACIÓN COMPLETA DEL SISTEMA RAG" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# Verificar que estamos en el directorio correcto
$currentDir = Get-Location
Write-Host "📁 Directorio actual: $currentDir" -ForegroundColor Cyan

# Verificar Python
Write-Host "🐍 Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python no está instalado o no está en PATH" -ForegroundColor Red
    Write-Host "   Instala Python 3.9+ desde https://python.org" -ForegroundColor Red
    exit 1
}

# Verificar que existen los documentos
Write-Host "📚 Verificando documentos..." -ForegroundColor Yellow
$dataDir = Join-Path $PSScriptRoot "..\data\texts"
if (-not (Test-Path $dataDir)) {
    Write-Host "❌ ERROR: No existe la carpeta data\texts\" -ForegroundColor Red
    Write-Host "   Crea la carpeta y copia tus documentos .txt allí" -ForegroundColor Red
    exit 1
}

$txtFiles = Get-ChildItem -Path $dataDir -Filter "*.txt"
if ($txtFiles.Count -eq 0) {
    Write-Host "❌ ERROR: No hay archivos .txt en data\texts\" -ForegroundColor Red
    Write-Host "   Copia tus documentos académicos .txt a esa carpeta" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Encontrados $($txtFiles.Count) archivos .txt" -ForegroundColor Green

# Ejecutar inicialización de Python
Write-Host ""
Write-Host "🔧 EJECUTANDO CONFIGURACIÓN COMPLETA..." -ForegroundColor Yellow
Write-Host "Este proceso incluye ETL completo y puede tomar varios minutos..." -ForegroundColor Yellow
Write-Host ""

try {
    # Configurar Google Drive (opcional)
    Write-Host "🔄 Configurando sincronización con Google Drive..." -ForegroundColor Cyan
    Write-Host ""
    
    $configureGoogleDrive = $false
    if (-not $NoInteractive) {
        $response = Read-Host "¿Quieres configurar sincronización automática con Google Drive? (s/n)"
        $configureGoogleDrive = $response -match '^[sySí]'
    }
    
    if ($configureGoogleDrive) {
        Write-Host "🔧 Configurando Google Drive..." -ForegroundColor Yellow
        try {
            if (Test-Path "SINCRONIZAR_DRIVE.ps1") {
                .\SINCRONIZAR_DRIVE.ps1 -Setup
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✅ Google Drive configurado exitosamente" -ForegroundColor Green
                    
                    # Sincronizar archivos después de configurar
                    Write-Host "🔄 Sincronizando archivos desde Drive..." -ForegroundColor Yellow
                    .\SINCRONIZAR_DRIVE.ps1 -Force
                }
            }
            else {
                Write-Host "⚠️ Script de Google Drive no encontrado" -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "⚠️ Error en configuración de Google Drive: $_" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    # Opción 1: Usar ETL completo (recomendado)
    Write-Host "🔄 Ejecutando proceso ETL completo..." -ForegroundColor Cyan
    python etl_rag_complete.py --force
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -ne 0) {
        Write-Host "⚠️ ETL falló, intentando inicialización básica..." -ForegroundColor Yellow
        python initialize_rag_system.py
        $exitCode = $LASTEXITCODE
    }
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "🎉 CONFIGURACIÓN COMPLETADA EXITOSAMENTE!" -ForegroundColor Green
        Write-Host "=========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "✅ Sistema RAG completamente configurado" -ForegroundColor Green
        Write-Host "✅ Base de datos vectorial creada" -ForegroundColor Green
        Write-Host "✅ Embeddings optimizados generados" -ForegroundColor Green
        Write-Host ""
        Write-Host "🚀 PRÓXIMOS PASOS:" -ForegroundColor Cyan
        Write-Host "1. Para iniciar el servidor:" -ForegroundColor White
        Write-Host "   python manage.py runserver" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "2. O usar el script completo:" -ForegroundColor White
        Write-Host "   python start_rag.py" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "3. Configurar API keys (opcional):" -ForegroundColor White
        Write-Host "   Edita el archivo .env y agrega OPENROUTER_API_KEY" -ForegroundColor Yellow
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "❌ ERROR EN LA CONFIGURACIÓN" -ForegroundColor Red
        Write-Host "Revisa los mensajes de error anteriores" -ForegroundColor Red
        exit $exitCode
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ ERROR EJECUTANDO EL SCRIPT DE PYTHON" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")