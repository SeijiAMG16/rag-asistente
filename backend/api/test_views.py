"""
Testing API Views para el Sistema RAG
Endpoints para probar el sistema desde la interfaz web
"""

import logging
import time
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar el sistema RAG
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def test_rag_simple(request):
    """Test simple del sistema RAG"""
    try:
        from simple_rag_system import initialize_simple_rag
        
        # Obtener pregunta del parámetro query o usar pregunta por defecto
        question = request.GET.get('q', '¿Cómo se manifiesta el racismo en el Perú según los documentos?')
        
        logger.info(f"🧪 Test RAG Simple - Pregunta: {question}")
        
        # Inicializar sistema
        rag_system = initialize_simple_rag()
        
        # Realizar consulta
        start_time = time.time()
        result = rag_system.query(question)
        test_time = time.time() - start_time
        
        # Obtener estadísticas del sistema
        stats = rag_system.get_stats()
        
        response_data = {
            "success": True,
            "test_type": "simple_test",
            "question": question,
            "answer": result['answer'],
            "sources": result.get('sources', []),
            "metadata": result.get('metadata', {}),
            "system_stats": stats,
            "test_duration": round(test_time, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Error en test RAG simple: {e}")
        return Response({
            "success": False,
            "error": str(e),
            "error_type": "rag_test_error"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def test_rag_multiple(request):
    """Test con múltiples preguntas predefinidas"""
    try:
        from simple_rag_system import initialize_simple_rag
        
        # Preguntas de prueba
        test_questions = [
            "¿Cómo se manifiesta el racismo en el Perú?",
            "¿Qué análisis hacen sobre la identidad cultural peruana?",
            "¿Cuáles son las características del mestizaje según los documentos?",
            "¿Qué dicen sobre la discriminación social?",
            "¿Cómo describen la política peruana?"
        ]
        
        logger.info("🧪 Test RAG Múltiple iniciado")
        
        # Inicializar sistema una sola vez
        rag_system = initialize_simple_rag()
        stats = rag_system.get_stats()
        
        results = []
        total_start_time = time.time()
        
        for i, question in enumerate(test_questions, 1):
            try:
                start_time = time.time()
                result = rag_system.query(question)
                query_time = time.time() - start_time
                
                # Resumir respuesta para el overview
                answer_preview = result['answer']
                if len(answer_preview) > 300:
                    answer_preview = answer_preview[:300] + "..."
                
                results.append({
                    "question_number": i,
                    "question": question,
                    "answer": result['answer'],
                    "answer_preview": answer_preview,
                    "sources_count": len(result.get('sources', [])),
                    "sources": result.get('sources', [])[:2],  # Solo las 2 primeras fuentes
                    "query_time": round(query_time, 2),
                    "metadata": result.get('metadata', {})
                })
                
            except Exception as e:
                logger.error(f"❌ Error en pregunta {i}: {e}")
                results.append({
                    "question_number": i,
                    "question": question,
                    "error": str(e),
                    "query_time": 0
                })
        
        total_time = time.time() - total_start_time
        
        response_data = {
            "success": True,
            "test_type": "multiple_test",
            "total_questions": len(test_questions),
            "results": results,
            "system_stats": stats,
            "total_duration": round(total_time, 2),
            "average_time_per_query": round(total_time / len(test_questions), 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Error en test RAG múltiple: {e}")
        return Response({
            "success": False,
            "error": str(e),
            "error_type": "multiple_test_error"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def rag_system_status(request):
    """Obtener estado completo del sistema RAG"""
    try:
        from simple_rag_system import initialize_simple_rag
        
        logger.info("🔍 Obteniendo estado del sistema RAG")
        
        # Intentar inicializar sistema
        try:
            rag_system = initialize_simple_rag()
            system_initialized = True
            initialization_error = None
        except Exception as init_error:
            rag_system = None
            system_initialized = False
            initialization_error = str(init_error)
        
        # Obtener estadísticas si el sistema está inicializado
        if system_initialized and rag_system:
            stats = rag_system.get_stats()
            
            # Test rápido de conectividad
            try:
                test_result = rag_system.query("test")
                connectivity_test = "success"
            except Exception as test_error:
                connectivity_test = f"failed: {str(test_error)}"
        else:
            stats = {
                "total_documents": 0,
                "system_type": "unknown",
                "llm_available": False,
                "status": "error"
            }
            connectivity_test = "failed: system not initialized"
        
        response_data = {
            "success": True,
            "system_initialized": system_initialized,
            "initialization_error": initialization_error,
            "connectivity_test": connectivity_test,
            "system_stats": stats,
            "available_endpoints": [
                "/api/test/rag/simple",
                "/api/test/rag/multiple", 
                "/api/test/rag/status",
                "/api/chat/simple"
            ],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado del sistema: {e}")
        return Response({
            "success": False,
            "error": str(e),
            "error_type": "system_status_error"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def test_custom_question(request):
    """Test con pregunta personalizada del usuario"""
    try:
        from simple_rag_system import initialize_simple_rag
        
        # Obtener pregunta del request
        question = request.data.get('question', '').strip()
        
        if not question:
            return Response({
                "success": False,
                "error": "Pregunta requerida",
                "error_type": "validation_error"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"🧪 Test pregunta personalizada: {question}")
        
        # Inicializar sistema
        rag_system = initialize_simple_rag()
        
        # Realizar consulta con análisis detallado
        start_time = time.time()
        result = rag_system.query(question)
        query_time = time.time() - start_time
        
        # Análisis de la calidad de la respuesta
        answer_length = len(result['answer'])
        sources_count = len(result.get('sources', []))
        
        quality_indicators = {
            "answer_length": answer_length,
            "sources_found": sources_count,
            "response_quality": "good" if answer_length > 200 and sources_count > 0 else "limited",
            "analysis_structured": "**" in result['answer'],  # Verifica si tiene estructura
        }
        
        response_data = {
            "success": True,
            "test_type": "custom_question",
            "question": question,
            "answer": result['answer'],
            "sources": result.get('sources', []),
            "metadata": result.get('metadata', {}),
            "quality_indicators": quality_indicators,
            "query_time": round(query_time, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Error en test pregunta personalizada: {e}")
        return Response({
            "success": False,
            "error": str(e),
            "error_type": "custom_question_error"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)