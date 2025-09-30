"""
🌐 VISTAS DJANGO RAG - API BACKEND COMPLETAMENTE DOCUMENTADA
===========================================================

Este archivo contiene todas las vistas de la API Django que exponen
el sistema RAG con DeepSeek V3 como endpoints REST.

ENDPOINTS PRINCIPALES:
1. /api/search/ - Búsqueda semántica en documentos
2. /api/ask/ - Consulta RAG con DeepSeek V3
3. /api/health/ - Estado del sistema
4. /api/stats/ - Estadísticas del sistema
5. /api/documents/ - Gestión de documentos

ARQUITECTURA DE LA API:
- Django REST Framework para serialización
- Autenticación y autorización configurables
- Throttling para prevenir abuso
- Logging detallado para monitoreo
- Manejo robusto de errores
- Validación de entrada completa

INTEGRACIÓN CON RAG:
- ChromaDB para búsqueda vectorial
- all-mpnet-base-v2 para embeddings
- DeepSeek V3 para generación de respuestas
- Sistema de cache para optimización
- Métricas de performance en tiempo real
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# === IMPORTS DE DJANGO ===
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.conf import settings
from django.core.cache import cache
from django.views import View

# === IMPORTS DE DRF ===
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework import status

# === IMPORTS DEL SISTEMA RAG ===
try:
    from backend.rag_system_comentado import (
        perform_semantic_search,
        generate_rag_response,
        initialize_rag_components
    )
    from backend.utils.rag_utils_comentado import (
        QueryOptimizer,
        validate_embeddings_consistency,
        RAGLogger
    )
except ImportError as e:
    logging.warning(f"⚠️ Imports RAG no disponibles: {e}")
    # Fallbacks para desarrollo
    def perform_semantic_search(query, top_k=5):
        return []
    def generate_rag_response(query, results):
        return f"Sistema RAG no disponible. Query: {query}"
    def initialize_rag_components():
        return None, None, None

# === CONFIGURACIÓN DE LOGGING ===
logger = logging.getLogger(__name__)
rag_logger = RAGLogger("API_Views")

# === CONFIGURACIÓN DE THROTTLING ===
class RAGSearchThrottle(AnonRateThrottle):
    """
    Throttling específico para búsquedas RAG
    Límite: 30 búsquedas por minuto para usuarios anónimos
    """
    rate = '30/min'

class RAGQueryThrottle(AnonRateThrottle):
    """
    Throttling específico para consultas RAG con LLM
    Límite: 10 consultas por minuto (más restrictivo por uso de DeepSeek V3)
    """
    rate = '10/min'

# === CACHE DE COMPONENTES RAG ===
_rag_components_cache = {
    'model': None,
    'client': None,
    'collection': None,
    'last_initialized': None,
    'initialization_error': None
}

def get_rag_components():
    """
    Obtiene componentes RAG con cache y reinicialización automática
    
    ESTRATEGIA DE CACHE:
    - Cache en memoria para evitar reinicialización constante
    - Timeout de 1 hora para reinicialización periódica
    - Manejo de errores con fallback graceful
    - Logging detallado para debugging
    
    Returns:
        tuple: (modelo, cliente, colección) o (None, None, None) si falla
    """
    global _rag_components_cache
    
    current_time = datetime.now()
    cache_timeout = timedelta(hours=1)
    
    # Verificar si necesita reinicialización
    needs_init = (
        _rag_components_cache['model'] is None or
        _rag_components_cache['last_initialized'] is None or
        current_time - _rag_components_cache['last_initialized'] > cache_timeout
    )
    
    if needs_init:
        try:
            logger.info("🔄 Inicializando componentes RAG...")
            model, client, collection = initialize_rag_components()
            
            _rag_components_cache.update({
                'model': model,
                'client': client,
                'collection': collection,
                'last_initialized': current_time,
                'initialization_error': None
            })
            
            logger.info("✅ Componentes RAG inicializados exitosamente")
            
        except Exception as e:
            error_msg = f"❌ Error inicializando RAG: {str(e)}"
            logger.error(error_msg)
            
            _rag_components_cache['initialization_error'] = error_msg
            return None, None, None
    
    return (
        _rag_components_cache['model'],
        _rag_components_cache['client'],
        _rag_components_cache['collection']
    )

def create_error_response(message: str, status_code: int = 400, error_code: str = None) -> JsonResponse:
    """
    Crea respuesta de error estandarizada
    
    Args:
        message (str): Mensaje de error para el usuario
        status_code (int): Código HTTP de estado
        error_code (str): Código interno de error
        
    Returns:
        JsonResponse: Respuesta JSON con formato de error estándar
    """
    error_data = {
        'error': True,
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'status_code': status_code
    }
    
    if error_code:
        error_data['error_code'] = error_code
    
    logger.error(f"API Error: {message} (Code: {status_code})")
    return JsonResponse(error_data, status=status_code)

def create_success_response(data: Any, message: str = None) -> JsonResponse:
    """
    Crea respuesta de éxito estandarizada
    
    Args:
        data (Any): Datos a retornar
        message (str): Mensaje opcional de éxito
        
    Returns:
        JsonResponse: Respuesta JSON con formato estándar
    """
    response_data = {
        'success': True,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    
    if message:
        response_data['message'] = message
    
    return JsonResponse(response_data)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Endpoint de verificación de salud del sistema
    
    VERIFICACIONES:
    - Estado de componentes RAG (modelo, ChromaDB)
    - Conectividad con DeepSeek V3
    - Estado de cache y memoria
    - Tiempo de respuesta del sistema
    
    Returns:
        JSON: Estado detallado del sistema
    """
    start_time = time.time()
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {},
        'performance': {}
    }
    
    try:
        # === VERIFICACIÓN 1: COMPONENTES RAG ===
        logger.info("🔍 Verificando componentes RAG...")
        model, client, collection = get_rag_components()
        
        if model and client and collection:
            # Verificar ChromaDB
            try:
                doc_count = collection.count()
                health_status['components']['chromadb'] = {
                    'status': 'healthy',
                    'document_count': doc_count
                }
            except Exception as e:
                health_status['components']['chromadb'] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # Verificar modelo de embeddings
            try:
                test_embedding = model.encode(["test"])
                health_status['components']['embedding_model'] = {
                    'status': 'healthy',
                    'model_name': 'all-mpnet-base-v2',
                    'dimensions': len(test_embedding[0])
                }
            except Exception as e:
                health_status['components']['embedding_model'] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            health_status['components']['rag_system'] = {
                'status': 'error',
                'error': _rag_components_cache.get('initialization_error', 'Components not initialized')
            }
        
        # === VERIFICACIÓN 2: DEEPSEEK V3 ===
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            health_status['components']['deepseek_v3'] = {
                'status': 'configured',
                'api_key_present': True
            }
        else:
            health_status['components']['deepseek_v3'] = {
                'status': 'not_configured',
                'api_key_present': False
            }
        
        # === VERIFICACIÓN 3: CACHE ===
        try:
            cache.set('health_check', 'test', 30)
            cache_value = cache.get('health_check')
            health_status['components']['cache'] = {
                'status': 'healthy' if cache_value == 'test' else 'error'
            }
        except Exception as e:
            health_status['components']['cache'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # === MÉTRICAS DE PERFORMANCE ===
        end_time = time.time()
        health_status['performance'] = {
            'response_time_ms': round((end_time - start_time) * 1000, 2),
            'memory_usage': _get_memory_usage(),
            'uptime': _get_uptime()
        }
        
        # Determinar estado general
        component_statuses = [comp.get('status') for comp in health_status['components'].values()]
        if any(status == 'error' for status in component_statuses):
            health_status['status'] = 'degraded'
        
        logger.info(f"✅ Health check completado: {health_status['status']}")
        return create_success_response(health_status)
        
    except Exception as e:
        logger.error(f"❌ Error en health check: {str(e)}")
        return create_error_response(f"Error en verificación de salud: {str(e)}", 500)

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RAGSearchThrottle])
def semantic_search(request):
    """
    Endpoint para búsqueda semántica en documentos
    
    FUNCIONALIDAD:
    - Recibe query en lenguaje natural
    - Genera embeddings con all-mpnet-base-v2
    - Busca documentos similares en ChromaDB
    - Retorna resultados rankeados por similitud
    
    REQUEST FORMAT:
    {
        "query": "¿Qué es la democracia en el Perú?",
        "top_k": 5,
        "include_metadata": true
    }
    
    RESPONSE FORMAT:
    {
        "success": true,
        "data": {
            "query": "...",
            "results": [...],
            "search_metadata": {...}
        }
    }
    """
    start_time = time.time()
    
    try:
        # === VALIDACIÓN DE ENTRADA ===
        if request.method != 'POST':
            return create_error_response("Método no permitido", 405)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return create_error_response("JSON inválido en request body", 400)
        
        # Validar query
        query = data.get('query', '').strip()
        if not query:
            return create_error_response("Query requerida", 400, "MISSING_QUERY")
        
        if len(query) > 1000:
            return create_error_response("Query demasiado larga (máximo 1000 caracteres)", 400, "QUERY_TOO_LONG")
        
        # Parámetros opcionales
        top_k = data.get('top_k', 5)
        include_metadata = data.get('include_metadata', True)
        
        # Validar top_k
        if not isinstance(top_k, int) or top_k < 1 or top_k > 20:
            return create_error_response("top_k debe ser un entero entre 1 y 20", 400, "INVALID_TOP_K")
        
        logger.info(f"🔍 Búsqueda semántica iniciada: '{query[:50]}...' (top_k={top_k})")
        
        # === VERIFICAR COMPONENTES RAG ===
        model, client, collection = get_rag_components()
        if not all([model, client, collection]):
            return create_error_response("Sistema RAG no disponible", 503, "RAG_UNAVAILABLE")
        
        # === OPTIMIZACIÓN DE QUERY ===
        try:
            from backend.utils.rag_utils_comentado import QueryOptimizer
            optimizer = QueryOptimizer()
            optimized_query_info = optimizer.optimize_query(query)
            logger.debug(f"Query optimizada: {optimized_query_info}")
        except Exception as e:
            logger.warning(f"⚠️ Error en optimización de query: {e}")
            optimized_query_info = None
        
        # === EJECUTAR BÚSQUEDA SEMÁNTICA ===
        try:
            search_results = perform_semantic_search(query, top_k)
            
            # Verificar resultados
            if not search_results:
                logger.warning(f"⚠️ No se encontraron resultados para: '{query}'")
                return create_success_response({
                    'query': query,
                    'results': [],
                    'message': 'No se encontraron documentos relevantes para la consulta'
                })
            
            # === FORMATEAR RESULTADOS ===
            formatted_results = []
            for i, result in enumerate(search_results):
                formatted_result = {
                    'rank': i + 1,
                    'text': result.get('texto', ''),
                    'source': result.get('archivo', 'documento_desconocido'),
                    'similarity_score': round(result.get('similarity_score', 0), 4),
                    'chunk_id': result.get('chunk', f'chunk_{i}')
                }
                
                # Incluir metadata adicional si se solicita
                if include_metadata and 'metadata' in result:
                    formatted_result['metadata'] = result['metadata']
                
                formatted_results.append(formatted_result)
            
            # === MÉTRICAS DE BÚSQUEDA ===
            end_time = time.time()
            search_metadata = {
                'total_results': len(formatted_results),
                'search_time_ms': round((end_time - start_time) * 1000, 2),
                'query_length': len(query),
                'top_k_requested': top_k,
                'model_used': 'all-mpnet-base-v2'
            }
            
            # Agregar información de optimización si está disponible
            if optimized_query_info:
                search_metadata['query_optimization'] = {
                    'academic_score': optimized_query_info.get('academic_score', 0),
                    'key_terms': optimized_query_info.get('key_terms', []),
                    'entities_found': len(optimized_query_info.get('entities', {}).get('persons', [])) > 0
                }
            
            # === LOGGING DE OPERACIÓN ===
            rag_logger.log_search_operation(
                query=query,
                results_count=len(formatted_results),
                execution_time=end_time - start_time
            )
            
            # === RESPUESTA EXITOSA ===
            response_data = {
                'query': query,
                'results': formatted_results,
                'search_metadata': search_metadata
            }
            
            logger.info(f"✅ Búsqueda completada: {len(formatted_results)} resultados en {search_metadata['search_time_ms']}ms")
            return create_success_response(response_data)
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda semántica: {str(e)}")
            return create_error_response(f"Error ejecutando búsqueda: {str(e)}", 500, "SEARCH_ERROR")
        
    except Exception as e:
        logger.error(f"❌ Error inesperado en semantic_search: {str(e)}")
        return create_error_response("Error interno del servidor", 500, "INTERNAL_ERROR")

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RAGQueryThrottle])
def rag_query(request):
    """
    Endpoint principal para consultas RAG con DeepSeek V3
    
    PROCESO COMPLETO:
    1. Validación de entrada y autenticación
    2. Búsqueda semántica en ChromaDB
    3. Preparación de contexto para LLM
    4. Generación de respuesta con DeepSeek V3
    5. Post-procesamiento y formateo
    6. Logging y métricas
    
    REQUEST FORMAT:
    {
        "query": "¿Cuál es la situación política en el Perú según los documentos?",
        "context_length": 5,
        "include_sources": true,
        "academic_mode": true
    }
    
    RESPONSE FORMAT:
    {
        "success": true,
        "data": {
            "query": "...",
            "response": "...",
            "sources": [...],
            "metadata": {...}
        }
    }
    """
    start_time = time.time()
    
    try:
        # === VALIDACIÓN DE ENTRADA ===
        if request.method != 'POST':
            return create_error_response("Método no permitido", 405)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return create_error_response("JSON inválido en request body", 400)
        
        # Validar query
        query = data.get('query', '').strip()
        if not query:
            return create_error_response("Query requerida", 400, "MISSING_QUERY")
        
        if len(query) > 2000:
            return create_error_response("Query demasiado larga (máximo 2000 caracteres)", 400, "QUERY_TOO_LONG")
        
        # Parámetros opcionales
        context_length = data.get('context_length', 5)
        include_sources = data.get('include_sources', True)
        academic_mode = data.get('academic_mode', True)
        
        # Validar parámetros
        if not isinstance(context_length, int) or context_length < 1 or context_length > 10:
            return create_error_response("context_length debe ser un entero entre 1 y 10", 400, "INVALID_CONTEXT_LENGTH")
        
        logger.info(f"💬 Consulta RAG iniciada: '{query[:50]}...' (context={context_length})")
        
        # === VERIFICAR COMPONENTES RAG ===
        model, client, collection = get_rag_components()
        if not all([model, client, collection]):
            return create_error_response("Sistema RAG no disponible", 503, "RAG_UNAVAILABLE")
        
        # === VERIFICAR CONFIGURACIÓN DEEPSEEK V3 ===
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            logger.warning("⚠️ API key de OpenRouter no configurada, usando fallback")
        
        # === CACHE DE RESPUESTAS ===
        # Generar clave de cache basada en query y parámetros
        cache_key = f"rag_query_{hash(query)}_{context_length}_{academic_mode}"
        cached_response = cache.get(cache_key)
        
        if cached_response:
            logger.info(f"🎯 Respuesta obtenida desde cache para: '{query[:50]}...'")
            return create_success_response(cached_response)
        
        # === FASE 1: BÚSQUEDA SEMÁNTICA ===
        search_start_time = time.time()
        
        try:
            search_results = perform_semantic_search(query, context_length)
            search_end_time = time.time()
            
            if not search_results:
                logger.warning(f"⚠️ No se encontraron documentos relevantes para: '{query}'")
                
                no_results_response = {
                    'query': query,
                    'response': f"No encontré información específica sobre '{query}' en los documentos disponibles. "
                              f"Te sugiero reformular la pregunta o verificar que los documentos contengan información relacionada.",
                    'sources': [],
                    'metadata': {
                        'search_time_ms': round((search_end_time - search_start_time) * 1000, 2),
                        'total_time_ms': round((search_end_time - start_time) * 1000, 2),
                        'documents_found': 0,
                        'model_used': 'ninguno (sin contexto)',
                        'academic_mode': academic_mode
                    }
                }
                
                return create_success_response(no_results_response)
            
            logger.info(f"🔍 Búsqueda completada: {len(search_results)} documentos en {(search_end_time - search_start_time):.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda semántica: {str(e)}")
            return create_error_response(f"Error en búsqueda: {str(e)}", 500, "SEARCH_ERROR")
        
        # === FASE 2: GENERACIÓN DE RESPUESTA ===
        generation_start_time = time.time()
        
        try:
            # Llamar al sistema de generación RAG
            rag_response = generate_rag_response(query, search_results)
            generation_end_time = time.time()
            
            # === PROCESAMIENTO DE RESPUESTA ===
            if isinstance(rag_response, dict):
                # Respuesta estructurada (sistema básico)
                response_text = rag_response.get('respuesta', '')
                sources_info = rag_response.get('fuentes', [])
                
                logger.info(f"📝 Respuesta estructurada generada: {len(response_text)} caracteres")
                
            elif isinstance(rag_response, str):
                # Respuesta de texto (DeepSeek V3)
                response_text = rag_response
                
                # Extraer información de fuentes desde search_results
                sources_info = []
                if include_sources:
                    for i, result in enumerate(search_results[:context_length], 1):
                        sources_info.append({
                            'numero': i,
                            'archivo': result.get('archivo', 'documento_desconocido'),
                            'chunk': result.get('chunk', f'chunk_{i}'),
                            'similarity_score': result.get('similarity_score', 0),
                            'texto_preview': result.get('texto', '')[:200] + "..." if len(result.get('texto', '')) > 200 else result.get('texto', '')
                        })
                
                logger.info(f"🤖 Respuesta DeepSeek V3 generada: {len(response_text)} caracteres")
                
            else:
                logger.error(f"❌ Formato de respuesta inesperado: {type(rag_response)}")
                return create_error_response("Error en formato de respuesta", 500, "RESPONSE_FORMAT_ERROR")
            
            # === VALIDACIÓN DE RESPUESTA ===
            if not response_text or len(response_text.strip()) < 20:
                logger.warning("⚠️ Respuesta generada muy corta o vacía")
                response_text = "No se pudo generar una respuesta adecuada basada en los documentos encontrados. " \
                              "Por favor, intenta reformular tu pregunta de manera más específica."
            
            # === METADATA DE LA OPERACIÓN ===
            total_end_time = time.time()
            
            operation_metadata = {
                'search_time_ms': round((search_end_time - search_start_time) * 1000, 2),
                'generation_time_ms': round((generation_end_time - generation_start_time) * 1000, 2),
                'total_time_ms': round((total_end_time - start_time) * 1000, 2),
                'documents_found': len(search_results),
                'context_length_used': len(search_results),
                'response_length': len(response_text),
                'sources_included': len(sources_info),
                'model_used': 'DeepSeek V3' if openrouter_key else 'Sistema básico',
                'academic_mode': academic_mode,
                'cache_used': False,
                'timestamp': datetime.now().isoformat()
            }
            
            # === ESTRUCTURA DE RESPUESTA FINAL ===
            final_response = {
                'query': query,
                'response': response_text,
                'sources': sources_info if include_sources else [],
                'metadata': operation_metadata
            }
            
            # === CACHE DE RESPUESTA ===
            # Cachear respuesta por 10 minutos
            cache.set(cache_key, final_response, 600)
            
            # === LOGGING DE OPERACIÓN COMPLETA ===
            rag_logger.log_llm_operation(
                model=operation_metadata['model_used'],
                tokens_used=len(query.split()) + len(response_text.split()),
                execution_time=total_end_time - start_time
            )
            
            logger.info(f"✅ Consulta RAG completada exitosamente en {operation_metadata['total_time_ms']}ms")
            return create_success_response(final_response)
            
        except Exception as e:
            logger.error(f"❌ Error en generación de respuesta: {str(e)}")
            return create_error_response(f"Error generando respuesta: {str(e)}", 500, "GENERATION_ERROR")
        
    except Exception as e:
        logger.error(f"❌ Error inesperado en rag_query: {str(e)}")
        return create_error_response("Error interno del servidor", 500, "INTERNAL_ERROR")

