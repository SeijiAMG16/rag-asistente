# 🚀 Pipeline ETL para Sistema RAG

## Descripción General

Este pipeline automatiza la extracción, transformación y carga (ETL) de documentos desde Google Drive hacia un sistema RAG (Retrieval-Augmented Generation) usando ChromaDB como base de datos vectorial.

## 📋 Funcionalidades

### ✅ Lo que hace el pipeline:

1. **📥 Descarga automática de Google Drive**
   - Conecta a tu carpeta de Google Drive usando `credentials.json`
   - Descarga PDFs, documentos de Google Docs, archivos de texto
   - Maneja múltiples tipos de archivos automáticamente

2. **📄 Extracción de texto inteligente**
   - Extrae texto de PDFs usando `pdfplumber` y `PyPDF2`
   - Procesa documentos DOCX
   - Maneja archivos de texto plano
   - Limpia y normaliza el texto extraído

3. **🧠 Ingesta a base de datos vectorial**
   - Genera embeddings usando modelos optimizados para español
   - Divide documentos en chunks inteligentes
   - Almacena en ChromaDB con metadata completa
   - Permite búsquedas semánticas eficientes

## 🗂️ Estructura de Archivos

```
rag-asistente/
├── credentials.json          # Credenciales de Google Drive
├── config.py                # Configuración central
├── run_etl.ps1              # Script PowerShell para Windows
├── data/                    # Datos procesados
│   ├── pdfs/               # Documentos descargados
│   └── texts/              # Textos extraídos
├── chroma_db/              # Base de datos vectorial
└── scripts/
    ├── etl_drive.py        # ETL de Google Drive
    ├── ingest_chromadb.py  # Ingesta a ChromaDB
    ├── query.py            # Sistema de consultas
    └── run_pipeline.py     # Pipeline completo
```

## 🔧 Configuración

### 1. Credenciales de Google Drive

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto o selecciona uno existente
3. Habilita las APIs:
   - Google Drive API
   - Google Docs API
4. Crea credenciales de cuenta de servicio
5. Descarga el archivo JSON como `credentials.json`
6. Comparte tu carpeta de Google Drive con el email de la cuenta de servicio

### 2. Configuración del proyecto

El archivo `config.py` contiene toda la configuración:

```python
# ID de tu carpeta de Google Drive
DRIVE_FOLDER_ID = "1wAYnaln3Dg-MnFy6rNhwqPlh7Ouc4EP8"

# Modelo de embeddings (optimizado para español)
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Configuración de chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
```

## 🚀 Ejecución

### Opción 1: Script automático (Recomendado)

```powershell
# En Windows PowerShell
.\run_etl.ps1
```

### Opción 2: Paso a paso

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Cambiar a directorio scripts
cd scripts

# 3. Ejecutar ETL de Google Drive
python etl_drive.py

# 4. Ingestar a ChromaDB
python ingest_chromadb.py
```

### Opción 3: Pipeline completo

```bash
cd scripts
python run_pipeline.py
```

## 📊 Monitoreo y Logs

El sistema proporciona logs detallados:

```
🚀 Configurando base de datos MySQL para RAG Asistente
==================================================
✅ Base de datos 'rag' creada o ya existe
📥 Encontrados 15 archivos en Google Drive
📄 Descargando: documento1.pdf
📄 Descargando: manual_usuario.docx
🧠 Procesando 15 documentos...
✅ Creados 247 chunks para ingesta
🎉 Pipeline completado exitosamente!
```

## 🔍 Sistema de Consultas

### Consulta interactiva

```bash
cd scripts
python query.py
```

### Consulta directa

```bash
python query.py "¿Cómo configurar el sistema?"
```

### Ejemplo de uso

```python
from scripts.query import RAGQuery

rag = RAGQuery()
results = rag.search("configuración de base de datos")
rag.format_results(results, "configuración de base de datos")
```

## 📈 Estadísticas del Sistema

El pipeline proporciona métricas completas:

- **Archivos procesados**: Total de documentos descargados
- **Chunks generados**: Fragmentos de texto para búsqueda
- **Tiempo de procesamiento**: Duración de cada etapa
- **Tamaño de la base vectorial**: Cantidad de embeddings almacenados

## 🔧 Personalización

### Cambiar modelo de embeddings

```python
# En config.py
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Inglés
# o
EMBEDDING_MODEL = "hiiamsid/sentence_similarity_spanish_es"  # Español
```

### Ajustar chunking

```python
# En config.py
CHUNK_SIZE = 500      # Chunks más pequeños
CHUNK_OVERLAP = 50    # Menos solapamiento
```

### Filtros de archivos

```python
# En config.py
SUPPORTED_MIME_TYPES = {
    'application/pdf': '.pdf',
    'text/plain': '.txt'
    # Remover otros tipos si no los necesitas
}
```

## 🐛 Solución de Problemas

### Error de autenticación Google Drive
```
Error: Archivo de credenciales no encontrado
```
**Solución**: Verifica que `credentials.json` esté en la raíz del proyecto

### Error de permisos Google Drive
```
Error: 403 Forbidden
```
**Solución**: Comparte la carpeta de Drive con el email de la cuenta de servicio

### Error de dependencias
```
Import "sentence_transformers" could not be resolved
```
**Solución**: Ejecuta `pip install -r requirements.txt`

### Base de datos vacía
```
Colección 'rag_documents' no encontrada
```
**Solución**: Ejecuta primero el ETL completo

## 📚 Dependencias Principales

- **Google APIs**: `google-api-python-client`, `google-auth`
- **Procesamiento de documentos**: `pdfplumber`, `python-docx`, `PyPDF2`
- **Embeddings**: `sentence-transformers`, `transformers`
- **Base vectorial**: `chromadb`
- **Utilidades**: `tqdm`, `python-dotenv`

## 🔄 Flujo de Trabajo Completo

1. **📥 Extracción**: Descarga archivos de Google Drive
2. **🔄 Transformación**: Extrae y limpia texto de documentos
3. **📊 Chunking**: Divide texto en fragmentos manejables
4. **🧠 Embeddings**: Genera representaciones vectoriales
5. **💾 Carga**: Almacena en ChromaDB con metadata
6. **🔍 Consulta**: Sistema de búsqueda semántica listo

¡Tu sistema RAG está completamente configurado y listo para usar! 🎉