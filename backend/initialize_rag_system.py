#!/usr/bin/env python3
"""
🚀 SCRIPT DE INICIALIZACIÓN COMPLETA PARA NUEVA PC
==================================================

Este script inicializa completamente el sistema RAG en una nueva PC:
1. Verifica dependencias
2. Crea base de datos vectorial ChromaDB
3. Procesa y vectoriza todos los documentos
4. Configura el sistema optimizado

EJECUTAR CUANDO:
- Instalas el proyecto en una nueva PC
- La carpeta chroma_db_simple está vacía
- Los embeddings no están funcionando
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict

def install_dependencies():
    """Instalar dependencias necesarias"""
    print("📦 INSTALANDO DEPENDENCIAS...")
    print("=" * 40)
    
    dependencies = [
        'chromadb>=0.5.0',
        'sentence-transformers>=2.2.0',
        'rank-bm25>=0.2.2',
        'numpy>=1.24.0',
        'tqdm',
        'python-dotenv'
    ]
    
    for dep in dependencies:
        print(f"Instalando {dep}...")
        result = os.system(f"{sys.executable} -m pip install {dep}")
        if result == 0:
            print(f"✅ {dep}")
        else:
            print(f"⚠️ {dep} (puede que ya esté instalado)")

def check_documents():
    """Verificar que existen documentos para procesar"""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "texts"
    
    if not data_dir.exists():
        print("❌ ERROR: No existe la carpeta data/texts/")
        print("   Asegúrate de tener los documentos en la carpeta correcta")
        return False
    
    txt_files = list(data_dir.glob("*.txt"))
    
    if not txt_files:
        print("❌ ERROR: No hay archivos .txt en data/texts/")
        print("   Copia tus documentos a esta carpeta primero")
        return False
    
    print(f"✅ Encontrados {len(txt_files)} archivos .txt para procesar")
    return True

def create_optimized_embeddings():
    """Crear embeddings optimizados para el sistema RAG"""
    print("🔧 CREANDO EMBEDDINGS OPTIMIZADOS...")
    print("=" * 50)
    
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        from tqdm import tqdm
        import numpy as np
        import re
        
        # Rutas del proyecto
        project_root = Path(__file__).parent.parent
        data_dir = project_root / "data" / "texts"
        chroma_dir = project_root / "chroma_db_simple"
        
        # Crear directorio si no existe
        chroma_dir.mkdir(exist_ok=True)
        
        print(f"📁 Carpeta de datos: {data_dir}")
        print(f"📁 Base de datos: {chroma_dir}")
        
        # Inicializar modelo de embeddings optimizado
        print("🤖 Cargando modelo de embeddings all-mpnet-base-v2 (768d)...")
        model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        
        # Inicializar ChromaDB
        print("🗄️ Inicializando ChromaDB...")
        client = chromadb.PersistentClient(path=str(chroma_dir))
        
        # Eliminar colección existente si existe
        try:
            client.delete_collection("simple_rag_docs")
            print("🗑️ Colección anterior eliminada")
        except:
            pass
        
        # Crear nueva colección
        collection = client.create_collection(
            name="simple_rag_docs",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Procesar documentos
        txt_files = list(data_dir.glob("*.txt"))
        print(f"📚 Procesando {len(txt_files)} documentos...")
        
        documents = []
        metadatas = []
        ids = []
        chunk_id = 0
        
        for file_path in tqdm(txt_files, desc="Leyendo archivos"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if not content.strip():
                    continue
                
                # Chunking inteligente que preserva referencias académicas
                chunks = smart_chunk_text(content, file_path.name)
                
                for i, chunk in enumerate(chunks):
                    if len(chunk.strip()) < 50:  # Saltar chunks muy pequeños
                        continue
                    
                    documents.append(chunk)
                    metadatas.append({
                        "source": file_path.name,
                        "chunk_id": i,
                        "file_size": len(content),
                        "chunk_size": len(chunk)
                    })
                    ids.append(f"doc_{chunk_id}")
                    chunk_id += 1
                    
            except Exception as e:
                print(f"⚠️ Error procesando {file_path.name}: {e}")
                continue
        
        print(f"📊 Total de chunks creados: {len(documents)}")
        
        # Generar embeddings en lotes
        print("🧮 Generando embeddings...")
        batch_size = 32
        
        for i in tqdm(range(0, len(documents), batch_size), desc="Embeddings"):
            batch_docs = documents[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            # Generar embeddings para el lote
            embeddings = model.encode(batch_docs, convert_to_tensor=False)
            
            # Agregar a ChromaDB
            collection.add(
                embeddings=embeddings.tolist(),
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
        
        final_count = collection.count()
        print(f"✅ Base de datos creada exitosamente!")
        print(f"📊 Total de documentos en ChromaDB: {final_count}")
        
        # Verificar funcionamiento
        print("🧪 Probando búsqueda...")
        test_query = "Arias 2020"
        test_embedding = model.encode([test_query])
        results = collection.query(
            query_embeddings=test_embedding.tolist(),
            n_results=3
        )
        
        if results['documents'] and results['documents'][0]:
            print(f"✅ Prueba exitosa: {len(results['documents'][0])} resultados para '{test_query}'")
            return True
        else:
            print("⚠️ Advertencia: No se encontraron resultados en la prueba")
            return False
            
    except Exception as e:
        print(f"❌ Error creando embeddings: {e}")
        return False

def smart_chunk_text(text: str, filename: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """
    Chunking inteligente que preserva referencias académicas y contexto
    """
    # Patrones para preservar referencias
    reference_patterns = [
        r'\b\w+\s*\(\d{4}\)',  # Autor (año)
        r'\b\w+\s*\(\d{4}[a-z]?\)',  # Autor (año + letra)
        r'\b\w+\s*y\s*\w+\s*\(\d{4}\)',  # Autor y Autor (año)
        r'\b\w+\s*et\s*al\.\s*\(\d{4}\)',  # Autor et al. (año)
    ]
    
    # Dividir en párrafos primero
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        
        # Si agregar este párrafo excede el tamaño, guardar chunk actual
        if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
            # Verificar si hay referencias que preservar
            has_reference = any(re.search(pattern, current_chunk, re.IGNORECASE) 
                              for pattern in reference_patterns)
            
            if has_reference:
                # Buscar un buen punto de corte que preserve referencias
                sentences = current_chunk.split('. ')
                best_chunk = ""
                
                for sentence in sentences:
                    if len(best_chunk + sentence) <= chunk_size:
                        best_chunk += sentence + ". "
                    else:
                        break
                
                if best_chunk:
                    chunks.append(best_chunk.strip())
                    # Crear overlap con contexto de referencia
                    overlap_text = '. '.join(sentences[-2:]) if len(sentences) > 2 else ""
                    current_chunk = overlap_text + " " + paragraph if overlap_text else paragraph
                else:
                    chunks.append(current_chunk)
                    current_chunk = paragraph
            else:
                chunks.append(current_chunk)
                current_chunk = paragraph
        else:
            current_chunk += " " + paragraph if current_chunk else paragraph
    
    # Agregar último chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    # Limpiar chunks vacíos
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def setup_environment():
    """Configurar variables de entorno necesarias"""
    print("⚙️ CONFIGURANDO ENTORNO...")
    print("=" * 30)
    
    backend_dir = Path(__file__).parent
    env_file = backend_dir / ".env"
    
    # Verificar si .env existe y tiene la configuración optimizada
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "USE_OPTIMIZED_RAG=true" in content:
            print("✅ Configuración optimizada ya está activa")
            return
    
    # Agregar o actualizar configuración
    config_lines = [
        "# === CONFIGURACIÓN RAG OPTIMIZADO ===",
        "USE_OPTIMIZED_RAG=true",
        "USE_ENHANCED_RAG=true",
        "",
        "# === CONFIGURACIÓN DEEPSEEK ===", 
        "# OPENROUTER_API_KEY=tu_clave_aqui",
        ""
    ]
    
    try:
        with open(env_file, 'a', encoding='utf-8') as f:
            f.write("\n" + "\n".join(config_lines))
        print("✅ Configuración optimizada agregada a .env")
    except Exception as e:
        print(f"⚠️ Error actualizando .env: {e}")

def main():
    """Función principal de inicialización"""
    print("🚀 INICIALIZACIÓN COMPLETA DEL SISTEMA RAG")
    print("=" * 60)
    print("Este proceso puede tomar varios minutos...")
    print()
    
    start_time = time.time()
    
    # Paso 1: Instalar dependencias
    install_dependencies()
    print()
    
    # Paso 2: Verificar documentos
    if not check_documents():
        return False
    print()
    
    # Paso 3: Configurar entorno
    setup_environment()
    print()
    
    # Paso 4: Crear embeddings optimizados
    success = create_optimized_embeddings()
    print()
    
    elapsed = time.time() - start_time
    print("=" * 60)
    if success:
        print("🎉 INICIALIZACIÓN COMPLETADA EXITOSAMENTE!")
        print(f"⏱️ Tiempo total: {elapsed:.1f} segundos")
        print()
        print("✅ El sistema RAG está listo para usar")
        print("✅ Base de datos vectorial creada")
        print("✅ Embeddings optimizados generados")
        print()
        print("🚀 Puedes ahora ejecutar:")
        print("   python manage.py runserver")
        print("   python start_rag.py")
    else:
        print("❌ INICIALIZACIÓN FALLÓ")
        print("Revisa los errores anteriores")
    
    return success

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Proceso cancelado por el usuario")
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        import traceback
        traceback.print_exc()