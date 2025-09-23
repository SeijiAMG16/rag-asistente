"""
Módulo de utilidades RAG para integrar la lógica existente del proyecto
Mantiene compatibilidad con scripts/api.py y scripts/query.py
"""
import os
import re
import logging
from typing import List, Dict, Any

# Configuración de logging
logger = logging.getLogger(__name__)

# --- Configuración opcional de LLM para respuestas generativas ---
# Activar con variable de entorno USE_LLM=true
USE_LLM = os.environ.get("USE_LLM", "false").lower() == "true"
LLM_MODEL = os.environ.get("LLM_MODEL", "Qwen/Qwen1.5-1.8B-Chat")
LLM_MAX_NEW_TOKENS = int(os.environ.get("LLM_MAX_NEW_TOKENS", "240"))
_LLM_PIPELINE = None  # caché del pipeline de generación

def _get_llm_pipeline():
    """Inicializa perezosamente el pipeline de generación de texto."""
    global _LLM_PIPELINE
    if _LLM_PIPELINE is not None:
        return _LLM_PIPELINE
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
        model = AutoModelForCausalLM.from_pretrained(LLM_MODEL)
        _LLM_PIPELINE = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=LLM_MAX_NEW_TOKENS,
        )
        logger.info(f"LLM pipeline inicializado: {LLM_MODEL}")
    except Exception as e:
        logger.error(f"No se pudo inicializar el LLM ({LLM_MODEL}): {e}")
        _LLM_PIPELINE = None
    return _LLM_PIPELINE

def get_project_root():
    """Obtiene la ruta raíz del proyecto para ubicar carpetas importantes como chroma_db/"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def initialize_rag_components():
    """
    Inicializa todos los componentes RAG necesarios
    Retorna modelo de embeddings, cliente ChromaDB y colección
    """
    try:
        from sentence_transformers import SentenceTransformer
        import chromadb

        # Paths del proyecto original
        PROJECT_ROOT = get_project_root()
        CHROMA_DIR = os.environ.get("CHROMA_DIR") or os.path.join(PROJECT_ROOT, "chroma_db")

        # Modelo de embeddings (el mismo usado en scripts/)
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

        # Cliente ChromaDB persistente
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        # Ensure collection exists
        try:
            collection = client.get_collection("documents")
        except Exception:
            collection = client.get_or_create_collection("documents")

        logger.info(f"RAG components initialized successfully. ChromaDB path: {CHROMA_DIR}")
        return model, client, collection

    except Exception as e:
        logger.error(f"Error initializing RAG components: {str(e)}")
        raise

def perform_semantic_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    busca los fragmentos más relevantes en la base vectorial 
    """
    try:
        model, client, collection = initialize_rag_components()

        # If collection is empty, short-circuit
        try:
            count = collection.count() if hasattr(collection, "count") else None
            if count is not None and count == 0:
                logger.warning("Chroma collection 'documents' is empty; returning no results")
                return []
        except Exception:
            # If count fails, continue and let query handle errors
            pass
        
        # Generar embedding de la consulta
        embedding = model.encode(query).tolist()
        
        # Búsqueda en ChromaDB
        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["metadatas", "documents", "distances"]
        )
        
        # Formatear resultados
        formatted_results = []
        if results["documents"] and len(results["documents"][0]) > 0:
            for i, (doc, meta, distance) in enumerate(zip(
                results["documents"][0], 
                results["metadatas"][0], 
                results["distances"][0]
            )):
                formatted_results.append({
                    "texto": doc,
                    "archivo": meta.get("filename", f"Documento {i+1}"),
                    "chunk": meta.get("chunk_index", i),
                    "similarity_score": round(1 - distance, 3),
                    "metadata": meta
                })
        
        logger.info(f"Semantic search completed. Query: '{query}', Results: {len(formatted_results)}")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}")
        return []

def generate_rag_response(query: str, search_results: List[Dict[str, Any]]) -> str:
    """
    Genera respuesta RAG usando el contexto de documentos encontrados.
    Si USE_LLM=true, utiliza un LLM para redactar la respuesta; si no, usa un formato resumido.
    """
    if not search_results:
        return (
            "Lo siento, no pude encontrar información relevante en los documentos "
            "para responder tu pregunta. Te recomiendo verificar que los documentos "
            "contengan información sobre el tema consultado."
        )

    try:
        # Construye el contexto con los 3 chunks más relevantes
        top_chunks = search_results[:3]
        contexto = "\n---\n".join([r["texto"] for r in top_chunks])

        if USE_LLM:
            generator = _get_llm_pipeline()
            if generator is not None:
                prompt = (
                    "Eres un asistente que responde en español de forma breve y precisa. "
                    "Responde solo usando la información de los fragmentos de contexto. "
                    "Si algo no está en el contexto, di que no hay suficiente información.\n\n"
                    f"Pregunta: {query}\n\n"
                    f"Contexto:\n{contexto}\n\n"
                    "Respuesta:"
                )
                try:
                    output = generator(prompt)[0]["generated_text"]
                    # Extrae lo posterior a "Respuesta:" si aparece
                    if "Respuesta:" in output:
                        output = output.split("Respuesta:", 1)[-1].strip()
                except Exception as gen_err:
                    logger.error(f"Fallo generación LLM: {gen_err}")
                    output = None
                if output:
                    logger.info("Respuesta generada con LLM")
                    return output
            # Si falla inicialización o generación, continúa con el modo no-LLM
            logger.warning("Fallo o desactivación del LLM; usando respuesta resumida.")

        # Modo sin LLM: construye una respuesta concisa con citas de fuentes
        response = "Basándome en los documentos analizados, encontré lo siguiente:\n\n"
        for i, result in enumerate(top_chunks, 1):
            snippet = result["texto"][:400] + "..." if len(result["texto"]) > 400 else result["texto"]
            response += f"[Fuente {i} - {result['archivo']}]:\n{snippet}\n\n"
        response += f"Se usaron {len(search_results)} fragmentos relevantes para esta respuesta."
        logger.info("Respuesta generada sin LLM")
        return response

    except Exception as e:
        logger.error(f"Error generating RAG response: {str(e)}")
        return "Error interno al generar la respuesta. Por favor intenta nuevamente."

def clean_and_format_response(response: str) -> str:
    """
    Limpia y formatea la respuesta generada
    Aplica las mismas reglas de limpieza que scripts/api.py
    """
    # Limpiar posibles restos de instrucción o etiquetas
    cleaned_response = re.sub(
        r"(Instrucción.*|<usuario>|<asistente>|<\w+>|</\w+>).*", 
        '', 
        response, 
        flags=re.IGNORECASE
    ).strip()
    
    # Limitar longitud de respuesta
    if len(cleaned_response) > 1000:
        cleaned_response = cleaned_response[:1000] + "..."
    
    return cleaned_response