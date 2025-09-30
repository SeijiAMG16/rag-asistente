# 🔄 SCRIPT ETL COMPLETO PARA RAG ASISTENTE
# ==========================================
# 
# Este script ejecuta el proceso completo de ETL:
# - EXTRACT: Extrae texto de PDFs
# - TRANSFORM: Procesa y fragmenta textos
# - LOAD: Genera embeddings y carga en ChromaDB
#
# USO: .\EJECUTAR_ETL.ps1 [opciones]

param(
    [switch]$Force,         # Recrear base de datos completa
    [switch]$NoPdfs,        # No procesar PDFs, solo textos existentes
    [int]$ChunkSize = 800,  # Tamaño de chunks
    [string]$Model = "all-mpnet-base-v2"  # Modelo de embeddings
)

Write-Host "🔄 PROCESO ETL COMPLETO - RAG ASISTENTE" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

# Verificar que estamos en el directorio correcto
$currentDir = Get-Location
Write-Host "📁 Directorio: $currentDir" -ForegroundColor Cyan

# Verificar Python
Write-Host "🐍 Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python no está disponible" -ForegroundColor Red
    exit 1
}

# Mostrar configuración
Write-Host ""
Write-Host "⚙️ CONFIGURACIÓN DEL ETL:" -ForegroundColor Yellow
Write-Host "  📊 Chunk Size: $ChunkSize caracteres" -ForegroundColor White
Write-Host "  🤖 Modelo: sentence-transformers/$Model" -ForegroundColor White
Write-Host "  📚 Procesar PDFs: $(-not $NoPdfs)" -ForegroundColor White
Write-Host "  🔄 Forzar recreación: $Force" -ForegroundColor White
Write-Host ""

# Verificar estructura de directorios
Write-Host "📁 Verificando estructura..." -ForegroundColor Yellow

$dataDir = Join-Path $PSScriptRoot "..\data"
$pdfsDir = Join-Path $dataDir "pdfs"
$textsDir = Join-Path $dataDir "texts"

if (-not (Test-Path $dataDir)) {
    Write-Host "❌ ERROR: No existe el directorio data/" -ForegroundColor Red
    Write-Host "   Crea la estructura: data/pdfs/ y data/texts/" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Directorio data/ existe" -ForegroundColor Green

# Verificar contenido
if (Test-Path $pdfsDir) {
    $pdfCount = (Get-ChildItem -Path $pdfsDir -Filter "*.pdf").Count
    Write-Host "📄 PDFs encontrados: $pdfCount" -ForegroundColor Cyan
} else {
    Write-Host "⚠️ No existe directorio pdfs/" -ForegroundColor Yellow
    $pdfCount = 0
}

if (Test-Path $textsDir) {
    $txtCount = (Get-ChildItem -Path $textsDir -Filter "*.txt").Count
    Write-Host "📝 TXTs encontrados: $txtCount" -ForegroundColor Cyan
} else {
    Write-Host "⚠️ No existe directorio texts/" -ForegroundColor Yellow
    $txtCount = 0
}

if ($pdfCount -eq 0 -and $txtCount -eq 0) {
    Write-Host "❌ ERROR: No hay documentos para procesar" -ForegroundColor Red
    Write-Host "   Copia archivos PDF a data/pdfs/ o TXT a data/texts/" -ForegroundColor Red
    exit 1
}

# Construir comando de Python
$pythonCommand = "python etl_rag_complete.py"

if ($Force) {
    $pythonCommand += " --force"
}

if ($NoPdfs) {
    $pythonCommand += " --no-pdfs"
}

if ($ChunkSize -ne 800) {
    $pythonCommand += " --chunk-size $ChunkSize"
}

if ($Model -ne "all-mpnet-base-v2") {
    $pythonCommand += " --model $Model"
}

Write-Host ""
Write-Host "🚀 EJECUTANDO PROCESO ETL..." -ForegroundColor Green
Write-Host "Comando: $pythonCommand" -ForegroundColor Gray
Write-Host ""
Write-Host "Este proceso puede tomar varios minutos..." -ForegroundColor Yellow
Write-Host ""

# Ejecutar ETL
try {
    $startTime = Get-Date
    
    Invoke-Expression $pythonCommand
    $exitCode = $LASTEXITCODE
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host ""
    Write-Host "⏱️ Tiempo total: $($duration.ToString('mm\:ss'))" -ForegroundColor Cyan
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "🎉 PROCESO ETL COMPLETADO EXITOSAMENTE!" -ForegroundColor Green
        Write-Host "=====================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "✅ Documentos extraídos y procesados" -ForegroundColor Green
        Write-Host "✅ Embeddings generados y cargados" -ForegroundColor Green
        Write-Host "✅ Base de datos vectorial lista" -ForegroundColor Green
        Write-Host ""
        Write-Host "🚀 PRÓXIMOS PASOS:" -ForegroundColor Cyan
        Write-Host "1. Iniciar el servidor:" -ForegroundColor White
        Write-Host "   python start_rag.py" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "2. Probar el sistema:" -ForegroundColor White
        Write-Host "   python -c `"from utils.rag_utils import perform_semantic_search; print(perform_semantic_search('Arias 2020'))`"" -ForegroundColor Yellow
        Write-Host ""
        
    } else {
        Write-Host ""
        Write-Host "❌ ERROR EN EL PROCESO ETL" -ForegroundColor Red
        Write-Host "Código de salida: $exitCode" -ForegroundColor Red
        Write-Host "Revisa los mensajes de error anteriores" -ForegroundColor Red
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ ERROR EJECUTANDO EL PROCESO ETL" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")