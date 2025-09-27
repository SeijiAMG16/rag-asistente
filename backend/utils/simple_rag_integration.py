"""
Integración simplificada del sistema RAG con Django
"""

import os
import sys
from pathlib import Path

# Añadir el sistema RAG al path de Django
current_dir = Path(__file__).parent
backend_dir = current_dir.parent  # backend/
project_root = backend_dir.parent  # rag-asistente/
sys.path.append(str(project_root))

try:
    from simple_rag_system import SimpleRAGSystem, initialize_simple_rag
    RAG_AVAILABLE = True
    SimpleRAGSystemType = SimpleRAGSystem
    print("✅ Sistema RAG con Análisis Inteligente importado correctamente")
except ImportError as e:
    print(f"Warning: RAG system not available - {e}")
    RAG_AVAILABLE = False
    SimpleRAGSystemType = None

# Instancia global del sistema RAG
_rag_system = None

def get_rag_system():
    """Obtener instancia del sistema RAG"""
    global _rag_system
    
    if not RAG_AVAILABLE:
        raise Exception("Sistema RAG no disponible")
    
    if _rag_system is None:
        _rag_system = initialize_simple_rag()
    
    return _rag_system

def query_rag_simple(question: str) -> dict:
    """Realizar consulta al sistema RAG desde Django"""
    try:
        if not RAG_AVAILABLE:
            return {
                "answer": "Sistema RAG no disponible. Revisa la configuración.",
                "error": "RAG_NOT_AVAILABLE",
                "sources": [],
                "metadata": {"error": True}
            }
        
        rag_system = get_rag_system()
        response = rag_system.query(question)
        
        # Formatear respuesta para Django
        return {
            "answer": response["answer"],
            "sources": response.get("sources", []),
            "metadata": {
                "timestamp": response.get("metadata", {}).get("timestamp"),
                "memory_usage": response.get("metadata", {}).get("memory_usage", 0),
                "documents_found": response.get("metadata", {}).get("documents_found", 0),
                "system_type": "simple_rag"
            }
        }
        
    except Exception as e:
        return {
            "answer": f"Error procesando la consulta: {str(e)}",
            "error": str(e),
            "sources": [],
            "metadata": {"error": True}
        }

def get_rag_stats_simple() -> dict:
    """Obtener estadísticas del sistema RAG"""
    try:
        if not RAG_AVAILABLE:
            return {
                "status": "unavailable",
                "error": "Sistema RAG no disponible"
            }
        
        rag_system = get_rag_system()
        stats = rag_system.get_stats()
        
        return {
            "status": "active",
            "stats": {
                "documents_count": stats.get("documents_count", 0),
                "memory_usage_gb": stats.get("memory_usage_gb", 0),
                "embeddings_loaded": stats.get("embeddings_loaded", False),
                "vectordb_loaded": stats.get("vectordb_loaded", False),
                "llm_loaded": stats.get("llm_loaded", False),
                "system_type": "simple_rag"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def test_rag_integration():
    """Test de integración RAG"""
    print("🧪 Testing integración RAG con Django...")
    
    # Test estadísticas
    stats = get_rag_stats_simple()
    print(f"📊 Stats: {stats}")
    
    # Test consulta
    if stats.get("status") == "active":
        response = query_rag_simple("¿Qué información tienes disponible?")
        print(f"🤖 Respuesta: {response['answer'][:100]}...")
        print(f"📚 Fuentes: {len(response['sources'])}")
    
    print("✅ Test de integración completado")

if __name__ == "__main__":
    test_rag_integration()