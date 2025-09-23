# Pipeline RAG completo para Windows
# Ejecuta todo el proceso de ETL y configuracion del sistema RAG

Write-Host "PIPELINE COMPLETO RAG ASISTENTE" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green

# Verificar directorio
if (-not (Test-Path "scripts")) {
    Write-Host "ERROR: Ejecuta este script desde la raiz del proyecto" -ForegroundColor Red
    exit 1
}

# Verificar credentials.json
if (-not (Test-Path "credentials.json")) {
    Write-Host "ERROR: No se encontro credentials.json" -ForegroundColor Red
    Write-Host "SOLUCION: Descarga credentials.json desde Google Cloud Console" -ForegroundColor Yellow
    exit 1
}

# Navegar a scripts
Set-Location scripts

Write-Host "Paso 1: Instalando dependencias..." -ForegroundColor Cyan
pip install -r ../requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: en instalacion de dependencias" -ForegroundColor Red
    exit 1
}

Write-Host "Paso 2: Ejecutando ETL de Google Drive..." -ForegroundColor Cyan
python etl_drive.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: en ETL de Google Drive" -ForegroundColor Red
    Write-Host "VERIFICAR: credentials.json y permisos de Google Drive" -ForegroundColor Yellow
    exit 1
}

Write-Host "Paso 3: Ingresando documentos a ChromaDB..." -ForegroundColor Cyan
python ingest_chromadb.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: en ingesta a ChromaDB" -ForegroundColor Red
    exit 1
}

Write-Host "PIPELINE COMPLETADO EXITOSAMENTE!" -ForegroundColor Green
Write-Host ""
Write-Host "Recursos disponibles:" -ForegroundColor Yellow
Write-Host "  - Documentos: ../data/pdfs/" -ForegroundColor White
Write-Host "  - Textos: ../data/texts/" -ForegroundColor White
Write-Host "  - Base vectorial: ../chroma_db/" -ForegroundColor White
Write-Host ""
Write-Host "Sistema RAG listo para usar!" -ForegroundColor Green

# Volver al directorio anterior
Set-Location ..