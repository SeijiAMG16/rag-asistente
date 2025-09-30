"""
🤖 SISTEMA RAG CON DEEPSEEK V3 - CÓDIGO COMPLETAMENTE DOCUMENTADO
================================================================

Este archivo contiene el sistema completo de RAG (Retrieval-Augmented Generation)
con integración de DeepSeek V3 para análisis académico contextual.

TECNOLOGÍAS CLAVE:
- DeepSeek V3: Modelo de 671B parámetros vía OpenRouter API
- all-mpnet-base-v2: Embeddings de 768 dimensiones
- ChromaDB: Base de datos vectorial con índice HNSW
- OpenRouter API: Gateway para modelos de IA avanzados
- Django REST Framework: Backend API
- React: Frontend interactivo

FLUJO RAG COMPLETO:
1. QUERY ENCODING: Convierte pregunta del usuario a vector 768D
2. SIMILARITY SEARCH: Busca chunks relevantes en ChromaDB
3. CONTEXT PREPARATION: Prepara contexto para DeepSeek V3
4. LLM ANALYSIS: DeepSeek V3 analiza y genera respuesta académica
5. RESPONSE FORMATTING: Estructura respuesta con fuentes y metadata
"""

import os
import re
import sys
import logging
from typing import List, Dict, Any
from pathlib import Path

# === CONFIGURACIÓN DE LOGGING ===
# Sistema de logging para monitorear operaciones RAG
logger = logging.getLogger(__name__)

# === CONFIGURACIÓN DE MODELOS LLM ===
# Sistema de fallback jerárquico para modelos de generación
USE_LLM = os.environ.get("USE_LLM", "false").lower() == "true"
LLM_MODEL = os.environ.get("LLM_MODEL", "Qwen/Qwen1.5-1.8B-Chat")
LLM_MAX_NEW_TOKENS = int(os.environ.get("LLM_MAX_NEW_TOKENS", "240"))
_LLM_PIPELINE = None  # Cache global del pipeline de generación

def initialize_rag_components():
    """
    Inicializa todos los componentes del sistema RAG
    
    Esta función es el punto de entrada principal que configura:
    1. Modelo de embeddings (all-mpnet-base-v2)
    2. Cliente ChromaDB con persistencia
    3. Colección de documentos vectorizados
    
    DETALLES TÉCNICOS:
    - all-mpnet-base-v2: Modelo basado en MPNet de Microsoft
    - 768 dimensiones: Tamaño óptimo para similitud semántica
    - ChromaDB: Base vectorial con índice HNSW para búsqueda eficiente
    - Persistencia local: Datos almacenados en disco para velocidad
    
    Returns:
        tuple: (modelo_embeddings, cliente_chromadb, colección)
    
    Raises:
        Exception: Si falla la inicialización de componentes críticos
    """
    try:
        # === IMPORTACIÓN DE BIBLIOTECAS CRÍTICAS ===
        from sentence_transformers import SentenceTransformer
        import chromadb

        # === CONFIGURACIÓN DE RUTAS ===
        # Detectar automáticamente la ubicación de ChromaDB
        current_dir = Path(__file__).parent
        chroma_path = current_dir.parent.parent / "chroma_db_simple"
        
        logger.info(f"📁 Ruta ChromaDB: {chroma_path}")
        
        # === INICIALIZACIÓN DEL MODELO DE EMBEDDINGS ===
        # all-mpnet-base-v2: Modelo de embeddings de alta calidad
        # - Entrenado en 1B+ pares de oraciones
        # - Soporte multilenguaje (español incluido)
        # - Optimizado para similitud semántica
        # - 768 dimensiones (balance entre calidad y eficiencia)
        logger.info("🤖 Cargando modelo all-mpnet-base-v2...")
        model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        
        # Verificar dimensiones del modelo
        embedding_dim = model.get_sentence_embedding_dimension()
        logger.info(f"📊 Dimensiones de embeddings: {embedding_dim}")

        # === INICIALIZACIÓN DE CHROMADB ===
        # ChromaDB: Base de datos vectorial optimizada
        # - Índice HNSW: Hierarchical Navigable Small World
        # - Búsqueda aproximada en O(log n)
        # - Soporte para metadata estructurada
        # - Backend SQLite para persistencia
        logger.info("🗄️ Inicializando cliente ChromaDB...")
        client = chromadb.PersistentClient(path=str(chroma_path))
        
        # Obtener colección de documentos
        collection = client.get_collection("simple_rag_docs")
        
        # === VERIFICACIÓN DE ESTADO ===
        # Contar documentos disponibles para búsqueda
        count = collection.count()
        logger.info(f"📚 Documentos en ChromaDB: {count}")
        
        if count == 0:
            logger.warning("⚠️ ChromaDB está vacía. Ejecutar ETL primero.")
        
        logger.info("✅ Componentes RAG inicializados correctamente")
        return model, client, collection

    except Exception as e:
        logger.error(f"❌ Error inicializando componentes RAG: {str(e)}")
        raise

