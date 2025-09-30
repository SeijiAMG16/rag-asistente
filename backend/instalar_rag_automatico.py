"""
INSTALACIÓN AUTOMÁTICA DEL SISTEMA RAG OPTIMIZADO
=================================================
Ejecuta este script en la PC de tu compañero
"""

import subprocess
import sys
import os
from pathlib import Path

def install_package(package):
    """Instalar un paquete con pip"""
    print(f"📦 Instalando {package}...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", package, "--user", "--quiet"
        ])
        print(f"✅ {package} instalado")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Error instalando {package}")
        return False

def main():
    print("🚀 INSTALACIÓN AUTOMÁTICA - SISTEMA RAG OPTIMIZADO")
    print("=" * 55)
    print()
    
    # Lista de dependencias críticas
    dependencies = [
        "sentence-transformers",
        "chromadb", 
        "rank-bm25",
        "numpy",
        "torch"
    ]
    
    print("📦 Instalando dependencias...")
    failed = []
    
    for dep in dependencies:
        if not install_package(dep):
            failed.append(dep)
    
    if failed:
        print(f"\n❌ Fallaron: {', '.join(failed)}")
        print("💡 Instalar manualmente con:")
        for dep in failed:
            print(f"   pip install {dep}")
    else:
        print("\n✅ Todas las dependencias instaladas")
    
    # Verificar sistema
    print("\n🧪 Probando sistema RAG...")
    try:
        # Añadir directorio actual al path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from utils.optimized_rag_system import OptimizedRAGSystem
        rag = OptimizedRAGSystem()
        
        # Verificar ChromaDB
        if not Path("../chroma_db_simple").exists() and not Path("chroma_db_simple").exists():
            print("⚠️ Base de datos no encontrada. Ejecutando ETL...")
            subprocess.run([sys.executable, "etl_rag_complete.py", "--chunk-size", "800"])
        
        # Inicializar
        rag._initialize_models()
        stats = rag.get_system_stats()
        
        print(f"✅ Sistema RAG funcional: {stats['collection_count']} documentos")
        
        # Prueba básica
        results = rag.advanced_search("test", 1)
        print(f"✅ Búsqueda funcional: {len(results)} resultados")
        
        print("\n🎉 ¡INSTALACIÓN EXITOSA!")
        print("💡 Ahora puedes ejecutar: python start_rag.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Creando sistema de respaldo...")
        
        # Crear sistema simple
        simple_content = '''
from sentence_transformers import SentenceTransformer
import chromadb
from pathlib import Path

class SimpleRAG:
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        self.client = chromadb.PersistentClient(path="../chroma_db_simple")
        self.collection = self.client.get_collection("simple_rag_docs")
    
    def advanced_search(self, query, top_k=5):
        embedding = self.model.encode(query, normalize_embeddings=True)
        results = self.collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )
        return [{
            'texto': doc,
            'archivo': meta.get('archivo', 'Unknown'),
            'similarity_score': round(1 - dist, 4),
            'final_score': round(1 - dist, 4)
        } for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )]

def get_optimized_rag():
    return SimpleRAG()
'''
        
        try:
            with open('utils/simple_rag_backup.py', 'w') as f:
                f.write(simple_content)
            print("✅ Sistema de respaldo creado en utils/simple_rag_backup.py")
            print("💡 Usar: from utils.simple_rag_backup import get_optimized_rag")
        except Exception as e2:
            print(f"❌ Error creando respaldo: {e2}")

if __name__ == "__main__":
    main()