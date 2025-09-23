#!/bin/bash
# Script de instalación automatizada para RAG Backend en Linux/macOS

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Instalador RAG Asistente - Linux/macOS${NC}"
echo "================================================"

# ==== CONFIGURACIÓN - EDITA ESTAS VARIABLES ====
DB_ADMIN_USER="root"
DB_ADMIN_PASSWORD="root"  # CAMBIAR POR TU PASSWORD REAL
DB_NAME="rag"
DB_USER="rag_user"
DB_PASSWORD="strong_password"
DB_HOST="127.0.0.1"
DB_PORT="3306"

SERVICE_ACCOUNT_FILE="/ruta/a/tu/service_account.json"  # CAMBIAR POR RUTA REAL
DRIVE_FOLDER_ID="tu_id_de_carpeta_drive"               # CAMBIAR POR ID REAL

# ==== NO EDITES DEBAJO DE ESTA LÍNEA ====

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Error: Debes ejecutar este script desde el directorio backend/${NC}"
    echo "Ejemplo: cd rag-asistente/backend && ./install.sh"
    exit 1
fi

echo -e "${YELLOW}📋 Verificando requisitos del sistema...${NC}"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no está instalado${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 encontrado: $(python3 --version)${NC}"

# Verificar MySQL
if ! command -v mysql &> /dev/null; then
    echo -e "${RED}❌ MySQL no está instalado${NC}"
    echo "Instalar con: sudo apt install mysql-server (Ubuntu) o brew install mysql (macOS)"
    exit 1
fi
echo -e "${GREEN}✅ MySQL encontrado${NC}"

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 no está instalado${NC}"
    exit 1
fi
echo -e "${GREEN}✅ pip3 encontrado${NC}"

echo -e "${YELLOW}🔧 Configurando entorno virtual...${NC}"

# Crear directorio scripts si no existe
mkdir -p scripts
cd scripts

# Crear entorno virtual
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✅ Entorno virtual creado${NC}"
else
    echo -e "${YELLOW}⚠️  Entorno virtual ya existe${NC}"
fi

# Activar entorno virtual
source .venv/bin/activate

# Actualizar pip
pip install --upgrade pip

echo -e "${YELLOW}📦 Instalando dependencias Python...${NC}"
# Instalar dependencias
pip install -r ../requirements.txt

echo -e "${YELLOW}🗄️  Configurando variables de entorno...${NC}"
# Exportar variables de entorno
export USE_SQLITE="0"
export DB_HOST="$DB_HOST"
export DB_PORT="$DB_PORT"
export DB_NAME="$DB_NAME"
export DB_USER="$DB_USER"
export DB_PASSWORD="$DB_PASSWORD"
export SERVICE_ACCOUNT_FILE="$SERVICE_ACCOUNT_FILE"
export DRIVE_FOLDER_ID="$DRIVE_FOLDER_ID"

# Volver al directorio backend
cd ..

echo -e "${YELLOW}🗄️  Configurando base de datos MySQL...${NC}"
# Crear base de datos y usuario
python manage.py initdb --admin-user "$DB_ADMIN_USER" --admin-password "$DB_ADMIN_PASSWORD" --db-name "$DB_NAME" --app-user "$DB_USER" --app-password "$DB_PASSWORD"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Base de datos configurada correctamente${NC}"
else
    echo -e "${RED}❌ Error configurando base de datos${NC}"
    exit 1
fi

echo -e "${YELLOW}🔄 Ejecutando migraciones...${NC}"
# Migrar modelos
python manage.py migrate

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migraciones ejecutadas correctamente${NC}"
else
    echo -e "${RED}❌ Error ejecutando migraciones${NC}"
    exit 1
fi

echo -e "${YELLOW}📁 Sincronizando PDFs desde Google Drive...${NC}"
# Sincronizar y alimentar PDFs desde Drive
python manage.py sync_drive_full --chunk-size 600 --chunk-overlap 60

echo -e "${GREEN}🎉 ¡Instalación completada!${NC}"
echo "================================================"
echo -e "${BLUE}📋 Próximos pasos:${NC}"
echo "1. Verificar que las credenciales de Google Drive sean correctas"
echo "2. Iniciar el servidor Django:"
echo "   ${YELLOW}python manage.py runserver 0.0.0.0:8000${NC}"
echo "3. En otra terminal, iniciar el frontend React:"
echo "   ${YELLOW}cd frontend-react && npm install && npm start${NC}"
echo ""
echo -e "${BLUE}🌐 URLs:${NC}"
echo "- Backend API: http://localhost:8000"
echo "- Frontend React: http://localhost:3000"
echo "- Admin Django: http://localhost:8000/admin"
echo ""
echo -e "${BLUE}🔧 Para desarrollo futuro:${NC}"
echo "- Activar entorno: ${YELLOW}source scripts/.venv/bin/activate${NC}"
echo "- Sincronizar Drive: ${YELLOW}python manage.py sync_drive_full${NC}"