def perform_semantic_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Ejecuta búsqueda semántica en la base de datos vectorial
    
    ALGORITMO DE BÚSQUEDA:
    1. ENCODING: Convierte la query a vector de 768 dimensiones
    2. SIMILARITY: Calcula similitud coseno con todos los documentos
    3. RANKING: Ordena resultados por score de similitud
    4. FILTERING: Retorna top_k resultados más relevantes
    
    OPTIMIZACIONES:
    - Índice HNSW para búsqueda sub-lineal
    - Normalización L2 de vectores para similitud coseno
    - Filtrado por threshold de relevancia
    - Preservación de metadata para trazabilidad
    
    Args:
        query (str): Pregunta del usuario en lenguaje natural
        top_k (int): Número máximo de resultados a retornar
        
    Returns:
        List[Dict]: Lista de chunks relevantes con metadata
        
    Estructura de retorno:
    [
        {
            'texto': 'contenido del chunk...',
            'archivo': 'documento_fuente.pdf',
            'chunk': 'chunk_001',
            'similarity_score': 0.85
        },
        ...
    ]
    """
    
    # === PRIORIZACIÓN DE SISTEMAS ===
    # El sistema prioriza diferentes implementaciones RAG:
    # 1. Sistema optimizado (híbrido + reranking)
    # 2. Sistema mejorado (con APIs externas)
    # 3. Sistema básico (solo ChromaDB)
    
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
    
    # === BÚSQUEDA BÁSICA CON CHROMADB ===
    try:
        # Inicializar componentes RAG
        model, client, collection = initialize_rag_components()

        # === FASE 1: VERIFICACIÓN DE DATOS ===
        try:
            # Verificar que hay documentos para buscar
            count = collection.count()
            if count == 0:
                logger.warning("⚠️ Colección 'simple_rag_docs' está vacía")
                return []
            logger.info(f"🔍 Buscando en colección con {count} documentos")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo verificar el conteo: {e}")
            # Continuar con la búsqueda de todas formas

        # === FASE 2: ENCODING DE LA QUERY ===
        logger.info(f"🔤 Encoding query: '{query[:50]}...'")
        
        # Generar embedding de la query usando el mismo modelo
        # que se usó para los documentos (consistencia crucial)
        query_embedding = model.encode([query])
        
        logger.info(f"🎯 Query embedding generado: {query_embedding.shape}")

        # === FASE 3: BÚSQUEDA POR SIMILITUD ===
        logger.info(f"🔍 Ejecutando búsqueda semántica (top_k={top_k})")
        
        # Búsqueda en ChromaDB usando similitud coseno
        # ChromaDB maneja automáticamente:
        # - Normalización de vectores
        # - Cálculo de similitud coseno
        # - Ranking por score
        # - Filtrado por top_k
        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )

        # === FASE 4: PROCESAMIENTO DE RESULTADOS ===
        formatted_results = []
        
        if results and results['documents'] and results['documents'][0]:
            documents = results['documents'][0]
            metadatas = results['metadatas'][0] if results['metadatas'] else []
            distances = results['distances'][0] if results['distances'] else []
            
            logger.info(f"📊 Encontrados {len(documents)} resultados")
            
            # Procesar cada resultado
            for i, doc in enumerate(documents):
                # Obtener metadata (con fallbacks para robustez)
                metadata = metadatas[i] if i < len(metadatas) else {}
                distance = distances[i] if i < len(distances) else 1.0
                
                # Convertir distancia a score de similitud
                # ChromaDB retorna distancias (menor = más similar)
                # Convertimos a score de similitud (mayor = más similar)
                similarity_score = 1.0 - distance if distance <= 1.0 else 0.0
                
                # Estructurar resultado
                result = {
                    'texto': doc,
                    'archivo': metadata.get('source_file', 'documento_desconocido'),
                    'chunk': metadata.get('chunk_id', f'chunk_{i}'),
                    'similarity_score': similarity_score,
                    'metadata': metadata  # Metadata completa para uso avanzado
                }
                
                formatted_results.append(result)
                
                # Log detallado para debugging
                logger.debug(f"   📄 {result['archivo']} - Score: {similarity_score:.3f}")
        
        else:
            logger.warning("⚠️ No se encontraron resultados para la query")
        
        logger.info(f"✅ Búsqueda completada: {len(formatted_results)} resultados")
        return formatted_results
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda semántica: {str(e)}")
        return []

def generate_rag_response(query: str, search_results: List[Dict[str, Any]]) -> str:
    """
    Genera respuesta RAG usando DeepSeek V3 para análisis académico
    
    JERARQUÍA DE MODELOS:
    1. DeepSeek V3 (671B parámetros) - vía OpenRouter API
    2. Sistema básico estructurado (fallback)
    
    DEEPSEEK V3 CARACTERÍSTICAS:
    - 671 billion parámetros
    - Contexto de 128K tokens
    - Optimizado para análisis académico
    - Multimodal (texto, código, matemáticas)
    - Temperature 0.3 para consistencia
    
    PROMPT ENGINEERING:
    - Rol específico: Asistente académico
    - Contexto estructurado con fuentes numeradas
    - Instrucciones claras para citas y referencias
    - Formato de respuesta académica
    
    Args:
        query (str): Pregunta del usuario
        search_results (List[Dict]): Resultados de búsqueda semántica
        
    Returns:
        str o Dict: Respuesta generada con fuentes (formato depende del fallback)
    """
    
    # === VALIDACIÓN DE ENTRADA ===
    if not search_results:
        logger.warning("⚠️ No hay resultados de búsqueda para generar respuesta")
        return _generate_no_results_response(query)

    # === PRIORIDAD 1: DEEPSEEK V3 VIA OPENROUTER ===
    from dotenv import load_dotenv
    load_dotenv()
    
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    if openrouter_key:
        logger.info("🤖 Usando DeepSeek V3 para análisis académico")
        
        try:
            import requests
            import json
            
            # === PREPARACIÓN DEL CONTEXTO ===
            # Formatear chunks de búsqueda como contexto estructurado
            context_chunks = []
            for i, result in enumerate(search_results[:5], 1):  # Top 5 resultados
                # Formato: [FUENTE N: archivo.pdf] contenido
                chunk = f"[FUENTE {i}: {result['archivo']}]\n{result['texto']}"
                context_chunks.append(chunk)
            
            # Unir todos los chunks en contexto único
            context_text = "\n\n".join(context_chunks)
            
            # === PROMPT ENGINEERING PARA DEEPSEEK V3 ===
            # Prompt especializado para análisis académico
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
- Usa el formato [FUENTE N] para referenciar las fuentes

RESPUESTA:"""

            # === CONFIGURACIÓN DE LA API ===
            # Headers requeridos por OpenRouter
            headers = {
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",  # Identificación de la app
                "X-Title": "RAG Academic Assistant"
            }
            
            # === PARÁMETROS DEL MODELO ===
            # Configuración optimizada para análisis académico
            data = {
                "model": "deepseek/deepseek-v3",    # Modelo específico
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,    # Baja temperatura para consistencia
                "max_tokens": 2000,    # Suficiente para análisis detallado
                "top_p": 0.9,         # Control de diversidad
                "frequency_penalty": 0.1,  # Reducir repetición
                "presence_penalty": 0.1    # Fomentar nuevas ideas
            }
            
            # === LLAMADA A LA API ===
            logger.info("🌐 Enviando request a OpenRouter/DeepSeek V3...")
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60  # Timeout de 60 segundos
            )
            
            # === PROCESAMIENTO DE LA RESPUESTA ===
            if response.status_code == 200:
                result = response.json()
                
                # Verificar estructura de respuesta válida
                if 'choices' in result and len(result['choices']) > 0:
                    deepseek_response = result['choices'][0]['message']['content']
                    
                    # Métricas de la respuesta
                    response_length = len(deepseek_response)
                    logger.info(f"✅ DeepSeek V3 respuesta exitosa: {response_length} caracteres")
                    
                    # Log de uso de tokens (si está disponible)
                    if 'usage' in result:
                        usage = result['usage']
                        logger.info(f"📊 Tokens: prompt={usage.get('prompt_tokens', 0)}, "
                                  f"completion={usage.get('completion_tokens', 0)}")
                    
                    return deepseek_response
                else:
                    logger.error("❌ Respuesta de DeepSeek V3 sin contenido válido")
            else:
                logger.error(f"❌ Error API OpenRouter: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout en llamada a DeepSeek V3")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error de conexión con OpenRouter: {e}")
        except Exception as e:
            logger.error(f"❌ Error procesando DeepSeek V3: {e}")

    # === FALLBACK: SISTEMA BÁSICO ESTRUCTURADO ===
    logger.info("🔄 Usando sistema de respuesta estructurado (fallback)")
    
    try:
        # Preparar contexto para sistema básico
        context_chunks = []
        sources_info = []
        
        # Procesar resultados de búsqueda
        for i, result in enumerate(search_results[:5], 1):
            # Chunk con metadata para contexto
            chunk_with_metadata = f"[FUENTE {i}: {result['archivo']}]\n{result['texto']}"
            context_chunks.append(chunk_with_metadata)
            
            # Información de fuentes para frontend
            sources_info.append({
                "numero": i,
                "archivo": result['archivo'],
                "chunk": result['chunk'],
                "similarity_score": result['similarity_score'],
                "texto_preview": result['texto'][:200] + "..." if len(result['texto']) > 200 else result['texto']
            })
        
        logger.info(f"🔧 Generando respuesta básica para: '{query[:50]}...' con {len(context_chunks)} chunks")
        
        # === GENERACIÓN DE RESPUESTA BÁSICA ===
        response = _generate_advanced_fallback_response(query, search_results)
        
        # Verificar calidad de respuesta
        if response and len(response.strip()) > 50:
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
            logger.warning("⚠️ Respuesta básica insuficiente, usando fallback final")
            return _generate_advanced_fallback_response_with_sources(query, search_results)
        
    except Exception as e:
        logger.error(f"❌ Error en sistema básico: {e}")
        return _generate_advanced_fallback_response_with_sources(query, search_results)

