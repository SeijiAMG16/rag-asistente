import os
from sentence_transformers import SentenceTransformer
import chromadb

# --- Configuración de paths ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

# --- Inicializa ChromaDB persistente (nueva API) ---
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_collection("documents")

# --- Usa el mismo modelo de embeddings que en la ingesta ---
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# --- Input del usuario ---
consulta = input("Escribe tu pregunta o frase de búsqueda en español:\n> ")

# --- Embedding de la consulta ---
embedding = model.encode(consulta).tolist()

# --- Recupera los 5 chunks más similares ---
results = collection.query(
    query_embeddings=[embedding],
    n_results=5,
    include=["metadatas", "documents"]
)

# --- Muestra resultados ---
print("\n--- Resultados encontrados ---")
for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
    print(f"\nResultado {i}:")
    print(f"Archivo: {meta['filename']}  |  Chunk: {meta['chunk_index']}")
    print("Texto:")
    print(doc[:500], "..." if len(doc) > 500 else "")
print("\n--- Fin de resultados ---")
