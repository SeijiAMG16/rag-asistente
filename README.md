# � RAG ASISTENTE - Sistema Autónomo Completo

Sistema de RAG (Retrieval-Augmented Generation) completamente autónomo que se configura automáticamente.

## ✨ Características Principales

- **🤖 Análisis Inteligente**: Integración con múltiples modelos LLM (Groq Llama 3.3-70B, OpenAI)
- **🛠️ Configuración Automática**: Sin scripts manuales, sin configuración compleja
- **💾 Base de Datos MySQL**: Configuración automática con usuarios predefinidos
- **🔒 Autenticación JWT**: Sistema completo de login/registro
- **📚 ChromaDB**: Vector database con 699+ documentos
- **🌐 API REST**: Endpoints completos para frontend

## 🎯 INICIO RÁPIDO (1 COMANDO)

### Opción 1: Usando PowerShell (Recomendado)
```powershell
cd backend
.\INICIAR_RAG.ps1
```

### Opción 2: Usando Python directamente  
```bash
cd backend
python start_rag.py
```

**¡ESO ES TODO!** 🎉

El sistema automáticamente:
- ✅ Instala todas las dependencias
- ✅ Configura MySQL (base de datos: `rag_asistente`)
- ✅ Ejecuta migraciones de Django
- ✅ Crea usuario administrador (`admin`/`admin123`)
- ✅ Inicia el servidor en `http://localhost:8000`

## 🔧 Requisitos Mínimos

- **Python 3.8+**
- **MySQL Server** (con usuario `root`/`sistemas`)
- **Windows/Linux/Mac**

## 📱 Usuarios Predefinidos

El sistema incluye usuarios de ejemplo:
- `admin` / `admin123` (Administrador)
- `testuser` / `password123`
- `usuario` / `password123`

## 🌐 Endpoints API

- `POST /api/register/` - Registro de usuarios
- `POST /api/login/` - Inicio de sesión  
- `POST /api/logout/` - Cerrar sesión
- `POST /api/chat/` - Chat con RAG
- `GET /api/me/` - Información del usuario

## 🧠 Sistema de Análisis

### Proveedores LLM (en orden de prioridad):
1. **Groq API** (Llama 3.3-70B) - Ultra rápido
2. **OpenAI API** (GPT-4) - Fallback inteligente
3. **Análisis Local** - Cuando no hay APIs

### Características Anti-Ambigüedad:
- Prompts especializados para consultas específicas
- Análisis contextual profundo
- Respuestas estructuradas y precisas
- Enfoque en documentos peruanos/locales

## 📂 Estructura del Proyecto

```
rag-asistente/
├── backend/               # Django Backend
│   ├── INICIAR_RAG.ps1   # 🚀 SCRIPT PRINCIPAL
│   ├── start_rag.py      # Script maestro Python
│   ├── manage.py         # Django management
│   ├── bootstrap/        # Auto-configuración
│   ├── api/             # REST API
│   ├── core/            # Configuración Django
│   └── utils/           # Utilidades RAG
├── frontend-react/       # Frontend React
├── chroma_db/           # Vector Database
└── scripts/             # Scripts auxiliares
```

## 🔥 Características Avanzadas

- **Auto-configuración**: Crea base de datos, usuario admin, migraciones
- **Multi-LLM**: Fallback automático entre proveedores
- **Vector Search**: ChromaDB con embeddings optimizados
- **CORS Habilitado**: Listo para frontend
- **JWT Tokens**: Autenticación robusta
- **Logs Detallados**: Seguimiento completo del sistema

## 🔍 Solución de Problemas

### Error: MySQL no conecta
```bash
# Verificar que MySQL esté ejecutándose
# Usuario: root, Password: sistemas
```

### Error: Dependencias faltantes
```bash
# El script instala automáticamente, pero si falla:
pip install -r requirements.txt
```

### Error: Puerto ocupado
```bash
# Django usa puerto 8000 por defecto
# Verificar que no haya otro proceso usando el puerto
```

## 🚀 Desarrollo

Para desarrollo avanzado:
```bash
cd backend
python manage.py shell          # Shell de Django
python manage.py createsuperuser # Crear admin manual
python manage.py collectstatic   # Archivos estáticos
```

## 🌟 Próximas Características

- [ ] Interfaz web administrativa
- [ ] Análisis de documentos PDF/DOCX
- [ ] API de subida de documentos
- [ ] Dashboard de métricas
- [ ] Exportación de conversaciones

---

**💡 Tip**: Para desarrollo frontend, usar `frontend-react/` con `npm start`

**🔧 Soporte**: El sistema detecta automáticamente la configuración y se adapta al entorno

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

### **Configurar Google Drive (Nueva PC):**
```powershell
# Windows - Configuración completa automática
.\SINCRONIZAR_DRIVE.ps1 -Setup

# Sincronización manual
.\SINCRONIZAR_DRIVE.ps1

# Daemon automático (cada 30 min)
.\SINCRONIZAR_DRIVE.ps1 -Daemon
```

```bash
# Linux/Mac - Comandos Django
python manage.py start_drive_sync --action setup
python manage.py start_drive_sync --action sync
python manage.py start_drive_sync --action status
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

# ETL local (sin Google Drive)
python etl_rag_complete.py --force
```

### **Google Drive Automation:**
```powershell
# Instalar dependencias de Drive
.\INSTALAR_GOOGLE_DRIVE.ps1

# Setup completo de Drive
.\SINCRONIZAR_DRIVE.ps1 -Setup

# Sincronización forzada
.\SINCRONIZAR_DRIVE.ps1 -Force

# Ver estado del sistema
.\SINCRONIZAR_DRIVE.ps1 -Status
```
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