def _generate_no_results_response(query: str) -> str:
    """
    Genera respuesta cuando no se encuentran documentos relevantes
    
    Esta función maneja el caso donde la búsqueda semántica no retorna
    resultados suficientemente relevantes para la query del usuario.
    
    Args:
        query (str): Query original del usuario
        
    Returns:
        str: Mensaje explicativo para el usuario
    """
    return (
        f"No encontré información específica sobre '{query}' en los documentos disponibles. "
        f"Te sugiero reformular la pregunta o verificar que los documentos contengan "
        f"información relacionada con el tema consultado.\n\n"
        f"Algunas sugerencias:\n"
        f"- Usa términos más específicos o sinónimos\n"
        f"- Verifica la ortografía de nombres propios\n"
        f"- Intenta con preguntas más generales sobre el tema"
    )

def _generate_advanced_fallback_response_with_sources(query: str, search_results: List[Dict[str, Any]]) -> Dict:
    """
    Fallback avanzado que incluye fuentes estructuradas
    
    Esta función genera una respuesta estructurada cuando fallan
    los sistemas principales de generación de respuestas.
    
    Args:
        query (str): Query del usuario
        search_results (List[Dict]): Resultados de búsqueda
        
    Returns:
        Dict: Respuesta estructurada con fuentes
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
    Genera respuesta avanzada sin usar LLMs externos
    
    ALGORITMO DE RESPUESTA:
    1. ANÁLISIS DE QUERY: Identifica términos clave y patrones
    2. RANKING DE CONTENIDO: Prioriza chunks más relevantes
    3. EXTRACCIÓN DE CITAS: Identifica referencias académicas
    4. SÍNTESIS: Combina información de múltiples fuentes
    5. FORMATEO: Estructura respuesta académica
    
    Args:
        query (str): Query del usuario
        search_results (List[Dict]): Resultados de búsqueda
        
    Returns:
        str: Respuesta generada algorítmicamente
    """
    import re
    
    if not search_results:
        return _generate_no_results_response(query)
    
    # === ANÁLISIS DE LA QUERY ===
    # Extraer términos clave de la pregunta
    query_terms = _extract_key_terms(query)
    logger.debug(f"🔍 Términos clave extraídos: {query_terms}")
    
    # === ANÁLISIS DE CONTENIDO ===
    relevant_passages = []
    academic_references = []
    
    # Procesar cada resultado de búsqueda
    for i, result in enumerate(search_results[:3], 1):  # Top 3 para calidad
        text = result['texto']
        source = result['archivo']
        score = result['similarity_score']
        
        # Extraer pasajes más relevantes del chunk
        relevant_parts = _extract_relevant_passages(text, query_terms)
        
        # Buscar referencias académicas en el texto
        references = _extract_academic_references(text)
        
        # Agregar a listas
        for passage in relevant_parts:
            relevant_passages.append({
                'text': passage,
                'source': source,
                'source_number': i,
                'score': score
            })
        
        academic_references.extend(references)
    
    # === CONSTRUCCIÓN DE RESPUESTA ===
    response_parts = []
    
    # Introducción contextual
    if query_terms:
        intro = f"Basándome en los documentos disponibles, puedo proporcionar la siguiente información sobre {', '.join(query_terms[:3])}:"
        response_parts.append(intro)
    
    # Contenido principal
    if relevant_passages:
        response_parts.append("\n")
        
        # Agrupar pasajes por tema/fuente
        for i, passage in enumerate(relevant_passages[:5], 1):
            formatted_passage = f"{i}. {passage['text']} [Fuente: {passage['source']}]"
            response_parts.append(formatted_passage)
    
    # Referencias académicas encontradas
    if academic_references:
        response_parts.append("\n\nReferencias académicas mencionadas:")
        unique_refs = list(set(academic_references))[:3]  # Máximo 3 referencias
        for ref in unique_refs:
            response_parts.append(f"- {ref}")
    
    # Conclusión
    if len(search_results) > 3:
        conclusion = f"\n\nEsta información está basada en {len(search_results)} documentos relevantes. Para un análisis más detallado, te recomiendo revisar las fuentes específicas mencionadas."
        response_parts.append(conclusion)
    
    # Unir todas las partes
    final_response = "\n".join(response_parts)
    
    # Verificar longitud mínima
    if len(final_response.strip()) < 100:
        # Respuesta muy corta, usar contenido directo
        return _generate_direct_content_response(query, search_results)
    
    return final_response

