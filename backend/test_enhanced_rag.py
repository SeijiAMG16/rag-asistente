#!/usr/bin/env python
"""
Test script para el sistema RAG mejorado con fuentes
"""
import os
import sys
import django
from pathlib import Path

# Añadir el directorio backend al path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Ahora importar después de configurar Django
from utils.rag_utils import generate_rag_response, perform_semantic_search


def test_rag_with_sources():
    """Test del sistema RAG con fuentes integradas"""
    
    test_queries = [
        "¿Qué es la inteligencia artificial?",
        "¿Cómo funciona el machine learning?",
        "¿Qué son las redes neuronales?",
        "Explica el procesamiento de lenguaje natural"
    ]
    
    print("🧪 PROBANDO SISTEMA RAG MEJORADO CON FUENTES")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 Test {i}: {query}")
        print("-" * 40)
        
        try:
            # Primero hacer búsqueda semántica
            print(f"🔍 Realizando búsqueda semántica...")
            search_results = perform_semantic_search(query, top_k=5)
            
            if not search_results:
                print("⚠️ No se encontraron documentos relevantes")
                continue
                
            print(f"📚 Encontrados {len(search_results)} documentos relevantes")
            
            # Generar respuesta con fuentes
            result = generate_rag_response(query, search_results)
            
            # Verificar el formato de la respuesta
            if isinstance(result, dict):
                print(f"✅ Respuesta estructurada recibida")
                respuesta = result.get('respuesta', 'N/A')
                print(f"📝 Respuesta ({len(respuesta)} caracteres): {respuesta[:200]}...")
                print(f"📚 Total fuentes: {result.get('total_fuentes', 0)}")
                
                # Mostrar fuentes
                fuentes = result.get('fuentes', [])
                if fuentes:
                    print(f"🔍 Fuentes utilizadas:")
                    for j, fuente in enumerate(fuentes[:3], 1):  # Mostrar solo las primeras 3
                        print(f"  {j}. Archivo: {fuente.get('archivo', 'N/A')}")
                        print(f"     Similitud: {fuente.get('similarity_score', 0):.3f}")
                        print(f"     Contenido: {fuente.get('texto_preview', '')[:100]}...")
                        print()
                else:
                    print("⚠️ No se encontraron fuentes")
                    
            elif isinstance(result, str):
                print(f"⚠️ Respuesta en formato string: {result[:200]}...")
            else:
                print(f"❌ Formato de respuesta inesperado: {type(result)}")
                
        except Exception as e:
            print(f"❌ Error en consulta: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*60)


if __name__ == "__main__":
    test_rag_with_sources()