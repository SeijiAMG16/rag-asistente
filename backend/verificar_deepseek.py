#!/usr/bin/env python3
"""
🧪 VERIFICADOR COMPLETO DE DEEPSEEK V3.1
========================================

Script para verificar que tu compañero pueda usar DeepSeek correctamente.
Ejecuta todas las pruebas necesarias en orden.

Uso: python verificar_deepseek.py
"""

import os
import sys
import requests
import json
from pathlib import Path

def print_header(title):
    print(f"\n{'='*50}")
    print(f"🧪 {title}")
    print(f"{'='*50}")

def print_step(step, description):
    print(f"\n{step} {description}")
    print("-" * 30)

def test_environment():
    """Verificar variables de entorno"""
    print_step("1️⃣", "VERIFICANDO VARIABLES DE ENTORNO")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ dotenv importado correctamente")
    except ImportError:
        print("❌ python-dotenv no instalado")
        print("   Instalar con: pip install python-dotenv")
        return False
    
    # Verificar API Key
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    if openrouter_key:
        print(f"✅ OPENROUTER_API_KEY configurada ({len(openrouter_key)} caracteres)")
        return openrouter_key
    else:
        print("❌ OPENROUTER_API_KEY no encontrada")
        print("   Verificar archivo .env en backend/")
        return False

def test_deepseek_connection(api_key):
    """Probar conexión directa con DeepSeek"""
    print_step("2️⃣", "PROBANDO CONEXIÓN CON DEEPSEEK V3.1")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:8000',
        'X-Title': 'RAG Asistente'
    }
    
    payload = {
        'model': 'deepseek/deepseek-chat-v3.1',  # Modelo corregido
        'messages': [
            {'role': 'user', 'content': 'Hola DeepSeek, confirma que estás funcionando correctamente.'}
        ],
        'max_tokens': 100,
        'temperature': 0.7
    }
    
    try:
        print("📡 Enviando request a OpenRouter...")
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"✅ DeepSeek responde: {content}")
                
                if 'usage' in result:
                    usage = result['usage']
                    print(f"📊 Tokens usados: {usage}")
                
                return True
            else:
                print("❌ Respuesta sin contenido válido")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en conexión: {e}")
        return False

def test_rag_system():
    """Probar sistema RAG completo"""
    print_step("3️⃣", "PROBANDO SISTEMA RAG COMPLETO")
    
    try:
        # Configurar Django
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
        django.setup()
        print("✅ Django configurado")
        
        # Importar funciones RAG
        from utils.rag_utils import perform_semantic_search, generate_rag_response
        print("✅ Funciones RAG importadas")
        
        # Probar búsqueda
        query = "Qué dice sobre las clases medias en el Perú?"
        print(f"📝 Consulta de prueba: {query}")
        
        search_results = perform_semantic_search(query, top_k=3)
        print(f"✅ Búsqueda semántica: {len(search_results)} resultados")
        
        if len(search_results) == 0:
            print("⚠️ No se encontraron documentos - verificar ChromaDB")
            return False
        
        # Generar respuesta con DeepSeek
        print("🤖 Generando respuesta con DeepSeek...")
        response = generate_rag_response(query, search_results)
        
        if response and len(response) > 100:
            print(f"✅ Respuesta RAG generada: {len(response)} caracteres")
            print(f"📝 Muestra: {response[:200]}...")
            return True
        else:
            print("❌ Respuesta RAG vacía o muy corta")
            return False
            
    except Exception as e:
        print(f"❌ Error en sistema RAG: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """Verificar dependencias críticas"""
    print_step("4️⃣", "VERIFICANDO DEPENDENCIAS")
    
    dependencies = [
        ('sentence_transformers', 'sentence-transformers'),
        ('chromadb', 'chromadb'),
        ('numpy', 'numpy'),
        ('requests', 'requests'),
        ('django', 'Django')
    ]
    
    missing = []
    
    for package, install_name in dependencies:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - instalar con: pip install {install_name}")
            missing.append(install_name)
    
    if missing:
        print(f"\n🔧 Instalar dependencias faltantes:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def main():
    """Función principal"""
    print_header("VERIFICADOR DE DEEPSEEK V3.1 PARA COMPAÑERO")
    
    # Test 1: Environment
    api_key = test_environment()
    if not api_key:
        print("\n❌ FALLO EN CONFIGURACIÓN DE ENTORNO")
        return False
    
    # Test 2: Dependencies
    if not test_dependencies():
        print("\n❌ FALLO EN DEPENDENCIAS")
        return False
    
    # Test 3: DeepSeek Connection
    if not test_deepseek_connection(api_key):
        print("\n❌ FALLO EN CONEXIÓN CON DEEPSEEK")
        return False
    
    # Test 4: RAG System
    if not test_rag_system():
        print("\n❌ FALLO EN SISTEMA RAG")
        return False
    
    # ¡Todo exitoso!
    print_header("🎉 VERIFICACIÓN COMPLETA EXITOSA")
    print("✅ Variables de entorno configuradas")
    print("✅ DeepSeek V3.1 conectado y funcionando")
    print("✅ Sistema RAG operativo")
    print("✅ Todas las dependencias instaladas")
    print("\n🚀 ¡TU COMPAÑERO PUEDE USAR DEEPSEEK SIN PROBLEMAS!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)