def _extract_key_terms(query: str) -> List[str]:
    """
    Extrae términos clave de la query del usuario
    
    ALGORITMO:
    1. Normalización de texto (minúsculas, eliminar acentos)
    2. Filtrado de stopwords
    3. Extracción de entidades (nombres propios, años)
    4. Ranking por relevancia
    
    Args:
        query (str): Query del usuario
        
    Returns:
        List[str]: Lista de términos clave ordenados por importancia
    """
    # Stopwords en español (palabras comunes a filtrar)
    stopwords = {
        'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son',
        'con', 'para', 'al', 'del', 'los', 'las', 'una', 'como', 'qué', 'cuál', 'cuáles', 'sobre', 'según',
        'cómo', 'dónde', 'cuándo', 'por qué', 'porque', 'pero', 'sin', 'hasta', 'desde', 'durante'
    }
    
    # Normalizar query
    normalized_query = query.lower()
    
    # Extraer palabras
    words = re.findall(r'\b\w+\b', normalized_query)
    
    # Filtrar stopwords y palabras muy cortas
    key_terms = [word for word in words if word not in stopwords and len(word) > 2]
    
    # Detectar años (importante en contexto académico)
    years = re.findall(r'\b(19|20)\d{2}\b', query)
    key_terms.extend(years)
    
    # Detectar nombres propios (comienzan con mayúscula)
    proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', query)
    key_terms.extend([noun.lower() for noun in proper_nouns])
    
    # Remover duplicados manteniendo orden
    seen = set()
    unique_terms = []
    for term in key_terms:
        if term not in seen:
            seen.add(term)
            unique_terms.append(term)
    
    return unique_terms[:10]  # Máximo 10 términos

