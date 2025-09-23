import os
import chromadb
from chromadb.config import Settings

# Usar la misma ruta de ChromaDB que el proyecto original
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DIR = os.environ.get("CHROMA_DIR") or os.path.join(PROJECT_ROOT, "chroma_db")
COLLECTION_NAME = "documents"  # Usar el mismo nombre que en scripts/

_client = None
_collection = None

def get_client():
    """
    Obtiene el cliente de ChromaDB usando la base de datos existente
    Mantiene compatibilidad con los datos ya procesados en scripts/
    """
    global _client
    if _client is None:
        # Usar PersistentClient como en scripts/api.py para mantener compatibilidad
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _client

def get_collection():
    """
    Obtiene la colección de documentos existente
    Usa la misma colección "documents" que ya fue creada por scripts/ingest.py
    """
    global _collection
    if _collection is None:
        client = get_client()
        try:
            # Intentar obtener la colección existente
            _collection = client.get_collection(COLLECTION_NAME)
        except Exception:
            # Si no existe, crearla (aunque debería existir si ya se procesaron documentos)
            _collection = client.get_or_create_collection(
                COLLECTION_NAME, 
                metadata={"hnsw:space": "cosine"}
            )
    return _collection

def knn_search(query_embedding, top_k=3):
    """
    Realizar búsqueda de k-vecinos más cercanos en la base vectorial
    Compatible con la estructura de datos existente
    """
    col = get_collection()
    res = col.query(
        query_embeddings=[query_embedding], 
        n_results=top_k, 
        include=["documents", "metadatas", "distances"]
    )
    return res
