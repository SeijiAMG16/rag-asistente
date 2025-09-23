# 📚 Asistente RAG Local (Django + React + ChromaDB + Google Drive + MySQL)

Asistente conversacional local para consultar tus propios documentos PDF desde Google Drive, combinando búsqueda semántica con RAG (Retrieval-Augmented Generation) y una interfaz web moderna.

---

## 🚀 Características

- **Backend Django**: API REST robusta con autenticación JWT
- **Frontend React**: Interfaz moderna y responsiva
- **Base de datos MySQL**: Almacenamiento confiable de conversaciones y metadatos
- **ChromaDB**: Base de datos vectorial para búsqueda semántica
- **Google Drive Integration**: Sincronización automática de PDFs
- **RAG Local**: Procesamiento 100% local, sin APIs externas
- **Autenticación**: Sistema completo de login/registro

---

## 🖥️ Requisitos Previos

Antes de instalar, asegúrate de tener:

- **Python 3.9+** (recomendado 3.10+)
- **Node.js 16+** y **npm**
- **MySQL Server** (versión 5.7+ o 8.0+)
- **Git**
- Cuenta de **Google Drive** y credenciales de servicio

---

## 🛠️ Instalación Completa

### **Paso 1: Clonar el Repositorio**

```bash
git clone https://github.com/SeijiAMG16/rag-asistente.git
cd rag-asistente
```

### **Paso 2: Configurar MySQL**

1. **Instalar MySQL** (si no está instalado):
   - Windows: Descargar desde [mysql.com](https://dev.mysql.com/downloads/mysql/)
   - Ubuntu/Debian: `sudo apt install mysql-server`
   - macOS: `brew install mysql`

2. **Iniciar el servicio MySQL**:
   - Windows: El servicio se inicia automáticamente
   - Linux/macOS: `sudo systemctl start mysql` o `brew services start mysql`

3. **Verificar conexión**:
   ```bash
   mysql -u root -p
   ```

### **Paso 3: Configurar Google Drive API**

1. **Crear proyecto en Google Cloud Console**:
   - Ir a [Google Cloud Console](https://console.cloud.google.com/)
   - Crear nuevo proyecto o seleccionar uno existente

2. **Habilitar Google Drive API**:
   - Buscar "Google Drive API" y habilitarla

3. **Crear cuenta de servicio**:
   - Ir a "Credenciales" → "Crear credenciales" → "Cuenta de servicio"
   - Descargar el archivo JSON de credenciales
   - Guardar como `service_account.json` en ubicación conocida

4. **Obtener ID de carpeta de Google Drive**:
   - Abrir Google Drive en navegador
   - Navegar a la carpeta con tus PDFs
   - Copiar el ID de la URL: `https://drive.google.com/drive/folders/[ID_AQUÍ]`

### **Paso 4: Configurar Backend (Django)**

```bash
# Navegar al directorio backend
cd backend/scripts

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r ../requirements.txt
```

### **Paso 5: Configurar Variables de Entorno**

Editar el archivo `backend/scripts/bootstrap_rag.ps1` (Windows) y actualizar estas variables:

```powershell
# EDITAR ESTAS VARIABLES SEGÚN TU CONFIGURACIÓN
$DB_ADMIN_USER = "root"                                           # Usuario admin de MySQL
$DB_ADMIN_PASSWORD = "tu_password_mysql"                         # Password de root MySQL
$DB_NAME = "rag"                                                 # Nombre de la BD (puedes mantenerlo)
$DB_USER = "rag_user"                                           # Usuario de la app (puedes mantenerlo)
$DB_PASSWORD = "strong_password"                                # Password del usuario app
$DB_HOST = "127.0.0.1"                                         # Host MySQL (local)
$DB_PORT = "3306"                                              # Puerto MySQL

$SERVICE_ACCOUNT_FILE = "C:\ruta\real\a\tu\service_account.json"  # RUTA REAL al JSON de Google
$DRIVE_FOLDER_ID = "tu_id_de_carpeta_drive_real"                  # ID REAL de tu carpeta Drive
```

### **Paso 6: Ejecutar Bootstrap del Backend**

```bash
# Desde backend/scripts/ con entorno virtual activado
cd backend/scripts
.\bootstrap_rag.ps1
```

Este script automáticamente:
- ✅ Crea la base de datos MySQL y usuario
- ✅ Ejecuta migraciones de Django
- ✅ Sincroniza PDFs desde Google Drive
- ✅ Procesa y vectoriza los documentos
- ✅ Inicia el servidor Django en `http://localhost:8000`

### **Paso 7: Configurar Frontend (React)**

En una **nueva terminal**:

```bash
# Navegar al frontend
cd frontend-react

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm start
```

El frontend estará disponible en `http://localhost:3000`

---

## 🚀 Uso Diario

Una vez configurado, para usar la aplicación:

### **Iniciar Backend:**
```bash
cd backend/scripts
.\.venv\Scripts\Activate.ps1  # Activar entorno virtual
cd ..
python manage.py runserver 0.0.0.0:8000
```

### **Iniciar Frontend:**
```bash
cd frontend-react
npm start
```

### **Sincronizar nuevos PDFs:**
```bash
cd backend
python manage.py sync_drive_full --chunk-size 600 --chunk-overlap 60
```

---

## 🔧 Comandos Útiles

### **Gestión de Base de Datos:**
```bash
# Crear/resetear base de datos
python manage.py initdb --admin-user root --admin-password tu_password

# Aplicar migraciones
python manage.py migrate

# Crear superusuario Django
python manage.py createsuperuser
```

### **Gestión de Documentos:**
```bash
# Sincronización completa desde Drive
python manage.py sync_drive_full --chunk-size 600 --chunk-overlap 60

# Forzar re-descarga de todos los PDFs
python manage.py sync_drive_full --force
```

---

## 🛠️ Solución de Problemas Comunes

### **Error: "Access denied for user 'rag_user'"**
```bash
# Recrear usuario de base de datos
python manage.py initdb --admin-user root --admin-password tu_password_mysql
```

### **Error: "Authentication credentials were not provided"**
- El problema se solucionó automáticamente en el código

### **Error: "SERVICE_ACCOUNT_FILE not found"**
- Verificar que la ruta en `bootstrap_rag.ps1` sea correcta
- Verificar que el archivo JSON existe y tiene permisos de lectura

### **Frontend no se conecta al Backend**
- Verificar que el backend esté ejecutándose en `http://localhost:8000`
- Verificar configuración CORS en Django settings

---

## 📁 Estructura del Proyecto

```
rag-asistente/
├── backend/                 # API Django
│   ├── api/                # App principal
│   ├── core/               # Configuración Django
│   ├── scripts/            # Scripts de bootstrap
│   └── manage.py           # Comando Django
├── frontend-react/         # Interfaz React
│   ├── src/                # Código fuente React
│   └── package.json        # Dependencias npm
├── data/                   # Datos y archivos procesados
│   ├── pdfs/              # PDFs descargados
│   └── texts/             # Textos extraídos
└── chroma_db/             # Base de datos vectorial
```

---

## 🔒 Seguridad

- Las credenciales se manejan por variables de entorno
- La autenticación usa JWT tokens
- Todos los datos se procesan localmente
- No se envía información a servicios externos (excepto Google Drive para descarga)

---
