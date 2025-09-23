import os
import re
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer
import chromadb
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# --- Paths ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

# --- ChromaDB ---
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_collection("documents")

# --- Embeddings model ---
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# --- LLM generativo ---
LLM_MODEL = "Qwen/Qwen1.5-1.8B-Chat"
tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
llm = AutoModelForCausalLM.from_pretrained(LLM_MODEL)
generator = pipeline("text-generation", model=llm, tokenizer=tokenizer, max_new_tokens=240)

# --- FastAPI ---
app = FastAPI(title="RAG Asistente API + LLM")

class SearchResult(BaseModel):
    archivo: str
    chunk: int
    texto: str

class QueryResponse(BaseModel):
    respuesta: str
    resultados: List[SearchResult]

@app.get("/buscar", response_model=QueryResponse)
def buscar(query: str = Query(..., description="Consulta en español")):
    embedding = model.encode(query).tolist()
    results = collection.query(
        query_embeddings=[embedding],
        n_results=5,
        include=["metadatas", "documents"]
    )

    encontrados = []
    contexto = ""
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        encontrados.append(SearchResult(
            archivo=meta["filename"],
            chunk=meta["chunk_index"],
            texto=doc
        ))
        contexto += doc + "\n---\n"

    # PROMPT claro y directo
    prompt = (
        f"Responde la pregunta solo usando la información relevante de los siguientes fragmentos.\n"
        f"Evita respuestas largas, que sean cortas. No mayor a 140 palabras."
        f"Pregunta: {query}\n"
        f"Fragmentos:\n{contexto}\n"
        "Respuesta:"
    )

    # Genera la respuesta
    respuesta_raw = generator(prompt)[0]["generated_text"].split("Respuesta:")[-1].strip()

    # Limpiar posibles restos de instrucción o etiquetas
    respuesta = re.sub(
        r"(Instrucción.*|<usuario>|<asistente>|<\w+>|</\w+>).*", 
        '', 
        respuesta_raw, 
        flags=re.IGNORECASE
    ).strip()

    return QueryResponse(respuesta=respuesta, resultados=encontrados)