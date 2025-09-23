# Script de arranque automático para RAG Backend + MySQL + Google Drive

Write-Host "🚀 RAG Asistente - Configuración Automática" -ForegroundColor Blue
Write-Host "==============================================" -ForegroundColor Blue

# ==== EDITA ESTAS VARIABLES SEGÚN TU INSTANCIA ====
$DB_ADMIN_USER = "root"
$DB_ADMIN_PASSWORD = "root"  # CAMBIAR POR TU PASSWORD REAL DE MYSQL
$DB_NAME = "rag"
$DB_USER = "rag_user"
$DB_PASSWORD = "strong_password"
$DB_HOST = "127.0.0.1"
$DB_PORT = "3306"

$SERVICE_ACCOUNT_FILE = "C:\ruta\a\service_account.json"   # CAMBIAR POR RUTA REAL
$DRIVE_FOLDER_ID = "1wAYnaln3Dg-MnFy6rNhwqPlh7Ouc4EP8"     # CAMBIAR POR ID REAL

# ==== NO EDITES DE AQUÍ ABAJO ====

# Verificar que estamos en el directorio correcto
if (!(Test-Path "..\manage.py")) {
    Write-Host "❌ Error: Debes ejecutar este script desde backend/scripts/" -ForegroundColor Red
    Write-Host "Ejemplo: cd rag-asistente\backend\scripts ; .\bootstrap_rag.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "📋 Verificando requisitos del sistema..." -ForegroundColor Yellow

# Verificar Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no está instalado o no está en PATH" -ForegroundColor Red
    exit 1
}

# Verificar MySQL (intentar conectar)
try {
    $mysqlTest = & "C:\Program Files\MySQL\MySQL Server 9.4\bin\mysql.exe" -u $DB_ADMIN_USER -p$DB_ADMIN_PASSWORD -e "SELECT 1;" 2>&1
    Write-Host "✅ MySQL conectado correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ No se puede conectar a MySQL. Verificar credenciales." -ForegroundColor Red
    Write-Host "Credenciales usadas: Usuario=$DB_ADMIN_USER" -ForegroundColor Yellow
    exit 1
}

cd $PSScriptRoot
Write-Host "📁 Directorio actual: $PWD" -ForegroundColor Cyan

Write-Host "🔧 Configurando entorno virtual..." -ForegroundColor Yellow
# 1. Activar entorno virtual
if (!(Test-Path ".venv")) { 
    Write-Host "Creando entorno virtual..." -ForegroundColor Cyan
    python -m venv .venv 
}
. .\.venv\Scripts\Activate.ps1
Write-Host "✅ Entorno virtual activado" -ForegroundColor Green

Write-Host "📦 Instalando dependencias Python..." -ForegroundColor Yellow
# 2. Instalar dependencias
pip install --upgrade pip | Out-Host
pip install -r ..\requirements.txt | Out-Host

Write-Host "🗄️ Configurando variables de entorno..." -ForegroundColor Yellow
# 3. Exportar variables de entorno
$env:USE_SQLITE = "0"
$env:DB_HOST = $DB_HOST
$env:DB_PORT = $DB_PORT
$env:DB_NAME = $DB_NAME
$env:DB_USER = $DB_USER
$env:DB_PASSWORD = $DB_PASSWORD
$env:SERVICE_ACCOUNT_FILE = $SERVICE_ACCOUNT_FILE
$env:DRIVE_FOLDER_ID = $DRIVE_FOLDER_ID

# Cambiar al directorio backend
cd ..

Write-Host "🗄️ Configurando base de datos MySQL..." -ForegroundColor Yellow
# 4. Crear base de datos y usuario si no existen
try {
    python manage.py initdb --admin-user $DB_ADMIN_USER --admin-password $DB_ADMIN_PASSWORD --db-name $DB_NAME --app-user $DB_USER --app-password $DB_PASSWORD
    Write-Host "✅ Base de datos configurada correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ Error configurando base de datos" -ForegroundColor Red
    exit 1
}

Write-Host "🔄 Ejecutando migraciones Django..." -ForegroundColor Yellow
# 5. Migrar modelos
try {
    python manage.py migrate
    Write-Host "✅ Migraciones ejecutadas correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ Error ejecutando migraciones" -ForegroundColor Red
    exit 1
}

Write-Host "📁 Sincronizando PDFs desde Google Drive..." -ForegroundColor Yellow
# 6. Sincronizar y alimentar PDFs desde Drive
python manage.py sync_drive_full --chunk-size 600 --chunk-overlap 60

Write-Host "🎉 ¡Configuración completada!" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Blue
Write-Host "📋 Próximos pasos:" -ForegroundColor Blue
Write-Host "1. Verificar que las credenciales de Google Drive sean correctas" -ForegroundColor White
Write-Host "2. El servidor Django se iniciará automáticamente..." -ForegroundColor White
Write-Host "3. En otra terminal, iniciar el frontend React:" -ForegroundColor White
Write-Host "   cd frontend-react && npm install && npm start" -ForegroundColor Yellow
Write-Host "" 
Write-Host "🌐 URLs importantes:" -ForegroundColor Blue
Write-Host "- Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "- Frontend React: http://localhost:3000" -ForegroundColor Cyan  
Write-Host "- Admin Django: http://localhost:8000/admin" -ForegroundColor Cyan
Write-Host ""

Write-Host "🚀 Iniciando servidor Django..." -ForegroundColor Green
Write-Host "Para detener el servidor: Ctrl+C" -ForegroundColor Yellow
Write-Host "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000