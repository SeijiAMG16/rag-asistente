#!/usr/bin/env python3
"""
DIAGNÓSTICO COMPLETO DEL SISTEMA RAG OPTIMIZADO
===============================================
Verifica todas las dependencias y configuraciones necesarias
"""

import os
import sys
import importlib
import traceback
from pathlib import Path

def test_basic_imports():
    """Verificar importaciones básicas"""
    print("🔍 VERIFICANDO IMPORTACIONES BÁSICAS")
    print("=" * 50)
    
    basic_modules = [
        'os', 'sys', 'json', 'pathlib', 'datetime', 'threading',
        'functools', 'hashlib', 'pickle', 'collections', 're'
    ]
    
    for module in basic_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")

def test_data_science_imports():
    """Verificar librerías de ciencia de datos"""
    print("\n🔬 VERIFICANDO LIBRERÍAS DE CIENCIA DE DATOS")
    print("=" * 50)
    
    data_modules = {
        'numpy': 'pip install numpy',
        'sentence_transformers': 'pip install sentence-transformers',
        'chromadb': 'pip install chromadb',
        'rank_bm25': 'pip install rank-bm25'
    }
    
    for module, install_cmd in data_modules.items():
        try:
            mod = importlib.import_module(module)
            if hasattr(mod, '__version__'):
                print(f"✅ {module} (v{mod.__version__})")
            else:
                print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: FALTANTE")
            print(f"   💡 Instalar con: {install_cmd}")

def test_file_paths():
    """Verificar rutas de archivos"""
    print("\n📁 VERIFICANDO RUTAS DE ARCHIVOS")
    print("=" * 50)
    
    current_dir = Path(__file__).parent
    backend_dir = current_dir.parent if current_dir.name == 'utils' else current_dir
    project_dir = backend_dir.parent if backend_dir.name == 'backend' else backend_dir
    
    paths_to_check = [
        ('Directorio actual', current_dir),
        ('Directorio backend', backend_dir),
        ('Directorio proyecto', project_dir),
        ('ChromaDB simple', project_dir / 'chroma_db_simple'),
        ('ChromaDB backend', backend_dir / 'chroma_db_simple'),
        ('Data PDFs', backend_dir / 'data' / 'pdfs'),
        ('Data texts', backend_dir / 'data' / 'texts'),
    ]
    
    for name, path in paths_to_check:
        if path.exists():
            if path.is_file():
                print(f"✅ {name}: {path} (archivo)")
            else:
                try:
                    count = len(list(path.iterdir())) if path.is_dir() else 0
                    print(f"✅ {name}: {path} ({count} items)")
                except PermissionError:
                    print(f"✅ {name}: {path} (sin permisos de lectura)")
        else:
            print(f"❌ {name}: {path} (NO EXISTE)")

def test_chromadb_connection():
    """Verificar conexión a ChromaDB"""
    print("\n🗄️ VERIFICANDO CONEXIÓN CHROMADB")
    print("=" * 50)
    
    try:
        import chromadb
        print(f"✅ ChromaDB importado (v{chromadb.__version__})")
        
        # Buscar bases de datos
        current_dir = Path(__file__).parent
        backend_dir = current_dir.parent if current_dir.name == 'utils' else current_dir
        project_dir = backend_dir.parent if backend_dir.name == 'backend' else backend_dir
        
        possible_paths = [
            project_dir / 'chroma_db_simple',
            backend_dir / 'chroma_db_simple',
            current_dir / 'chroma_db_simple',
            Path.cwd() / 'chroma_db_simple'
        ]
        
        for path in possible_paths:
            if path.exists():
                print(f"🔍 Probando ChromaDB en: {path}")
                try:
                    client = chromadb.PersistentClient(path=str(path))
                    collections = client.list_collections()
                    print(f"  ✅ Conexión exitosa: {len(collections)} colecciones")
                    
                    for col in collections:
                        try:
                            count = col.count()
                            print(f"    📊 {col.name}: {count} documentos")
                        except Exception as e:
                            print(f"    ⚠️ {col.name}: Error contando ({e})")
                            
                except Exception as e:
                    print(f"  ❌ Error conectando: {e}")
        
    except ImportError as e:
        print(f"❌ ChromaDB no disponible: {e}")
        print("💡 Instalar con: pip install chromadb")

def test_sentence_transformers():
    """Verificar SentenceTransformers"""
    print("\n🤖 VERIFICANDO SENTENCE TRANSFORMERS")
    print("=" * 50)
    
    try:
        from sentence_transformers import SentenceTransformer, CrossEncoder
        print("✅ SentenceTransformers importado")
        
        # Probar modelo básico
        try:
            model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
            test_text = "Esto es una prueba"
            embedding = model.encode(test_text)
            print(f"✅ Modelo de embeddings: {len(embedding)} dimensiones")
        except Exception as e:
            print(f"❌ Error con modelo de embeddings: {e}")
        
        # Probar cross-encoder
        try:
            cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-2-v2')
            test_pairs = [("pregunta", "respuesta")]
            scores = cross_encoder.predict(test_pairs)
            print(f"✅ Cross-encoder: funcional")
        except Exception as e:
            print(f"❌ Error con cross-encoder: {e}")
            
    except ImportError as e:
        print(f"❌ SentenceTransformers no disponible: {e}")
        print("💡 Instalar con: pip install sentence-transformers")

