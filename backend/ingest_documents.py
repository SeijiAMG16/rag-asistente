#!/usr/bin/env python3
"""
Script directo para ingerir documentos en ChromaDB
Carga todos los archivos .txt de data/texts/ en la colección simple_rag_docs
"""

import os
import sys
from sentence_transformers import SentenceTransformer
import chromadb

def ingest_documents():
    """
    Ingiere documentos de texto en ChromaDB
    """
    try:
        # Configurar rutas
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        text_dir = os.path.join(project_root, "data", "texts")
        chroma_dir = os.path.join(project_root, "chroma_db_simple")
        
        print(f"📁 Directorio de textos: {text_dir}")
        print(f"📁 Directorio ChromaDB: {chroma_dir}")
        
        # Verificar que existe el directorio de textos
        if not os.path.exists(text_dir):
            print(f"❌ Error: Directorio {text_dir} no existe")
            return False
            
        # Listar archivos .txt
        txt_files = [f for f in os.listdir(text_dir) if f.lower().endswith('.txt')]
        print(f"📄 Encontrados {len(txt_files)} archivos .txt")
        
        if not txt_files:
            print("❌ No se encontraron archivos .txt para procesar")
            return False

        # Configuración de fragmentación
        CHUNK_SIZE = 500
        CHUNK_OVERLAP = 50

        print("🚀 Inicializando ChromaDB y modelo de embeddings...")
        
        # Inicializar cliente ChromaDB
        client = chromadb.PersistentClient(path=chroma_dir)
        
        # Crear/obtener colección
        try:
            collection = client.get_collection("simple_rag_docs")
            print("📚 Colección 'simple_rag_docs' existente encontrada")
            # Limpiar colección existente
            count = collection.count()
            if count > 0:
                print(f"🧹 Limpiando {count} documentos existentes...")
                collection.delete(where={})
        except:
            collection = client.create_collection("simple_rag_docs")
            print("📚 Colección 'simple_rag_docs' creada")

        # Inicializar modelo de embeddings
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        print("🤖 Modelo de embeddings cargado")

        files_processed = []
        total_chunks = 0
        
        # Procesar cada archivo .txt
        for i, filename in enumerate(txt_files, 1):
            print(f"\n📖 Procesando [{i}/{len(txt_files)}]: {filename}")
            
            file_path = os.path.join(text_dir, filename)
            
            try:
                # Leer archivo
                with open(file_path, "r", encoding="utf-8") as f:
                    full_text = f.read()
                
                if not full_text.strip():
                    print(f"⚠️  Archivo vacío: {filename}")
                    continue

                # Fragmentar texto en chunks
                chunks = []
                start = 0
                while start < len(full_text):
                    end = min(start + CHUNK_SIZE, len(full_text))
                    chunk = full_text[start:end]
                    if chunk.strip():  # Solo agregar chunks no vacíos
                        chunks.append(chunk)
                    start += CHUNK_SIZE - CHUNK_OVERLAP

                if not chunks:
                    print(f"⚠️  No se generaron chunks válidos para: {filename}")
                    continue

                print(f"   📄 Generando {len(chunks)} chunks...")

                # Procesar chunks en lotes pequeños para evitar problemas de memoria
                batch_size = 10
                for batch_start in range(0, len(chunks), batch_size):
                    batch_end = min(batch_start + batch_size, len(chunks))
                    batch_chunks = chunks[batch_start:batch_end]
                    
                    # Generar IDs, embeddings y metadatos para el lote
                    ids = []
                    embeddings = []
                    metadatas = []
                    documents = []
                    
                    for idx, chunk in enumerate(batch_chunks, batch_start):
                        chunk_id = f"{filename}_{idx}"
                        embedding = model.encode(chunk).tolist()
                        metadata = {
                            "filename": filename,
                            "chunk_index": idx,
                        }
                        
                        ids.append(chunk_id)
                        embeddings.append(embedding)
                        metadatas.append(metadata)
                        documents.append(chunk)
                    
                    # Agregar lote a ChromaDB
                    collection.add(
                        ids=ids,
                        embeddings=embeddings,
                        metadatas=metadatas,
                        documents=documents
                    )
                    
                    print(f"   ✅ Lote {batch_start//batch_size + 1} de {(len(chunks) + batch_size - 1)//batch_size} agregado")

                total_chunks += len(chunks)
                files_processed.append({
                    "file": filename,
                    "chunks": len(chunks)
                })
                
                print(f"   ✅ Procesado: {len(chunks)} chunks")
                
            except Exception as e:
                print(f"   ❌ Error procesando {filename}: {str(e)}")
                continue

        # Verificar resultado final
        final_count = collection.count()
        print(f"\n🎉 INGESTA COMPLETADA")
        print(f"📊 Archivos procesados: {len(files_processed)}")
        print(f"📊 Total de chunks: {total_chunks}")
        print(f"📊 Documentos en ChromaDB: {final_count}")
        
        # Mostrar resumen por archivo
        if files_processed:
            print(f"\n📋 RESUMEN POR ARCHIVO:")
            for item in files_processed:
                print(f"   • {item['file']}: {item['chunks']} chunks")
        
        return True

    except Exception as e:
        print(f"❌ Error durante la ingesta: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO INGESTA DE DOCUMENTOS")
    print("=" * 50)
    
    success = ingest_documents()
    
    if success:
        print("\n✅ Ingesta completada exitosamente")
        print("🎯 El sistema RAG ahora puede responder preguntas")
        sys.exit(0)
    else:
        print("\n❌ La ingesta falló")
        sys.exit(1)