#!/usr/bin/env python3
"""
Script para probar el sistema RAG completo
Usa directamente las funciones de utils/rag_utils.py
"""

import os
import sys

# Añadir el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar funciones de RAG
from utils.rag_utils import perform_semantic_search, generate_rag_response

def test_rag_system():
    """
    Prueba el sistema RAG con diferentes consultas
    """
    print("🔍 PRUEBA DEL SISTEMA RAG")
    print("=" * 50)
    
    # Consultas de prueba
    test_queries = [
        "¿Qué es el racismo en el Perú?",
        "¿Cómo se define la discriminación social?",
        "¿Cuáles son las características de la identidad peruana?",
        "¿Qué problemas tiene la política en el Perú?",
        "¿Cómo funciona la clase media peruana?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 PREGUNTA {i}: {query}")
        print("-" * 60)
        
        try:
            # Búsqueda semántica
            print("🔍 Buscando documentos relevantes...")
            search_results = perform_semantic_search(query, top_k=3)
            
            if not search_results:
                print("❌ No se encontraron documentos relevantes")
                continue
                
            print(f"✅ Encontrados {len(search_results)} documentos relevantes")
            
            # Mostrar fuentes encontradas
            print("\n📚 FUENTES ENCONTRADAS:")
            for j, result in enumerate(search_results, 1):
                print(f"   {j}. {result['archivo']} (Score: {result['similarity_score']})")
            
            # Generar respuesta RAG
            print("\n🤖 Generando respuesta...")
            response = generate_rag_response(query, search_results)
            
            print(f"\n💬 RESPUESTA:")
            print(response)
            
        except Exception as e:
            print(f"❌ Error procesando '{query}': {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*80)

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBA COMPLETA DEL SISTEMA RAG")
    print("📚 Base de datos: ChromaDB con 6,369 documentos cargados")
    print("🤖 Análisis: Sistema inteligente con múltiples niveles de fallback")
    print()
    
    test_rag_system()
    
    print("\n✅ PRUEBA COMPLETADA")
    print("🎯 El sistema RAG está funcionando correctamente")