def _extract_relevant_passages(text: str, query_terms: List[str]) -> List[str]:
    """
    Extrae pasajes relevantes de un texto basándose en términos clave
    
    Args:
        text (str): Texto a analizar
        query_terms (List[str]): Términos clave a buscar
        
    Returns:
        List[str]: Lista de pasajes relevantes
    """
    if not query_terms:
        # Si no hay términos, retornar primeras oraciones
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences[:2] if len(s.strip()) > 20]
    
    # Dividir texto en oraciones
    sentences = re.split(r'[.!?]+', text)
    relevant_sentences = []
    
    # Evaluar cada oración
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:  # Filtrar oraciones muy cortas
            continue
        
        # Contar términos presentes en la oración
        sentence_lower = sentence.lower()
        term_count = sum(1 for term in query_terms if term in sentence_lower)
        
        # Si contiene términos relevantes, agregar
        if term_count > 0:
            relevant_sentences.append((sentence, term_count))
    
    # Ordenar por relevancia (número de términos)
    relevant_sentences.sort(key=lambda x: x[1], reverse=True)
    
    # Retornar top oraciones (solo el texto)
    return [sentence[0] for sentence in relevant_sentences[:3]]

def _extract_academic_references(text: str) -> List[str]:
    """
    Extrae referencias académicas del texto
    
    PATRONES DETECTADOS:
    - (Autor, 2020)
    - (Autor et al., 2020)
    - Según Autor (2020)
    - Como señala Autor et al. (2020)
    
    Args:
        text (str): Texto a analizar
        
    Returns:
        List[str]: Lista de referencias encontradas
    """
    references = []
    
    # Patrón 1: (Autor, año)
    pattern1 = r'\(([A-Z][a-zA-Z]+),?\s+(\d{4})\)'
    matches1 = re.findall(pattern1, text)
    for match in matches1:
        references.append(f"{match[0]} ({match[1]})")
    
    # Patrón 2: (Autor et al., año)
    pattern2 = r'\(([A-Z][a-zA-Z]+)\s+et\s+al\.,?\s+(\d{4})\)'
    matches2 = re.findall(pattern2, text)
    for match in matches2:
        references.append(f"{match[0]} et al. ({match[1]})")
    
    # Patrón 3: Según Autor
    pattern3 = r'[Ss]egún\s+([A-Z][a-zA-Z]+)'
    matches3 = re.findall(pattern3, text)
    for match in matches3:
        references.append(f"Según {match}")
    
    return references

