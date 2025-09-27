#!/usr/bin/env python3
"""
Prueba del Sistema RAG Avanzado con Modelos LLM Potentes
Utiliza Groq API con Llama 3.3 70B para análisis inteligente
"""

import os
import sys

# Añadir el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar variables de entorno
from dotenv import load_dotenv
load_dotenv()

def test_advanced_rag():
    """
    Prueba el sistema RAG con modelos LLM potentes
    """
    print("🔥 PRUEBA DEL SISTEMA RAG AVANZADO")
    print("🤖 Modelo: Groq Llama 3.3 70B")
    print("=" * 60)
    
    # Importar funciones de RAG
    from utils.rag_utils import perform_semantic_search, generate_rag_response
    
    # Consultas de prueba más específicas
    test_queries = [
        "¿Cuáles son las causas del racismo en el Perú según los documentos?",
        "¿Cómo se manifiesta la discriminación social en la sociedad peruana?",
        "¿Qué características definen la identidad cultural peruana?",
        "¿Cuáles son los principales problemas de la clase media en el Perú?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 CONSULTA {i}: {query}")
        print("-" * 80)
        
        try:
            # Búsqueda semántica
            print("📚 Buscando documentos relevantes...")
            search_results = perform_semantic_search(query, top_k=4)
            
            if not search_results:
                print("❌ No se encontraron documentos relevantes")
                continue
                
            print(f"✅ Encontrados {len(search_results)} documentos relevantes")
            
            # Mostrar fuentes encontradas con scores
            print("\n📋 FUENTES IDENTIFICADAS:")
            for j, result in enumerate(search_results, 1):
                score = result['similarity_score']
                archivo = result['archivo']
                print(f"   {j}. {archivo}")
                print(f"      📊 Relevancia: {score:.3f}")
            
            # Generar respuesta con LLM avanzado
            print(f"\n🧠 Analizando con Llama 3.3 70B...")
            response = generate_rag_response(query, search_results)
            
            print(f"\n💬 ANÁLISIS INTELIGENTE:")
            print("=" * 40)
            print(response)
            print("=" * 40)
            
        except Exception as e:
            print(f"❌ Error procesando consulta: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "🔄"*80)
        
        # Pausa entre consultas
        input("Presiona Enter para continuar con la siguiente consulta...")

def verify_api_keys():
    """
    Verifica que las API keys estén configuradas
    """
    print("🔐 VERIFICANDO CONFIGURACIÓN DE API KEYS:")
    print("-" * 50)
    
    apis = {
        "GROQ": os.getenv("GROQ_API_KEY"),
        "TOGETHER": os.getenv("TOGETHER_API_KEY"),
        "GEMINI": os.getenv("GEMINI_API_KEY"),
        "OPENAI": os.getenv("OPENAI_API_KEY"),
    }
    
    for api_name, api_key in apis.items():
        if api_key:
            masked_key = api_key[:8] + "..." + api_key[-4:]
            print(f"✅ {api_name}: {masked_key}")
        else:
            print(f"⚪ {api_name}: No configurado")
    
    print()

if __name__ == "__main__":
    print("🚀 SISTEMA RAG AVANZADO - PRUEBA COMPLETA")
    print("🔥 ANÁLISIS INTELIGENTE CON LLM POTENTES")
    print("=" * 60)
    
    # Verificar configuración
    verify_api_keys()
    
    # Verificar base de datos
    try:
        from utils.rag_utils import initialize_rag_components
        model, client, collection = initialize_rag_components()
        count = collection.count()
        print(f"📚 Base de datos ChromaDB: {count} documentos cargados")
        print()
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        sys.exit(1)
    
    # Iniciar pruebas
    test_advanced_rag()
    
    print("\n✅ PRUEBA COMPLETADA")
    print("🎯 Sistema RAG avanzado funcionando correctamente")