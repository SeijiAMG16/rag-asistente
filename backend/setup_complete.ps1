# Script para configurar automaticamente MySQL con Django
# Configuracion automatica del proyecto RAG Asistente

# Configurar la codificacion de la consola
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Configurando RAG Asistente con MySQL" -ForegroundColor Green
Write-Host "==============================================="

# Verificar si estamos en el directorio correcto
if (-not (Test-Path "manage.py")) {
    Write-Host "ERROR: No se encontro manage.py. Ejecuta este script desde el directorio backend/" -ForegroundColor Red
    exit 1
}

# Verificar si existe el archivo .env
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: No se encontro el archivo .env" -ForegroundColor Red
    Write-Host "SOLUCION: Crea un archivo .env con la configuracion de tu base de datos MySQL" -ForegroundColor Yellow
    exit 1
}

# Instalar dependencias
Write-Host "Instalando dependencias de Python..." -ForegroundColor Cyan
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: al instalar dependencias" -ForegroundColor Red
    exit 1
}

# Ejecutar script de configuracion MySQL
Write-Host "Configurando base de datos MySQL..." -ForegroundColor Cyan
python setup_mysql.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: en la configuracion de MySQL" -ForegroundColor Red
    Write-Host "SOLUCION: Verifica que MySQL este ejecutandose y las credenciales sean correctas" -ForegroundColor Yellow
    exit 1
}

# Ejecutar migraciones
Write-Host "Aplicando migraciones..." -ForegroundColor Cyan
python manage.py makemigrations
python manage.py migrate

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: al aplicar migraciones" -ForegroundColor Red
    exit 1
}

# Recolectar archivos estaticos
Write-Host "Recolectando archivos estaticos..." -ForegroundColor Cyan
python manage.py collectstatic --noinput

Write-Host "Configuracion completada exitosamente!" -ForegroundColor Green
Write-Host ""
Write-Host "Informacion importante:" -ForegroundColor Yellow
Write-Host "   - Base de datos: MySQL configurada automaticamente"
Write-Host "   - Usuario admin creado: admin / admin123"
Write-Host "   - Para iniciar el servidor: python manage.py runserver"
Write-Host "   - Panel de administracion: http://localhost:8000/admin/"
Write-Host ""
Write-Host "Deseas iniciar el servidor ahora? (S/N): " -ForegroundColor Cyan -NoNewline
$response = Read-Host

if ($response -eq "S" -or $response -eq "s" -or $response -eq "Y" -or $response -eq "y") {
    Write-Host "Iniciando servidor Django..." -ForegroundColor Green
    python manage.py runserver
}