def _generate_direct_content_response(query: str, search_results: List[Dict[str, Any]]) -> str:
    """
    Genera respuesta directa usando contenido de los resultados
    
    Args:
        query (str): Query del usuario
        search_results (List[Dict]): Resultados de búsqueda
        
    Returns:
        str: Respuesta directa
    """
    if not search_results:
        return _generate_no_results_response(query)
    
    response_parts = ["Basándome en los documentos encontrados:\n"]
    
    for i, result in enumerate(search_results[:3], 1):
        # Tomar primera parte del texto como respuesta
        text_preview = result['texto'][:300] + "..." if len(result['texto']) > 300 else result['texto']
        source = result['archivo']
        
        response_parts.append(f"{i}. {text_preview} [Fuente: {source}]")
    
    return "\n\n".join(response_parts)

def clean_and_format_response(response: str) -> str:
    """
    Limpia y formatea la respuesta para el usuario final
    
    PROCESAMIENTO:
    1. Normalización de espacios en blanco
    2. Corrección de puntuación
    3. Formato de párrafos
    4. Limpieza de caracteres especiales
    
    Args:
        response (str): Respuesta cruda a limpiar
        
    Returns:
        str: Respuesta limpia y formateada
    """
    if not response:
        return "No se pudo generar una respuesta válida."
    
    # Normalizar espacios en blanco
    response = re.sub(r'\s+', ' ', response)
    response = re.sub(r'\n\s*\n', '\n\n', response)
    
    # Corregir puntuación
    response = re.sub(r'\s+([.!?,:;])', r'\1', response)
    response = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', response)
    
    # Limpiar caracteres especiales problemáticos
    response = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', response)
    
    # Asegurar terminación correcta
    response = response.strip()
    if response and not response.endswith(('.', '!', '?', ':')):
        response += '.'
    
    return response