def test_optimized_rag_import():
    """Verificar importación del sistema optimizado"""
    print("\n🚀 VERIFICANDO SISTEMA RAG OPTIMIZADO")
    print("=" * 50)
    
    try:
        # Añadir rutas necesarias
        current_dir = Path(__file__).parent
        backend_dir = current_dir.parent if current_dir.name == 'utils' else current_dir
        
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        
        print(f"📁 Directorio base: {backend_dir}")
        print(f"📁 Python path: {sys.path[:3]}...")
        
        # Intentar importar
        from utils.optimized_rag_system import OptimizedRAGSystem, get_optimized_rag
        print("✅ optimized_rag_system importado exitosamente")
        
        # Crear instancia
        rag = OptimizedRAGSystem()
        print("✅ OptimizedRAGSystem instanciado")
        
        # Verificar inicialización
        rag._initialize_models()
        print("✅ Modelos inicializados")
        
        # Obtener estadísticas
        stats = rag.get_system_stats()
        print(f"✅ Estadísticas obtenidas: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error con sistema optimizado: {e}")
        print(f"📍 Traceback completo:")
        traceback.print_exc()
        return False

def create_simple_fallback():
    """Crear sistema RAG simple como fallback"""
    print("\n🔧 CREANDO SISTEMA RAG SIMPLE DE RESPALDO")
    print("=" * 50)
    
    simple_rag = '''"""
Sistema RAG Simple - Fallback
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SimpleRAGSystem:
    def __init__(self, chroma_path: str = None):
        current_dir = Path(__file__).parent
        backend_dir = current_dir.parent if current_dir.name == 'utils' else current_dir
        project_dir = backend_dir.parent if backend_dir.name == 'backend' else backend_dir
        
        self.chroma_path = chroma_path or str(project_dir / "chroma_db_simple")
        self.embedding_model = None
        self.client = None
        self.collection = None
        self._initialized = False
    
    def _initialize_models(self):
        if self._initialized:
            return
        
        logger.info("🚀 Inicializando sistema RAG simple...")
        
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        except ImportError:
            logger.error("❌ sentence-transformers no disponible")
            raise
        
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = self.client.get_collection("simple_rag_docs")
            logger.info(f"✅ Sistema RAG simple inicializado: {self.collection.count()} documentos")
        except Exception as e:
            logger.error(f"❌ Error inicializando ChromaDB: {e}")
            raise
        
        self._initialized = True
    
    def advanced_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        self._initialize_models()
        
        query_embedding = self.embedding_model.encode(query, normalize_embeddings=True)
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )
        
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for doc, meta, distance in zip(
                results['documents'][0],
                results['metadatas'][0], 
                results['distances'][0]
            ):
                formatted_results.append({
                    'texto': doc,
                    'archivo': meta.get('archivo', 'Unknown'),
                    'chunk': meta.get('chunk', 'Unknown'),
                    'similarity_score': round(1 - distance, 4),
                    'final_score': round(1 - distance, 4),
                    'metadata': meta
                })
        
        return formatted_results
    
    def get_system_stats(self) -> Dict[str, Any]:
        self._initialize_models()
        return {
            'collection_count': self.collection.count() if self.collection else 0,
            'type': 'simple'
        }

# Funciones compatibles
def get_optimized_rag():
    return SimpleRAGSystem()

def perform_optimized_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    rag_system = get_optimized_rag()
    return rag_system.advanced_search(query, top_k)
'''
    
    try:
        current_dir = Path(__file__).parent
        fallback_path = current_dir / 'simple_rag_fallback.py'
        
        with open(fallback_path, 'w', encoding='utf-8') as f:
            f.write(simple_rag)
        
        print(f"✅ Sistema RAG simple creado en: {fallback_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creando fallback: {e}")
        return False

def main():
    """Diagnóstico completo"""
    print("🔬 DIAGNÓSTICO COMPLETO DEL SISTEMA RAG OPTIMIZADO")
    print("=" * 60)
    
    # Tests
    test_basic_imports()
    test_data_science_imports()
    test_file_paths()
    test_chromadb_connection()
    test_sentence_transformers()
    
    # Test principal
    rag_success = test_optimized_rag_import()
    
    if not rag_success:
        print("\n⚠️ SISTEMA OPTIMIZADO FALLÓ - CREANDO FALLBACK")
        create_simple_fallback()
    
    print("\n📋 RESUMEN DE DIAGNÓSTICO")
    print("=" * 30)
    
    if rag_success:
        print("✅ Sistema RAG optimizado: FUNCIONAL")
    else:
        print("❌ Sistema RAG optimizado: FALLÓ")
        print("✅ Sistema RAG simple: DISPONIBLE COMO FALLBACK")
    
    print("\n💡 INSTRUCCIONES PARA TU COMPAÑERO:")
    print("1. Ejecutar: pip install sentence-transformers chromadb rank-bm25")
    print("2. Verificar que existe: chroma_db_simple/")
    print("3. Ejecutar: python diagnostico_rag.py")
    print("4. Si falla, usar: from utils.simple_rag_fallback import get_optimized_rag")

if __name__ == "__main__":
    main()