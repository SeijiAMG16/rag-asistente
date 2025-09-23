"""
Script de consulta para el sistema RAG
Busca documentos relevantes en ChromaDB usando embeddings
"""

import os
import sys
from datetime import datetime

# Configuración de paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import *

# Imports para RAG
from sentence_transformers import SentenceTransformer
import chromadb

class RAGQuery:
    """Clase para realizar consultas al sistema RAG"""
    
    def __init__(self):
        """Inicializar el sistema de consultas"""
        self.model = None
        self.client = None
        self.collection = None
        self.setup()
    
    def setup(self):
        """Configurar ChromaDB y modelo de embeddings"""
        try:
            # Cargar modelo de embeddings
            print("🤖 Cargando modelo de embeddings...")
            self.model = SentenceTransformer(EMBEDDING_MODEL)
            
            # Configurar ChromaDB
            print("🗃️ Conectando a ChromaDB...")
            self.client = chromadb.PersistentClient(path=CHROMA_DIR)
            
            try:
                self.collection = self.client.get_collection(COLLECTION_NAME)
                count = self.collection.count()
                print(f"✅ Conectado a colección '{COLLECTION_NAME}' ({count} documentos)")
            except Exception:
                print(f"❌ Error: Colección '{COLLECTION_NAME}' no encontrada")
                print("💡 Ejecuta primero el pipeline de ingesta")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error en configuración: {e}")
            return False
    
    def search(self, query: str, n_results: int = 5):
        """Buscar documentos relevantes"""
        try:
            print(f"\n🔍 Buscando: '{query}'")
            
            # Generar embedding de la consulta
            embedding = self.model.encode(query).tolist()
            
            # Buscar en ChromaDB
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                include=["metadatas", "documents", "distances"]
            )
            
            return results
            
        except Exception as e:
            print(f"❌ Error en búsqueda: {e}")
            return None
    
    def format_results(self, results, query: str):
        """Formatear y mostrar resultados"""
        if not results or not results["documents"][0]:
            print("❌ No se encontraron resultados")
            return
        
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results.get("distances", [None])[0] if results.get("distances") else [None] * len(documents)
        
        print(f"\n📋 Resultados para: '{query}'")
        print("=" * 60)
        
        for i, (doc, meta, distance) in enumerate(zip(documents, metadatas, distances), 1):
            filename = meta.get('filename', 'Desconocido')
            chunk_index = meta.get('chunk_index', 0)
            
            print(f"\n📄 Resultado {i}:")
            print(f"   📁 Archivo: {filename}")
            print(f"   🔢 Chunk: {chunk_index}")
            if distance is not None:
                similarity = 1 - distance
                print(f"   📊 Similaridad: {similarity:.3f}")
            
            print(f"   📝 Contenido:")
            # Mostrar texto con límite
            preview = doc[:400] if len(doc) > 400 else doc
            if len(doc) > 400:
                preview += "..."
            
            # Agregar sangría
            preview_lines = preview.split('\n')
            for line in preview_lines:
                print(f"      {line}")
            
            print()
    
    def interactive_mode(self):
        """Modo interactivo de consultas"""
        print("\n🎯 MODO INTERACTIVO DE CONSULTAS RAG")
        print("=" * 40)
        print("Escribe tus preguntas o 'salir' para terminar")
        print()
        
        while True:
            try:
                query = input("🔍 Consulta: ").strip()
                
                if query.lower() in ['salir', 'exit', 'quit', '']:
                    break
                
                # Realizar búsqueda
                start_time = datetime.now()
                results = self.search(query)
                end_time = datetime.now()
                
                if results:
                    self.format_results(results, query)
                    duration = (end_time - start_time).total_seconds()
                    print(f"⏱️ Tiempo de búsqueda: {duration:.3f} segundos")
                
                print("\n" + "-" * 40)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n👋 ¡Hasta luego!")

def main():
    """Función principal"""
    try:
        # Crear instancia de RAG
        rag = RAGQuery()
        
        # Verificar configuración
        if not rag.setup():
            return 1
        
        # Verificar argumentos de línea de comandos
        if len(sys.argv) > 1:
            # Consulta directa desde argumentos
            query = " ".join(sys.argv[1:])
            results = rag.search(query)
            if results:
                rag.format_results(results, query)
        else:
            # Modo interactivo
            rag.interactive_mode()
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
