# Script simple para configurar MySQL con Django
# Sin emojis ni caracteres especiales para evitar problemas de codificacion

Write-Host "CONFIGURANDO RAG ASISTENTE CON MYSQL" -ForegroundColor Green
Write-Host "======================================"

# Verificar directorio
if (-not (Test-Path "manage.py")) {
    Write-Host "ERROR: No se encontro manage.py" -ForegroundColor Red
    Write-Host "Ejecuta este script desde el directorio backend/" -ForegroundColor Yellow
    exit 1
}

# Verificar archivo .env
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: No se encontro el archivo .env" -ForegroundColor Red
    exit 1
}

Write-Host "Paso 1: Instalando dependencias..." -ForegroundColor Cyan
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { 
    Write-Host "ERROR en instalacion de dependencias" -ForegroundColor Red
    exit 1 
}

Write-Host "Paso 2: Configurando MySQL..." -ForegroundColor Cyan
python setup_mysql.py
if ($LASTEXITCODE -ne 0) { 
    Write-Host "ERROR en configuracion MySQL" -ForegroundColor Red
    Write-Host "Verifica que MySQL este corriendo" -ForegroundColor Yellow
    exit 1 
}

Write-Host "Paso 3: Aplicando migraciones..." -ForegroundColor Cyan
python manage.py makemigrations
python manage.py migrate
if ($LASTEXITCODE -ne 0) { 
    Write-Host "ERROR en migraciones" -ForegroundColor Red
    exit 1 
}

Write-Host "CONFIGURACION COMPLETADA!" -ForegroundColor Green
Write-Host "Usuario admin: admin / admin123" -ForegroundColor Yellow
Write-Host "Para iniciar: python manage.py runserver" -ForegroundColor Yellow

$iniciar = Read-Host "Iniciar servidor ahora? (s/n)"
if ($iniciar -eq "s") {
    python manage.py runserver
}