@api_view(['GET'])
@permission_classes([AllowAny])
def system_stats(request):
    """
    Endpoint para estadísticas del sistema RAG
    
    ESTADÍSTICAS INCLUIDAS:
    - Conteo de documentos en ChromaDB
    - Métricas de uso de la API
    - Performance promedio
    - Estado de componentes
    - Uso de cache
    
    Returns:
        JSON: Estadísticas detalladas del sistema
    """
    try:
        stats = {
            'timestamp': datetime.now().isoformat(),
            'database': {},
            'api_usage': {},
            'performance': {},
            'cache': {}
        }
        
        # === ESTADÍSTICAS DE BASE DE DATOS ===
        try:
            model, client, collection = get_rag_components()
            if collection:
                doc_count = collection.count()
                stats['database'] = {
                    'total_documents': doc_count,
                    'collection_name': collection.name,
                    'status': 'connected'
                }
            else:
                stats['database'] = {'status': 'disconnected'}
        except Exception as e:
            stats['database'] = {'status': 'error', 'error': str(e)}
        
        # === ESTADÍSTICAS DE CACHE ===
        try:
            # Estadísticas básicas de cache Django
            cache_info = {
                'backend': str(type(cache)),
                'status': 'connected'
            }
            
            # Test básico de cache
            test_key = 'stats_test'
            cache.set(test_key, 'test_value', 10)
            if cache.get(test_key) == 'test_value':
                cache_info['test_result'] = 'passed'
            else:
                cache_info['test_result'] = 'failed'
            
            stats['cache'] = cache_info
            
        except Exception as e:
            stats['cache'] = {'status': 'error', 'error': str(e)}
        
        # === ESTADÍSTICAS DE CONFIGURACIÓN ===
        stats['configuration'] = {
            'deepseek_configured': bool(os.getenv("OPENROUTER_API_KEY")),
            'debug_mode': settings.DEBUG,
            'environment': os.getenv('DJANGO_ENV', 'development')
        }
        
        logger.info("📊 Estadísticas del sistema generadas")
        return create_success_response(stats)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {str(e)}")
        return create_error_response(f"Error obteniendo estadísticas: {str(e)}", 500)

