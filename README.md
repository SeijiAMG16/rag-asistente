# 📚 Asistente RAG Local (FastAPI + Streamlit + ChromaDB + Google Drive)

Asistente conversacional local para consultar tus propios documentos, combinando búsqueda semántica y modelos LLM ligeros, con opción de ingestión directa desde Google Drive.

1. sync_drive.py
2. extract_text.py
3. ingest.py
4. query.py (prueba del 3)
5. api.py

---

## 🚀 Características

- Recuperación inteligente de fragmentos relevantes de tus propios documentos.
- Soporte para ingestión de archivos `.txt` locales y extracción directa desde Google Drive (`.pdf`, `.docx`, etc.).
- Respuestas generadas con modelos LLM locales (sin depender de servicios pagos ni la nube).
- Interfaz web moderna, fácil de usar (Streamlit).
- Todo el procesamiento y almacenamiento se realiza localmente, sin enviar información sensible a terceros.

---

## 🖥️ Requisitos

- **Python 3.9+** (recomendado 3.10+)
- Recomendado: **tarjeta GPU** para mejor rendimiento con LLM (opcional)
- Acceso a Google Drive (para ingestión automática)
- Modelos se descargan automáticamente en primera ejecución

---

## 🛠️ Instalación

1. **Clona este repositorio**  

   ```bash
   git clone https://github.com/HugoX2003/rag-asistente
   cd rag-asistente
   ```

2. **Crea y activa un entorno virtual**

    ```bash
    python -m venv venv
    # En Windows
    venv\Scripts\activate
    # En Linux/macOS
    source venv/bin/activate
    ```

3. **Instala las dependencias**

    ```bash
    pip install -r requirements.txt
    ```

---

## 🛠️ Instalación

### Opción A: Procesar archivos locales `.txt`

- Coloca tus archivos `.txt` en `data/texts/`
- Ejecuta el ingestor:

    ```bash
    python scripts/ingest.py
    ```

### Opción B: Descargar y extraer desde Google Drive

1. Coloca tu `credentials.json` de Google en la raíz del proyecto.
2. Ejecuta:

    ```bash
    python scripts/sync_drive.py
    ```

- Se abrirá el navegador para autenticarte la primera vez.

3. Los archivos de Google Drive se descargarán y convertirán a `.txt` en `data/texts/`.
4. Ejecuta luego el ingestor:

    ```bash
    python scripts/ingest.py
    ```

## 🚀 Ejecuta la API y la interfaz web

### 1. Inicia la API (en una terminal)

```bash
    uvicorn scripts.api:app --reload
```

### 2. Inicia el frontend (en otra terminal)

```bash
    streamlit run frontend.py
```

- Accede a la interfaz web: http://localhost:8501

- Documentación interactiva de la API: http://localhost:8000/docs

## ✨ Personalización y sugerencias

- Cambia el modelo LLM en `api.py` según tus recursos.

- Puedes mejorar la visualización del frontend editando `frontend.py`.

- El sistema es 100% local, no depende de APIs pagas.
