import os
from sentence_transformers import SentenceTransformer
import chromadb

# --- Configuración de paths ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT_DIR = os.path.join(PROJECT_ROOT, "data", "texts")
CHROMA_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

# --- Configuración de chunking ---
CHUNK_SIZE = 500    # Número de caracteres por chunk
CHUNK_OVERLAP = 50  # Solapamiento entre chunks

# --- Inicializa ChromaDB persistente (nueva API) ---
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection("documents")

# --- Modelo de embeddings para español ---
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# --- Procesa los archivos .txt ---
for filename in os.listdir(TEXT_DIR):
    if filename.endswith('.txt'):
        file_path = os.path.join(TEXT_DIR, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            full_text = f.read()

        # Chunking manual
        chunks = []
        start = 0
        while start < len(full_text):
            end = min(start + CHUNK_SIZE, len(full_text))
            chunk = full_text[start:end]
            chunks.append(chunk)
            start += CHUNK_SIZE - CHUNK_OVERLAP

        # Embeddings e inserción en ChromaDB
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{filename}_{idx}"
            embedding = model.encode(chunk).tolist()
            metadata = {
                "filename": filename,
                "chunk_index": idx,
                "text": chunk
            }
            collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[chunk]
            )
        print(f"Ingresado: {filename} ({len(chunks)} chunks)")

print("¡Ingesta a ChromaDB completada!")