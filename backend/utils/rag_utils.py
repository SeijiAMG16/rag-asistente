"""
Módulo de utilidades RAG para integrar la lógica existente del proyecto
Mantiene compatibilidad con scripts/api.py y scripts/query.py
Integra sistema de análisis inteligente para respuestas razonadas
"""
import os
import re
import sys
import logging
from typing import List, Dict, Any
from pathlib import Path

# Agregar el directorio raíz al path para importar el sistema de análisis
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

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

        # Usar ruta relativa que sabemos que funciona
        current_dir = Path(__file__).parent
        chroma_path = current_dir.parent.parent / "chroma_db_simple"
        
        # Modelo de embeddings mejorado (mismo que la base avanzada)
        model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

        # Cliente ChromaDB con ruta que funciona
        client = chromadb.PersistentClient(path=str(chroma_path))
        collection = client.get_collection("simple_rag_docs")
        
        count = collection.count()
        logger.info(f"RAG components initialized. ChromaDB: {chroma_path}, Docs: {count}")
        
        return model, client, collection

    except Exception as e:
        logger.error(f"Error initializing RAG components: {str(e)}")
        raise
        raise

def perform_semantic_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    busca los fragmentos más relevantes en la base vectorial 
    
    NUEVO: Sistema RAG optimizado con búsqueda híbrida y reranking
    """
    
    # Priorizar sistema optimizado si está disponible
    use_optimized = os.getenv("USE_OPTIMIZED_RAG", "true").lower() == "true"
    
    if use_optimized:
        try:
            from .optimized_rag_system import perform_optimized_search
            logger.info("🚀 Usando sistema RAG optimizado (híbrido + reranking)")
            return perform_optimized_search(query, top_k)
        except ImportError as e:
            logger.warning(f"⚠️ Sistema optimizado no disponible: {e}")
        except Exception as e:
            logger.error(f"❌ Error en sistema optimizado: {e}, fallback a sistema clásico")
    
    # Fallback al sistema mejorado
    use_enhanced = (
        os.getenv("USE_ENHANCED_RAG", "false").lower() == "true" or
        os.getenv("GROQ_API_KEY") or 
        os.getenv("TOGETHER_API_KEY") or
        os.getenv("OPENROUTER_API_KEY") or
        os.getenv("COHERE_API_KEY")
    )
    
    if use_enhanced:
        try:
            # Usar sistema RAG optimizado directamente
            from .optimized_rag_system import OptimizedRAGSystem
            logger.info("🚀 Usando sistema RAG optimizado (híbrido + reranking)")
            
            optimized_system = OptimizedRAGSystem()
            results = optimized_system.advanced_search(query, top_k=top_k)
            
            # Convertir formato para compatibilidad
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'texto': result['content'],
                    'archivo': result['source'],
                    'chunk': result.get('chunk_id', 'N/A'),
                    'similarity_score': result['score']
                })
            
            return formatted_results
            
        except ImportError:
            logger.warning("⚠️ Sistema optimizado no disponible, usando búsqueda clásica")
        except Exception as e:
            logger.error(f"❌ Error en sistema optimizado: {e}, fallback a búsqueda clásica")
    
    try:
        model, client, collection = initialize_rag_components()

        # Verificar si la colección tiene documentos
        try:
            count = collection.count()
            if count == 0:
                logger.warning("Colección 'simple_rag_docs' está vacía; no se pueden hacer búsquedas")
                return []
            logger.info(f"Realizando búsqueda en colección con {count} documentos")
        except Exception as e:
            logger.warning(f"No se pudo verificar el conteo de documentos: {e}")
            # Continuar con la búsqueda de todas formas
        
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
    Genera respuesta RAG usando modelos LLM potentes (DeepSeek V3).
    ANÁLISIS REAL y CONTEXTUAL - NO respuestas predeterminadas.
    Incluye fuentes y referencias específicas.
    
    PRIORIDAD: DeepSeek V3 via OpenRouter
    """
    if not search_results:
        return _generate_no_results_response(query)

    # PRIMERA PRIORIDAD: DeepSeek V3 via OpenRouter
    from dotenv import load_dotenv
    load_dotenv()
    
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        try:
            import requests
            import json
            
            # Preparar chunks para DeepSeek
            context_chunks = []
            for i, result in enumerate(search_results[:5], 1):
                chunk = f"[FUENTE {i}: {result['archivo']}]\n{result['texto']}"
                context_chunks.append(chunk)
            
            logger.info("🤖 Usando DeepSeek V3 para análisis académico")
            
            # Llamada directa a OpenRouter API con DeepSeek
            context_text = "\n\n".join(context_chunks)
            
            prompt = f"""Eres un asistente académico especializado en análisis de textos universitarios. 
Tu tarea es proporcionar respuestas precisas, detalladas y bien fundamentadas basándote en los documentos proporcionados.

CONTEXTO ACADÉMICO:
{context_text}

PREGUNTA DEL ESTUDIANTE:
{query}

INSTRUCCIONES:
- Proporciona una respuesta académica completa y detallada
- Cita específicamente los autores y años cuando sea relevante
- Incluye referencias directas a los textos
- Mantén un tono académico y profesional
- Si la información no está en el contexto, indícalo claramente

RESPUESTA:"""

            headers = {
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "RAG Academic Assistant"
            }
            
            data = {
                "model": "deepseek/deepseek-v3",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    deepseek_response = result['choices'][0]['message']['content']
                    logger.info(f"✅ DeepSeek V3 respuesta exitosa: {len(deepseek_response)} caracteres")
                    return deepseek_response
                
        except Exception as e:
            logger.error(f"❌ Error con DeepSeek: {e}, fallback a sistema básico")

    # FALLBACK: Sistema básico con contexto estructurado
    try:
        # Preparar contexto de los mejores resultados sin análisis LLM externo
        context_chunks = []
        sources_info = []
        
        for i, result in enumerate(search_results[:5], 1):  # Top 5 resultados más relevantes
            # Incluir metadatos para mayor contexto
            chunk_with_metadata = f"[FUENTE {i}: {result['archivo']}]\n{result['texto']}"
            context_chunks.append(chunk_with_metadata)
            
            # Preparar información de fuentes para el frontend
            sources_info.append({
                "numero": i,
                "archivo": result['archivo'],
                "chunk": result['chunk'],
                "similarity_score": result['similarity_score'],
                "texto_preview": result['texto'][:200] + "..." if len(result['texto']) > 200 else result['texto']
            })
        
        logger.info(f"Generando respuesta básica estructurada para: '{query[:50]}...' con {len(context_chunks)} chunks")
        
        # Generar respuesta básica estructurada (sin LLM externo)
        response = _generate_advanced_fallback_response(query, search_results)
        
        if response and len(response.strip()) > 50:  # Verificar que sea una respuesta sustantiva
            # Estructurar respuesta con fuentes
            structured_response = {
                "respuesta": clean_and_format_response(response),
                "fuentes": sources_info,
                "total_fuentes": len(sources_info),
                "query_procesada": query
            }
            
            logger.info(f"✅ Respuesta básica generada: {len(response)} caracteres con {len(sources_info)} fuentes")
            return structured_response
        else:
            logger.warning("⚠️ Respuesta básica insuficiente, usando fallback")
            return _generate_advanced_fallback_response_with_sources(query, search_results)
        
    except Exception as e:
        logger.error(f"❌ Error en sistema básico: {e}")
        return _generate_advanced_fallback_response_with_sources(query, search_results)
    except Exception as e:
        logger.error(f"❌ Error en análisis LLM: {str(e)}")
        return _generate_advanced_fallback_response_with_sources(query, search_results)

def _generate_no_results_response(query: str) -> str:
    """Respuesta cuando no se encuentran documentos relevantes"""
    return (
        f"No encontré información específica sobre '{query}' en los documentos disponibles. "
        f"Te sugiero reformular la pregunta o verificar que los documentos contengan "
        f"información relacionada con el tema consultado."
    )

def _generate_advanced_fallback_response_with_sources(query: str, search_results: List[Dict[str, Any]]) -> Dict:
    """
    Fallback avanzado que incluye fuentes estructuradas
    """
    # Generar respuesta fallback
    fallback_response = _generate_advanced_fallback_response(query, search_results)
    
    # Preparar información de fuentes
    sources_info = []
    for i, result in enumerate(search_results[:5], 1):
        sources_info.append({
            "numero": i,
            "archivo": result['archivo'],
            "chunk": result['chunk'],
            "similarity_score": result['similarity_score'],
            "texto_preview": result['texto'][:200] + "..." if len(result['texto']) > 200 else result['texto']
        })
    
    return {
        "respuesta": fallback_response,
        "fuentes": sources_info,
        "total_fuentes": len(sources_info),
        "query_procesada": query
    }

def _generate_advanced_fallback_response(query: str, search_results: List[Dict[str, Any]]) -> str:
    """
    Fallback avanzado que analiza el contexto sin usar respuestas predeterminadas
    """
    import re
    
    # Analizar la pregunta para identificar conceptos clave
    query_lower = query.lower()
    key_concepts = []
    
    # Mapeo de conceptos 
    concept_mapping = {
        'racismo': ['discriminación', 'racial', 'étnico', 'prejuicio', 'estereotipo'],
        'política': ['gobierno', 'estado', 'poder', 'democracia', 'fujimori', 'político'],
        'identidad': ['cultural', 'mestizaje', 'peruana', 'nacional', 'identitario'],
        'cultura': ['tradición', 'costumbres', 'valores', 'sociedad', 'cultural'],
        'discriminación': ['social', 'desigualdad', 'exclusión', 'segregación'],
        'sociedad': ['social', 'grupos', 'clases', 'estratos', 'jerarquía'],
        'educación': ['escuela', 'universidad', 'enseñanza', 'académico'],
        'economía': ['económico', 'clase', 'dinero', 'trabajo', 'laboral'],
        'historia': ['histórico', 'pasado', 'evolución', 'tiempo'],
        'modernidad': ['moderno', 'modernización', 'cambio', 'transformación']
    }
    
    # Identificar conceptos en la pregunta
    for concept, related_terms in concept_mapping.items():
        if concept in query_lower or any(term in query_lower for term in related_terms):
            key_concepts.append(concept)
    
    # Extraer información relevante del contexto
    relevant_info = []
    context_text = ' '.join([r["texto"] for r in search_results[:3]])
    
    # Buscar oraciones relevantes
    sentences = re.split(r'[.!?]+', context_text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 40:  # Oraciones sustanciales
            sentence_lower = sentence.lower()
            
            # Calcular relevancia
            relevance_score = 0
            for concept in key_concepts:
                if concept in sentence_lower:
                    relevance_score += 2
            
            # Buscar términos relacionados
            for concept, related in concept_mapping.items():
                if concept in key_concepts:
                    for term in related:
                        if term in sentence_lower:
                            relevance_score += 1
            
            if relevance_score > 0:
                relevant_info.append((sentence, relevance_score))
    
    # Ordenar por relevancia
    relevant_info.sort(key=lambda x: x[1], reverse=True)
    top_sentences = [sent[0] for sent in relevant_info[:4]]
    
    # Construir respuesta analítica estructurada
    if top_sentences and key_concepts:
        concepts_text = ', '.join(key_concepts)
        response_parts = [
            f"Según el análisis de los documentos sobre {concepts_text}:",
            ""
        ]
        
        # Categorizar información
        definitions = []
        characteristics = []
        examples = []
        
        for sentence in top_sentences:
            sentence_lower = sentence.lower()
            if any(pattern in sentence_lower for pattern in ['se define', 'es', 'significa', 'consiste']):
                definitions.append(sentence)
            elif any(pattern in sentence_lower for pattern in ['caracteriza', 'presenta', 'muestra', 'evidencia']):
                characteristics.append(sentence)
            elif any(pattern in sentence_lower for pattern in ['ejemplo', 'caso', 'como', 'tal como']):
                examples.append(sentence)
            else:
                characteristics.append(sentence)  # Default category
        
        # Agregar secciones estructuradas
        if definitions:
            response_parts.append("**Aspectos conceptuales:**")
            for definition in definitions[:2]:
                clean_def = definition.replace('\n', ' ').strip()
                response_parts.append(f"• {clean_def}")
            response_parts.append("")
        
        if characteristics:
            response_parts.append("**Características identificadas:**")
            for char in characteristics[:2]:
                clean_char = char.replace('\n', ' ').strip()
                response_parts.append(f"• {clean_char}")
            response_parts.append("")
        
        if examples:
            response_parts.append("**Manifestaciones específicas:**")
            for example in examples[:1]:
                clean_example = example.replace('\n', ' ').strip()
                response_parts.append(f"• {clean_example}")
            response_parts.append("")
        
        # Síntesis
        if len(key_concepts) == 1:
            synthesis = f"Este análisis revela que {key_concepts[0]} presenta múltiples dimensiones que requieren consideración del contexto peruano específico."
        else:
            synthesis = f"La intersección de estos elementos ({', '.join(key_concepts)}) muestra la complejidad del tema en el contexto sociocultural peruano."
        
        response_parts.append(synthesis)
        
        return '\n'.join(response_parts)
    
    # Respuesta general pero informativa usando contexto
    if search_results:
        # Usar contenido más relevante
        top_content = search_results[0]["texto"]
        
        # Extraer oraciones clave
        key_sentences = []
        sentences = re.split(r'[.!?]+', top_content)
        for sentence in sentences[:5]:  # Primeras 5 oraciones
            sentence = sentence.strip()
            if len(sentence) > 50:  # Sustanciales
                key_sentences.append(sentence)
        
        if key_sentences:
            response = f"Basándome en el análisis de los documentos encontrados:\n\n"
            
            for i, sentence in enumerate(key_sentences[:3], 1):
                clean_sentence = sentence.replace('\n', ' ').strip()
                response += f"{i}. {clean_sentence}.\n"
            
            response += f"\nEsta información proporciona elementos clave para entender el tema desde la perspectiva de los documentos analizados."
            
            return response
    
    # Último recurso - respuesta contextual
    return (
        f"Los documentos consultados abordan aspectos de '{query}'. "
        f"Se encontraron {len(search_results)} fragmentos relacionados que contienen "
        f"información sobre el tema, incluyendo análisis, definiciones y ejemplos específicos "
        f"del contexto peruano. La información sugiere un enfoque multidimensional del tema."
    )

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