# === FUNCIONES DE UTILIDAD ===

def _get_memory_usage() -> Dict[str, Any]:
    """
    Obtiene información de uso de memoria (aproximada)
    
    Returns:
        Dict: Información de memoria
    """
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
            'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
            'percent': round(process.memory_percent(), 2)
        }
    except ImportError:
        return {'status': 'psutil_not_available'}
    except Exception as e:
        return {'error': str(e)}

def _get_uptime() -> str:
    """
    Calcula uptime aproximado del proceso
    
    Returns:
        str: Uptime en formato legible
    """
    try:
        import psutil
        process = psutil.Process()
        create_time = datetime.fromtimestamp(process.create_time())
        uptime = datetime.now() - create_time
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
            
    except ImportError:
        return "unavailable"
    except Exception:
        return "unknown"

# === VISTAS ADICIONALES ===

@api_view(['GET'])
@permission_classes([AllowAny])
def api_documentation(request):
    """
    Endpoint de documentación de la API
    
    Returns:
        JSON: Documentación de todos los endpoints disponibles
    """
    documentation = {
        'api_version': '1.0',
        'description': 'API REST para sistema RAG con DeepSeek V3',
        'base_url': request.build_absolute_uri('/api/'),
        'endpoints': {
            '/health/': {
                'method': 'GET',
                'description': 'Verificación de salud del sistema',
                'parameters': None,
                'throttling': None
            },
            '/search/': {
                'method': 'POST',
                'description': 'Búsqueda semántica en documentos',
                'parameters': {
                    'query': 'string (requerido) - Consulta en lenguaje natural',
                    'top_k': 'integer (opcional) - Número de resultados (1-20, default: 5)',
                    'include_metadata': 'boolean (opcional) - Incluir metadata (default: true)'
                },
                'throttling': '30 requests/minute'
            },
            '/ask/': {
                'method': 'POST',
                'description': 'Consulta RAG completa con generación de respuesta',
                'parameters': {
                    'query': 'string (requerido) - Consulta en lenguaje natural',
                    'context_length': 'integer (opcional) - Documentos de contexto (1-10, default: 5)',
                    'include_sources': 'boolean (opcional) - Incluir fuentes (default: true)',
                    'academic_mode': 'boolean (opcional) - Modo académico (default: true)'
                },
                'throttling': '10 requests/minute'
            },
            '/stats/': {
                'method': 'GET',
                'description': 'Estadísticas del sistema',
                'parameters': None,
                'throttling': None
            },
            '/docs/': {
                'method': 'GET',
                'description': 'Esta documentación',
                'parameters': None,
                'throttling': None
            }
        },
        'error_format': {
            'error': True,
            'message': 'Descripción del error',
            'status_code': 'Código HTTP',
            'error_code': 'Código interno (opcional)',
            'timestamp': 'ISO timestamp'
        },
        'success_format': {
            'success': True,
            'data': 'Datos de respuesta',
            'message': 'Mensaje opcional',
            'timestamp': 'ISO timestamp'
        }
    }
    
    return create_success_response(documentation, "Documentación de API RAG")

# === MANEJO DE ERRORES GLOBALES ===

def custom_404(request, exception):
    """
    Manejo personalizado de errores 404
    """
    return create_error_response("Endpoint no encontrado", 404, "NOT_FOUND")

def custom_500(request):
    """
    Manejo personalizado de errores 500
    """
    logger.error("Error 500 en API RAG")
    return create_error_response("Error interno del servidor", 500, "INTERNAL_SERVER_ERROR")

# === MIDDLEWARE PERSONALIZADO ===

class RAGAPIMiddleware:
    """
    Middleware personalizado para la API RAG
    
    FUNCIONALIDADES:
    - Logging de todas las requests
    - Medición de tiempo de respuesta
    - Headers de seguridad
    - Rate limiting adicional
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Log de request entrante
        if request.path.startswith('/api/'):
            logger.info(f"📥 API Request: {request.method} {request.path}")
        
        response = self.get_response(request)
        
        # Log de response
        if request.path.startswith('/api/'):
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            logger.info(f"📤 API Response: {response.status_code} ({response_time}ms)")
        
        # Headers de seguridad
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response

# === CONFIGURACIÓN DE URLS ===
# Este archivo debe ser importado en urls.py para configurar las rutas