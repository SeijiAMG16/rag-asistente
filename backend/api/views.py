import logging
import time
import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import Conversation, Message

# Configura el logger para registrar eventos importantes del sistema
logger = logging.getLogger(__name__)

# Variable para saber si la autenticación es obligatoria (por variable de entorno)
AUTH_REQUIRED = os.environ.get("AUTH_REQUIRED", "true").lower() == "true"

def _perm():
    """
    Devuelve los permisos requeridos para los endpoints.
    Si AUTH_REQUIRED es True, exige autenticación; si no, permite acceso libre.
    """
    return [IsAuthenticated] if AUTH_REQUIRED else [AllowAny]

@api_view(["POST"])
@permission_classes([AllowAny])  # El registro de usuarios es público
def register_view(request):
    """
    Permite registrar nuevos usuarios.
    Recibe username, email y password.
    Valida que no existan duplicados y crea el usuario.
    """
    try:
        data = request.data
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        # Validaciones básicas
        if not username or not email or not password:
            return Response({"error": "Todos los campos son requeridos"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"error": "El usuario ya existe"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({"error": "El email ya está registrado"}, status=status.HTTP_400_BAD_REQUEST)

        # Crea el usuario en la base de datos
        user = User.objects.create_user(username=username, email=email, password=password)

        # Log de registro exitoso
        logger.info("user_registered", extra={
            "event": "user_registered",
            "user_id": user.id,
            "username": username,
            "email": email,
            "route": "/register",
            "status_code": 201,
        })

        return Response({"message": "Usuario creado exitosamente"}, status=status.HTTP_201_CREATED)

    except Exception as e:
        # Log de error en registro
        logger.error("registration_failed", extra={
            "event": "registration_failed",
            "error": str(e),
            "route": "/register",
            "status_code": 500,
        })
        return Response({"error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
@permission_classes([AllowAny])
def health_view(_request):
    """
    Endpoint para verificar que el backend está activo.
    Retorna {"status": "ok"} si todo funciona.
    """
    return Response({"status": "ok"}, status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes(_perm())
def query_view(request):
    """
    Recibe una pregunta y responde usando la lógica RAG.
    - Busca fragmentos relevantes en ChromaDB.
    - Genera respuesta y la guarda en el historial de chat.
    """
    t0 = time.time()
    body = request.data or {}
    question = (body.get("question") or body.get("message") or "").strip()
    top_k = int(body.get("top_k", 5)) #usa los 5 más relevantes por defecto
    conversation_id = body.get("conversation_id")
    query_id = body.get("query_id")

    if not question:
        return Response({"error": "La pregunta es requerida"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Busca o crea la conversación
        conv = None
        if conversation_id:
            conv = Conversation.objects.filter(id=conversation_id, user=request.user if AUTH_REQUIRED else None).first()
        if conv is None:
            conv = Conversation.objects.create(
                user=request.user if AUTH_REQUIRED and request.user.is_authenticated else None,
                title=(question[:50] + "...") if len(question) > 50 else question
            )
        # Guarda el mensaje del usuario en el historial
        Message.objects.create(conversation=conv, sender='user', text=question)

        # Importa funciones RAG para buscar y generar respuesta
        from utils.rag_utils import (
            perform_semantic_search,
            generate_rag_response,
            clean_and_format_response,
        )
        # Busca los fragmentos más relevantes
        search_results = perform_semantic_search(question, top_k)
        sources = []
        for i, result in enumerate(search_results[:3]):
            sources.append({
                "title": result.get("archivo", f"Documento {i+1}"),
                "snippet": (result.get("texto", "")[:200] + "...") if len(result.get("texto", "")) > 200 else result.get("texto", ""),
                "page": result.get("chunk", i),
                "uri": f"#chunk-{result.get('chunk', i)}",
                "chunk_index": result.get("chunk", i),
                "metadata": result.get("metadata", {}),
            })
        # Genera la respuesta final
        answer_raw = generate_rag_response(question, search_results)
        answer = clean_and_format_response(answer_raw)
        # Guarda el mensaje del bot en el historial
        Message.objects.create(conversation=conv, sender='bot', text=answer)
    except Exception as e:
        # Log de error en consulta RAG
        logger.error("rag_query_failed", extra={
            "event": "rag_query_failed",
            "error": str(e),
            "question": question,
            "user_id": getattr(request.user, "id", None),
        })
        error_payload = {"error": "Error interno al procesar la consulta."}
        if getattr(settings, "DEBUG", False):
            error_payload["detail"] = str(e)
        return Response(error_payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    latency_ms = int((time.time() - t0) * 1000)
    # Log de consulta exitosa
    logger.info("query_completed", extra={
        "event": "query_completed",
        "user_id": getattr(request.user, "id", None),
        "query_id": query_id,
        "conversation_id": conversation_id,
        "latency_ms": latency_ms,
        "top_k": top_k,
        "num_sources": len(sources),
        "question_length": len(question),
        "results_found": len(search_results),
        "route": "/query",
        "status_code": 200,
    })

    # Retorna la respuesta y metadatos
    return Response({
        "answer": answer,
        "message": answer,
        "response": answer,
        "sources": sources,
        "resultados": search_results,
        "conversation_id": conv.id if 'conv' in locals() and conv else conversation_id,
        "metadata": {
            "query_time_ms": latency_ms,
            "sources_found": len(sources),
            "total_results": len(search_results),
            "top_k_requested": top_k,
            "chroma_db_used": True,
        },
    }, status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes(_perm())
def ingest_view(request):
    """
    Permite ingerir documentos de texto (.txt) en el sistema RAG.
    Fragmenta el texto, genera embeddings y los guarda en ChromaDB.
    """
    import os
    from sentence_transformers import SentenceTransformer
    import chromadb

    try:
        # Define rutas de carpetas
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        text_dir = os.path.join(project_root, "data", "texts")
        chroma_dir = os.environ.get("CHROMA_DIR") or os.path.join(project_root, "chroma_db")

        # Configuración de fragmentación
        CHUNK_SIZE = int(request.data.get("chunk_size", 500))
        CHUNK_OVERLAP = int(request.data.get("chunk_overlap", 50))

        # Inicializa cliente ChromaDB y modelo de embeddings
        client = chromadb.PersistentClient(path=chroma_dir)
        collection = client.get_or_create_collection("documents")
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

        files_processed = []
        # Procesa cada archivo .txt
        for filename in os.listdir(text_dir):
            if not filename.lower().endswith(".txt"):
                continue
            file_path = os.path.join(text_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                full_text = f.read()

            # Fragmenta el texto en chunks
            chunks = []
            start = 0
            while start < len(full_text):
                end = min(start + CHUNK_SIZE, len(full_text))
                chunk = full_text[start:end]
                chunks.append(chunk)
                start += CHUNK_SIZE - CHUNK_OVERLAP

            # Genera embeddings y los guarda en ChromaDB
            for idx, chunk in enumerate(chunks):
                chunk_id = f"{filename}_{idx}"
                embedding = model.encode(chunk).tolist() # Cada chunk de texto se convierte en un embedding
                metadata = {
                    "filename": filename,
                    "chunk_index": idx,
                    "text": chunk,
                }
                collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    documents=[chunk],
                )
            files_processed.append({"file": filename, "chunks": len(chunks)})

        # Retorna resumen de archivos procesados
        return Response({
            "status": "ok",
            "processed": files_processed,
            "collection_count": collection.count() if hasattr(collection, "count") else None,
        })
    except Exception as e:
        # Log de error en ingesta
        logger.error("ingest_failed", extra={
            "event": "ingest_failed",
            "error": str(e),
            "route": "/ingest",
            "status_code": 500,
        })
        return Response(
            {"error": "Error durante la ingesta", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["POST"])
@permission_classes(_perm())
def sync_drive_view(request):
    """
    Descarga PDFs desde Google Drive a la carpeta local.
    Solo descarga si no existen localmente.
    """
    # --- Sincronización de PDFs desde Google Drive ---
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
        from google.oauth2 import service_account
        import io

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pdf_dir = os.path.join(project_root, "data", "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)

        # Obtiene credenciales y carpeta de Drive
        service_account_file = os.environ.get("SERVICE_ACCOUNT_FILE") or os.path.join(project_root, "credentials.json")
        drive_folder_id = os.environ.get("DRIVE_FOLDER_ID") or None
        if not drive_folder_id:
            return Response({"error": "Falta DRIVE_FOLDER_ID"}, status=status.HTTP_400_BAD_REQUEST)
        if not os.path.exists(service_account_file):
            return Response({"error": "No se encontró SERVICE_ACCOUNT_FILE", "path": service_account_file}, status=status.HTTP_400_BAD_REQUEST)

        scopes = ['https://www.googleapis.com/auth/drive.readonly']
        creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
        service = build('drive', 'v3', credentials=creds)

        # Busca PDFs en la carpeta de Drive
        query = f"'{drive_folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(q=query, pageSize=1000, fields="files(id, name)").execute()
        files = results.get('files', [])

        downloaded = []
        skipped = []
        for f in files:
            file_id = f['id']
            file_name = f['name']
            local_path = os.path.join(pdf_dir, file_name)
            if os.path.exists(local_path):
                skipped.append(file_name)
                continue
            # Descarga el PDF
            req = service.files().get_media(fileId=file_id)
            with io.FileIO(local_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, req)
                done = False
                while not done:
                    status_dl, done = downloader.next_chunk()
            downloaded.append(file_name)

        # Retorna resumen de PDFs descargados y omitidos
        return Response({
            "status": "ok",
            "downloaded": downloaded,
            "skipped": skipped,
            "pdf_dir": pdf_dir,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        # Log de error en sync
        logger.error("sync_drive_failed", extra={
            "event": "sync_drive_failed",
            "error": str(e),
            "route": "/sync-drive",
            "status_code": 500,
        })
        return Response({"error": "Error al sincronizar Drive", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@permission_classes(_perm())
def ingest_upload_view(request):
    """
    Permite subir un PDF desde el frontend, extraer su texto y agregarlo a ChromaDB.
    El archivo se guarda en data/pdfs y el texto en data/texts.
    """
    try:
        import pdfplumber
        from sentence_transformers import SentenceTransformer
        import chromadb
        import uuid

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pdf_dir = os.path.join(project_root, "data", "pdfs")
        text_dir = os.path.join(project_root, "data", "texts")
        chroma_dir = os.environ.get("CHROMA_DIR") or os.path.join(project_root, "chroma_db")
        os.makedirs(pdf_dir, exist_ok=True)
        os.makedirs(text_dir, exist_ok=True)

        # Verifica que se haya subido un archivo PDF
        if 'file' not in request.FILES:
            return Response({"error": "Falta el archivo PDF (campo 'file')"}, status=status.HTTP_400_BAD_REQUEST)
        up = request.FILES['file']
        if not up.name.lower().endswith('.pdf'):
            return Response({"error": "El archivo debe ser PDF"}, status=status.HTTP_400_BAD_REQUEST)

        # Guarda el PDF en la carpeta local
        safe_name = up.name.replace(' ', '_')
        pdf_path = os.path.join(pdf_dir, safe_name)
        with open(pdf_path, 'wb') as f:
            for chunk in up.chunks():
                f.write(chunk)

        # Extrae el texto del PDF y lo guarda como .txt
        txt_filename = os.path.splitext(safe_name)[0] + '.txt'
        txt_path = os.path.join(text_dir, txt_filename)
        text = ''
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        with open(txt_path, 'w', encoding='utf-8') as tf:
            tf.write(text)

        # Fragmenta el texto y lo ingesta en ChromaDB
        CHUNK_SIZE = int(request.data.get("chunk_size", 500))
        CHUNK_OVERLAP = int(request.data.get("chunk_overlap", 50))
        client = chromadb.PersistentClient(path=chroma_dir)
        collection = client.get_or_create_collection("documents") #Se usa la colección "documents" para almacenar los embeddings y metadatos de cada chunk.

        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            chunks.append(text[start:end])
            start += CHUNK_SIZE - CHUNK_OVERLAP

        added = 0
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{txt_filename}_{idx}_{uuid.uuid4().hex[:8]}" # ID único para cada chunk
            embedding = model.encode(chunk).tolist() # El embedding generado por MiniLM
            metadata = {"filename": txt_filename, "chunk_index": idx, "text": chunk} #Metadatos (nombre de archivo, índice de chunk, texto original)
            collection.add(ids=[chunk_id], embeddings=[embedding], metadatas=[metadata], documents=[chunk])
            added += 1

        # Retorna resumen de la ingesta
        return Response({
            "status": "ok",
            "pdf": safe_name,
            "text_file": txt_filename,
            "chunks_added": added,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        # Log de error en ingesta por upload
        logger.error("ingest_upload_failed", extra={"event":"ingest_upload_failed","error":str(e)})
        return Response({"error":"Error al subir/ingerir PDF","detail":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@permission_classes(_perm())
def sync_drive_full_view(request):
    """
    Sincroniza PDFs desde Drive, extrae texto y los ingesta en ChromaDB en un solo paso.
    Descarga, extrae y fragmenta cada PDF, eliminando embeddings previos del mismo archivo.
    """
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
        from google.oauth2 import service_account
        import io
        import pdfplumber
        from sentence_transformers import SentenceTransformer
        import chromadb

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pdf_dir = os.path.join(project_root, "data", "pdfs")
        text_dir = os.path.join(project_root, "data", "texts")
        chroma_dir = os.environ.get("CHROMA_DIR") or os.path.join(project_root, "chroma_db")
        os.makedirs(pdf_dir, exist_ok=True)
        os.makedirs(text_dir, exist_ok=True)

        # Obtiene credenciales y carpeta de Drive
        service_account_file = os.environ.get("SERVICE_ACCOUNT_FILE") or os.path.join(project_root, "credentials.json")
        drive_folder_id = os.environ.get("DRIVE_FOLDER_ID") or None
        if not drive_folder_id:
            return Response({"error": "Falta DRIVE_FOLDER_ID"}, status=status.HTTP_400_BAD_REQUEST)
        if not os.path.exists(service_account_file):
            return Response({"error": "No se encontró SERVICE_ACCOUNT_FILE", "path": service_account_file}, status=status.HTTP_400_BAD_REQUEST)

        scopes = ['https://www.googleapis.com/auth/drive.readonly']
        creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
        service = build('drive', 'v3', credentials=creds)

        # Busca PDFs en la carpeta de Drive
        query = f"'{drive_folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(q=query, pageSize=1000, fields="files(id, name, modifiedTime)").execute()
        files = results.get('files', [])

        # Inicializa ChromaDB y modelo de embeddings
        client = chromadb.PersistentClient(path=chroma_dir)
        collection = client.get_or_create_collection("documents")
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

        CHUNK_SIZE = int(request.data.get("chunk_size", 500))
        CHUNK_OVERLAP = int(request.data.get("chunk_overlap", 50))
        force = str(request.data.get("force", "false")).lower() == "true"

        downloaded = []
        skipped = []
        ingested = []
        for f in files:
            file_id = f['id']
            file_name = f['name']
            local_path = os.path.join(pdf_dir, file_name)
            needs_download = force or (not os.path.exists(local_path))
            if needs_download:
                # Descarga el PDF
                req = service.files().get_media(fileId=file_id)
                with io.FileIO(local_path, 'wb') as fh:
                    downloader = MediaIoBaseDownload(fh, req)
                    done = False
                    while not done:
                        status_dl, done = downloader.next_chunk()
                downloaded.append(file_name)
            else:
                skipped.append(file_name)

            # Extrae el texto y lo guarda como .txt
            txt_filename = os.path.splitext(file_name)[0] + '.txt'
            txt_path = os.path.join(text_dir, txt_filename)
            try:
                text = ''
                with pdfplumber.open(local_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + '\n'
                with open(txt_path, 'w', encoding='utf-8') as tf:
                    tf.write(text)

                # Fragmenta el texto y lo ingesta en ChromaDB
                chunks = []
                start = 0
                while start < len(text):
                    end = min(start + CHUNK_SIZE, len(text))
                    chunks.append(text[start:end])
                    start += CHUNK_SIZE - CHUNK_OVERLAP

                # Elimina embeddings previos del mismo archivo
                try:
                    collection.delete(where={"filename": txt_filename})
                except Exception:
                    pass

                for idx, chunk in enumerate(chunks):
                    embedding = model.encode(chunk).tolist()
                    metadata = {"filename": txt_filename, "chunk_index": idx, "text": chunk}
                    chunk_id = f"{txt_filename}_{idx}"
                    collection.add(ids=[chunk_id], embeddings=[embedding], metadatas=[metadata], documents=[chunk])
                ingested.append({"file": file_name, "chunks": len(chunks)})
            except Exception as e:
                logger.error("drive_ingest_failed", extra={"file": file_name, "error": str(e)})

        # Retorna resumen de PDFs descargados, omitidos e ingeridos
        return Response({
            "status": "ok",
            "downloaded": downloaded,
            "skipped": skipped,
            "ingested": ingested,
            "pdf_dir": pdf_dir,
            "text_dir": text_dir,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        # Log de error en sync+ingest
        logger.error("sync_drive_full_failed", extra={"error": str(e)})
        return Response({"error": "Error en Sync+Ingest Drive", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
@permission_classes(_perm())
def conversations_view(request):
    """
    Devuelve la lista de conversaciones del usuario (o todas si no hay auth).
    """
    qs = Conversation.objects.all()
    if AUTH_REQUIRED:
        qs = qs.filter(user=request.user)
    data = [{
        "id": c.id,
        "title": c.title,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    } for c in qs]
    return Response({"conversations": data})

@api_view(["GET"])
@permission_classes(_perm())
def messages_view(request, conv_id: int):
    """
    Devuelve todos los mensajes de una conversación específica.
    Solo permite acceso si el usuario es dueño de la conversación.
    """
    try:
        conv = Conversation.objects.get(id=conv_id)
        if AUTH_REQUIRED and conv.user_id != getattr(request.user, 'id', None):
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)
        msgs = conv.messages.all()
        data = [{
            "id": m.id,
            "sender": m.sender,
            "text": m.text,
            "created_at": m.created_at,
        } for m in msgs]
        return Response({"messages": data, "conversation": {"id": conv.id, "title": conv.title}})
    except Conversation.DoesNotExist:
        return Response({"error": "Conversación no encontrada"}, status=status.HTTP_404_NOT_FOUND)