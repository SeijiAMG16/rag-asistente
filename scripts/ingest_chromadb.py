"""
Script mejorado para ingestar documentos a ChromaDB con integración a Django
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict
import re

# Configuración de paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuración básica
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT_DIR = os.path.join(PROJECT_ROOT, "data", "texts")
CHROMA_DIR = os.path.join(PROJECT_ROOT, "chroma_db")
COLLECTION_NAME = "rag_documents"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Imports para embeddings y ChromaDB
from sentence_transformers import SentenceTransformer
import chromadb
from tqdm import tqdm

# Configuración de logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class DocumentIngestor:
    """Clase para ingestar documentos a ChromaDB"""
    
    def __init__(self):
        """Inicializar el ingestor"""
        self.model = None
        self.client = None
        self.collection = None
        self.setup_embeddings()
        self.setup_chromadb()
    
    def setup_embeddings(self):
        """Configurar modelo de embeddings"""
        try:
            logger.info(f"Cargando modelo de embeddings: {EMBEDDING_MODEL}")
            self.model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info("Modelo de embeddings cargado exitosamente")
        except Exception as e:
            logger.error(f"Error cargando modelo de embeddings: {e}")
            raise
    
    def setup_chromadb(self):
        """Configurar ChromaDB"""
        try:
            logger.info(f"Configurando ChromaDB en: {CHROMA_DIR}")
            self.client = chromadb.PersistentClient(path=CHROMA_DIR)
            
            # Obtener o crear colección
            try:
                self.collection = self.client.get_collection(COLLECTION_NAME)
                logger.info(f"Colección existente encontrada: {COLLECTION_NAME}")
            except:
                self.collection = self.client.create_collection(COLLECTION_NAME)
                logger.info(f"Nueva colección creada: {COLLECTION_NAME}")
            
        except Exception as e:
            logger.error(f"Error configurando ChromaDB: {e}")
            raise
    
    def clean_text(self, text: str) -> str:
        """Limpiar y normalizar texto"""
        # Eliminar caracteres especiales excesivos
        text = re.sub(r'\s+', ' ', text)  # Espacios múltiples
        text = re.sub(r'\n+', '\n', text)  # Saltos de línea múltiples
        text = text.strip()
        return text
    
    def create_chunks(self, text: str, filename: str) -> List[Dict]:
        """Crear chunks de texto con metadata"""
        chunks = []
        
        # Limpiar texto
        text = self.clean_text(text)
        
        if len(text) < CHUNK_SIZE:
            # Si el texto es pequeño, crear un solo chunk
            chunks.append({
                'text': text,
                'filename': filename,
                'chunk_index': 0,
                'chunk_id': f"{filename}_chunk_0"
            })
        else:
            # Dividir en chunks con solapamiento
            start = 0
            chunk_index = 0
            
            while start < len(text):
                end = min(start + CHUNK_SIZE, len(text))
                
                # Intentar cortar en un punto natural (punto, salto de línea)
                if end < len(text):
                    for i in range(end, max(start + CHUNK_SIZE // 2, end - 100), -1):
                        if text[i] in '.!?\n':
                            end = i + 1
                            break
                
                chunk_text = text[start:end].strip()
                
                if chunk_text:  # Solo agregar chunks no vacíos
                    chunks.append({
                        'text': chunk_text,
                        'filename': filename,
                        'chunk_index': chunk_index,
                        'chunk_id': f"{filename}_chunk_{chunk_index}"
                    })
                    chunk_index += 1
                
                start = end - CHUNK_OVERLAP
                if start >= len(text):
                    break
        
        return chunks
    
    def ingest_document(self, filepath: str) -> bool:
        """Ingestar un documento individual"""
        try:
            filename = os.path.basename(filepath)
            logger.info(f"Procesando: {filename}")
            
            # Leer archivo
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            
            if not text.strip():
                logger.warning(f"Archivo vacío: {filename}")
                return False
            
            # Crear chunks
            chunks = self.create_chunks(text, filename)
            logger.info(f"Creados {len(chunks)} chunks para {filename}")
            
            # Verificar si ya existe en ChromaDB
            existing_ids = []
            try:
                # Intentar obtener documentos existentes de este archivo
                result = self.collection.get(
                    where={"filename": filename}
                )
                existing_ids = result['ids']
                
                if existing_ids:
                    logger.info(f"Eliminando {len(existing_ids)} chunks existentes de {filename}")
                    self.collection.delete(ids=existing_ids)
            
            except Exception as e:
                logger.debug(f"No hay chunks existentes para {filename}: {e}")
            
            # Procesar chunks en lotes
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                
                # Generar embeddings para el lote
                texts = [chunk['text'] for chunk in batch_chunks]
                embeddings = self.model.encode(texts, show_progress_bar=False)
                
                # Preparar datos para ChromaDB
                ids = [chunk['chunk_id'] for chunk in batch_chunks]
                metadatas = [
                    {
                        'filename': chunk['filename'],
                        'chunk_index': chunk['chunk_index'],
                        'file_path': filepath,
                        'ingested_at': datetime.now().isoformat()
                    }
                    for chunk in batch_chunks
                ]
                documents = texts
                
                # Insertar en ChromaDB
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings.tolist(),
                    metadatas=metadatas,
                    documents=documents
                )
            
            logger.info(f"✅ {filename} ingresado exitosamente ({len(chunks)} chunks)")
            return True
            
        except Exception as e:
            logger.error(f"Error ingresando {filepath}: {e}")
            return False
    
    def ingest_all_documents(self) -> Dict[str, int]:
        """Ingestar todos los documentos de TEXT_DIR"""
        stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'total_chunks': 0
        }
        
        if not os.path.exists(TEXT_DIR):
            logger.error(f"Directorio de textos no existe: {TEXT_DIR}")
            return stats
        
        # Obtener lista de archivos .txt
        txt_files = [f for f in os.listdir(TEXT_DIR) if f.endswith('.txt')]
        
        if not txt_files:
            logger.warning(f"No se encontraron archivos .txt en {TEXT_DIR}")
            return stats
        
        logger.info(f"Encontrados {len(txt_files)} archivos para procesar")
        
        # Procesar cada archivo con barra de progreso
        for filename in tqdm(txt_files, desc="Ingresando documentos"):
            filepath = os.path.join(TEXT_DIR, filename)
            stats['processed'] += 1
            
            if self.ingest_document(filepath):
                stats['successful'] += 1
            else:
                stats['failed'] += 1
        
        # Obtener estadísticas finales de ChromaDB
        try:
            collection_count = self.collection.count()
            stats['total_chunks'] = collection_count
            logger.info(f"Total de chunks en ChromaDB: {collection_count}")
        except Exception as e:
            logger.warning(f"No se pudo obtener conteo de ChromaDB: {e}")
        
        return stats
    
    def get_collection_stats(self) -> Dict:
        """Obtener estadísticas de la colección"""
        try:
            count = self.collection.count()
            
            # Obtener algunos metadatos para estadísticas
            sample = self.collection.get(limit=1000)
            
            filenames = set()
            if sample['metadatas']:
                filenames = set(meta.get('filename', 'unknown') for meta in sample['metadatas'])
            
            return {
                'total_chunks': count,
                'unique_files': len(filenames),
                'collection_name': COLLECTION_NAME,
                'embedding_model': EMBEDDING_MODEL
            }
        
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}

def main():
    """Función principal"""
    print("🚀 Iniciando ingesta de documentos a ChromaDB")
    print("=" * 50)
    
    try:
        # Crear ingestor
        ingestor = DocumentIngestor()
        
        # Verificar que existan archivos
        if not os.path.exists(TEXT_DIR):
            print(f"❌ Error: Directorio de textos no existe: {TEXT_DIR}")
            print("💡 Ejecuta primero el ETL para extraer textos de Google Drive")
            return 1
        
        # Ejecutar ingesta
        start_time = datetime.now()
        stats = ingestor.ingest_all_documents()
        end_time = datetime.now()
        
        # Mostrar resultados
        print("\n📊 Resultados de la ingesta:")
        print(f"   ✅ Archivos procesados: {stats['successful']}/{stats['processed']}")
        print(f"   ❌ Archivos fallidos: {stats['failed']}")
        print(f"   📝 Total chunks creados: {stats['total_chunks']}")
        print(f"   ⏱️ Tiempo total: {end_time - start_time}")
        
        # Estadísticas de la colección
        collection_stats = ingestor.get_collection_stats()
        if collection_stats:
            print("\n📈 Estadísticas de ChromaDB:")
            print(f"   🗂️ Colección: {collection_stats['collection_name']}")
            print(f"   📄 Total chunks: {collection_stats['total_chunks']}")
            print(f"   📁 Archivos únicos: {collection_stats['unique_files']}")
            print(f"   🤖 Modelo: {collection_stats['embedding_model']}")
        
        print(f"\n🎉 Ingesta completada!")
        print(f"📁 Base de datos vectorial: {CHROMA_DIR}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error en ingesta: {e}")
        return 1

if __name__ == "__main__":
    exit(main())