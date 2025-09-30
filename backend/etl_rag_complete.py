#!/usr/bin/env python3
"""
🔄 PROCESO ETL COMPLETO PARA RAG ASISTENTE
==========================================

Este script ejecuta el proceso completo de ETL:
- EXTRACT: Lee documentos PDF y TXT
- TRANSFORM: Procesa, limpia y fragmenta el texto
- LOAD: Genera embeddings y carga en ChromaDB

FUNCIONALIDADES:
- Procesa PDFs automáticamente
- Extrae texto limpio
- Chunking inteligente que preserva referencias académicas
- Embeddings optimizados (768d)
- Carga en base de datos vectorial

USO:
python etl_rag_complete.py [--force] [--chunk-size 800] [--model mpnet]
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import re
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGETLProcessor:
    """Procesador ETL completo para el sistema RAG"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.pdfs_dir = self.data_dir / "pdfs"
        self.texts_dir = self.data_dir / "texts"
        self.chroma_dir = self.project_root / "chroma_db_simple"
        
        # Configuración por defecto
        self.chunk_size = 800
        self.chunk_overlap = 100
        self.embedding_model = "sentence-transformers/all-mpnet-base-v2"
        
        # Estadísticas del proceso
        self.stats = {
            'pdfs_processed': 0,
            'texts_extracted': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'total_documents': 0
        }
    
    def setup_directories(self):
        """Crear directorios necesarios"""
        logger.info("📁 Configurando directorios...")
        
        directories = [self.data_dir, self.pdfs_dir, self.texts_dir, self.chroma_dir]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Directorio: {directory}")
    
    def extract_from_pdfs(self, force: bool = False) -> List[Tuple[str, str]]:
        """
        EXTRACT: Extraer texto de archivos PDF
        Retorna lista de tuplas (filename, text_content)
        """
        logger.info("📚 FASE EXTRACT: Procesando PDFs...")
        
        try:
            import PyPDF2
            import pdfplumber
        except ImportError:
            logger.warning("⚠️ PyPDF2 o pdfplumber no disponible, instalando...")
            os.system(f"{sys.executable} -m pip install PyPDF2 pdfplumber")
            import PyPDF2
            import pdfplumber
        
        pdf_files = list(self.pdfs_dir.glob("*.pdf"))
        extracted_texts = []
        
        if not pdf_files:
            logger.warning(f"⚠️ No se encontraron PDFs en {self.pdfs_dir}")
            return extracted_texts
        
        logger.info(f"📄 Encontrados {len(pdf_files)} archivos PDF")
        
        for pdf_path in pdf_files:
            try:
                txt_filename = pdf_path.stem + ".txt"
                txt_path = self.texts_dir / txt_filename
                
                # Verificar si ya existe el texto extraído
                if txt_path.exists() and not force:
                    logger.info(f"⏭️ Saltando {pdf_path.name} (texto ya existe)")
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    extracted_texts.append((txt_filename, content))
                    continue
                
                logger.info(f"🔍 Extrayendo texto de {pdf_path.name}...")
                
                # Intentar con pdfplumber primero (mejor calidad)
                text_content = ""
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text_content += page_text + "\n"
                    
                    if len(text_content.strip()) < 100:
                        raise Exception("Texto insuficiente con pdfplumber")
                        
                except Exception as e:
                    logger.warning(f"⚠️ pdfplumber falló para {pdf_path.name}, usando PyPDF2...")
                    
                    # Fallback a PyPDF2
                    text_content = ""
                    with open(pdf_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        for page in pdf_reader.pages:
                            text_content += page.extract_text() + "\n"
                
                # Verificar que se extrajo contenido válido
                if len(text_content.strip()) < 50:
                    logger.error(f"❌ No se pudo extraer texto válido de {pdf_path.name}")
                    continue
                
                # Guardar texto extraído
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                
                extracted_texts.append((txt_filename, text_content))
                self.stats['pdfs_processed'] += 1
                self.stats['texts_extracted'] += 1
                
                logger.info(f"✅ Extraído: {len(text_content)} caracteres de {pdf_path.name}")
                
            except Exception as e:
                logger.error(f"❌ Error procesando {pdf_path.name}: {e}")
                continue
        
        logger.info(f"📊 EXTRACT completado: {len(extracted_texts)} textos extraídos")
        return extracted_texts
    
    def load_existing_texts(self) -> List[Tuple[str, str]]:
        """Cargar textos ya existentes en data/texts/"""
        logger.info("📝 Cargando textos existentes...")
        
        txt_files = list(self.texts_dir.glob("*.txt"))
        existing_texts = []
        
        for txt_path in txt_files:
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if len(content.strip()) > 50:  # Verificar contenido válido
                    existing_texts.append((txt_path.name, content))
                    logger.debug(f"✅ Cargado: {txt_path.name}")
                else:
                    logger.warning(f"⚠️ Archivo muy pequeño: {txt_path.name}")
                    
            except Exception as e:
                logger.error(f"❌ Error leyendo {txt_path.name}: {e}")
                continue
        
        logger.info(f"📊 Textos existentes cargados: {len(existing_texts)}")
        return existing_texts
    
    def transform_texts(self, texts: List[Tuple[str, str]]) -> List[Dict]:
        """
        TRANSFORM: Procesar y fragmentar textos
        Retorna lista de chunks con metadatos
        """
        logger.info("🔄 FASE TRANSFORM: Procesando y fragmentando textos...")
        
        all_chunks = []
        chunk_id = 0
        
        for filename, content in texts:
            try:
                logger.info(f"🔍 Procesando {filename}...")
                
                # Limpiar y normalizar texto
                cleaned_content = self.clean_text(content)
                
                if len(cleaned_content.strip()) < 100:
                    logger.warning(f"⚠️ Contenido insuficiente en {filename}")
                    continue
                
                # Fragmentar con preservación de contexto académico
                chunks = self.smart_chunk_text(cleaned_content, filename)
                
                # Crear metadatos para cada chunk
                for i, chunk_text in enumerate(chunks):
                    chunk_data = {
                        'id': f"doc_{chunk_id}",
                        'content': chunk_text,
                        'metadata': {
                            'source': filename,
                            'chunk_id': i,
                            'file_size': len(content),
                            'chunk_size': len(chunk_text),
                            'has_references': self.has_academic_references(chunk_text)
                        }
                    }
                    all_chunks.append(chunk_data)
                    chunk_id += 1
                
                self.stats['chunks_created'] += len(chunks)
                logger.info(f"✅ {filename}: {len(chunks)} chunks creados")
                
            except Exception as e:
                logger.error(f"❌ Error transformando {filename}: {e}")
                continue
        
        logger.info(f"📊 TRANSFORM completado: {len(all_chunks)} chunks totales")
        return all_chunks
    
    def clean_text(self, text: str) -> str:
        """Limpiar y normalizar texto"""
        # Normalizar espacios en blanco
        text = re.sub(r'\s+', ' ', text)
        
        # Normalizar saltos de línea
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Limpiar caracteres especiales problemáticos
        text = text.replace('\x00', '')
        text = text.replace('\ufffd', '')
        
        # Preservar referencias académicas
        text = re.sub(r'([A-Z][a-z]+)\s*\(\s*(\d{4})\s*\)', r'\1 (\2)', text)
        
        return text.strip()
    
    def smart_chunk_text(self, text: str, filename: str) -> List[str]:
        """Fragmentación inteligente que preserva contexto académico"""
        
        # Patrones de referencias académicas a preservar
        reference_patterns = [
            r'\b[A-Z][a-z]+\s*\(\d{4}[a-z]?\)',  # Autor (año)
            r'\b[A-Z][a-z]+\s*y\s*[A-Z][a-z]+\s*\(\d{4}\)',  # Autor y Autor (año)
            r'\b[A-Z][a-z]+\s*et\s*al\.\s*\(\d{4}\)',  # Autor et al. (año)
        ]
        
        # Dividir en párrafos
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Si agregar este párrafo excede el tamaño máximo
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                
                # Verificar si hay referencias académicas en el chunk actual
                has_references = any(re.search(pattern, current_chunk, re.IGNORECASE) 
                                   for pattern in reference_patterns)
                
                if has_references:
                    # Buscar punto de corte que preserve referencias
                    sentences = current_chunk.split('. ')
                    best_chunk = ""
                    
                    for sentence in sentences:
                        if len(best_chunk + sentence + '. ') <= self.chunk_size:
                            best_chunk += sentence + '. '
                        else:
                            break
                    
                    if best_chunk:
                        chunks.append(best_chunk.strip())
                        
                        # Crear overlap con contexto de referencias
                        overlap_sentences = sentences[-2:] if len(sentences) > 2 else sentences[-1:]
                        overlap_text = '. '.join(overlap_sentences)
                        current_chunk = overlap_text + '. ' + paragraph if overlap_text else paragraph
                    else:
                        chunks.append(current_chunk)
                        current_chunk = paragraph
                else:
                    # Sin referencias, corte normal
                    chunks.append(current_chunk)
                    current_chunk = paragraph
            else:
                # Agregar párrafo al chunk actual
                current_chunk = current_chunk + '\n\n' + paragraph if current_chunk else paragraph
        
        # Agregar último chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Filtrar chunks muy pequeños
        return [chunk for chunk in chunks if len(chunk.strip()) >= 100]
    
    def has_academic_references(self, text: str) -> bool:
        """Detectar si el texto contiene referencias académicas"""
        patterns = [
            r'\b[A-Z][a-z]+\s*\(\d{4}\)',
            r'\b[A-Z][a-z]+\s*et\s*al\.\s*\(\d{4}\)',
            r'\bibitem|\\cite|doi:|DOI:',
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    def load_to_chromadb(self, chunks: List[Dict], force: bool = False) -> bool:
        """
        LOAD: Generar embeddings y cargar en ChromaDB
        """
        logger.info("💾 FASE LOAD: Generando embeddings y cargando en ChromaDB...")
        
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
            from tqdm import tqdm
        except ImportError:
            logger.warning("⚠️ Dependencias faltantes, instalando...")
            os.system(f"{sys.executable} -m pip install chromadb sentence-transformers tqdm")
            import chromadb
            from sentence_transformers import SentenceTransformer
            from tqdm import tqdm
        
        try:
            # Inicializar modelo de embeddings
            logger.info(f"🤖 Cargando modelo: {self.embedding_model}")
            model = SentenceTransformer(self.embedding_model)
            
            # Inicializar ChromaDB
            logger.info(f"🗄️ Conectando a ChromaDB: {self.chroma_dir}")
            client = chromadb.PersistentClient(path=str(self.chroma_dir))
            
            # Manejar colección existente
            collection_name = "simple_rag_docs"
            
            if force:
                try:
                    client.delete_collection(collection_name)
                    logger.info("🗑️ Colección anterior eliminada")
                except:
                    pass
            
            try:
                collection = client.get_collection(collection_name)
                if not force:
                    current_count = collection.count()
                    logger.info(f"📊 Colección existente: {current_count} documentos")
                    if current_count > 0 and not force:
                        logger.info("⏭️ Agregando a colección existente...")
            except:
                collection = client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("✅ Nueva colección creada")
            
            # Procesar en lotes para eficiencia
            batch_size = 32
            total_batches = (len(chunks) + batch_size - 1) // batch_size
            
            logger.info(f"🔄 Procesando {len(chunks)} chunks en {total_batches} lotes...")
            
            for i in tqdm(range(0, len(chunks), batch_size), desc="Generando embeddings"):
                batch_chunks = chunks[i:i+batch_size]
                
                # Extraer datos del lote
                batch_ids = [chunk['id'] for chunk in batch_chunks]
                batch_documents = [chunk['content'] for chunk in batch_chunks]
                batch_metadatas = [chunk['metadata'] for chunk in batch_chunks]
                
                # Generar embeddings
                embeddings = model.encode(batch_documents, convert_to_tensor=False)
                
                # Agregar a ChromaDB
                collection.add(
                    ids=batch_ids,
                    embeddings=embeddings.tolist(),
                    documents=batch_documents,
                    metadatas=batch_metadatas
                )
                
                self.stats['embeddings_generated'] += len(batch_chunks)
            
            # Verificar resultado final
            final_count = collection.count()
            self.stats['total_documents'] = final_count
            
            logger.info(f"✅ LOAD completado: {final_count} documentos en ChromaDB")
            
            # Prueba de funcionalidad
            self.test_search_functionality(model, collection)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en LOAD: {e}")
            return False
    
    def test_search_functionality(self, model, collection):
        """Probar funcionalidad de búsqueda"""
        logger.info("🧪 Probando funcionalidad de búsqueda...")
        
        test_queries = ["Arias 2020", "racismo", "política peruana"]
        
        for query in test_queries:
            try:
                # Generar embedding de prueba
                query_embedding = model.encode([query])
                
                # Buscar
                results = collection.query(
                    query_embeddings=query_embedding.tolist(),
                    n_results=3
                )
                
                result_count = len(results['documents'][0]) if results['documents'] else 0
                logger.info(f"✅ '{query}': {result_count} resultados")
                
            except Exception as e:
                logger.error(f"❌ Error probando '{query}': {e}")
    
    def print_statistics(self):
        """Mostrar estadísticas del proceso ETL"""
        logger.info("📊 ESTADÍSTICAS DEL PROCESO ETL")
        logger.info("=" * 40)
        
        for key, value in self.stats.items():
            label = key.replace('_', ' ').title()
            logger.info(f"{label}: {value}")
        
        logger.info("=" * 40)
    
    def run_complete_etl(self, force: bool = False, extract_pdfs: bool = True):
        """Ejecutar proceso ETL completo"""
        start_time = time.time()
        
        logger.info("🚀 INICIANDO PROCESO ETL COMPLETO")
        logger.info("=" * 50)
        
        try:
            # Configurar directorios
            self.setup_directories()
            
            # EXTRACT: Procesar PDFs si se solicita
            extracted_texts = []
            if extract_pdfs:
                extracted_texts = self.extract_from_pdfs(force=force)
            
            # Cargar textos existentes
            existing_texts = self.load_existing_texts()
            
            # Combinar todos los textos
            all_texts = extracted_texts + existing_texts
            
            if not all_texts:
                logger.error("❌ No se encontraron textos para procesar")
                return False
            
            logger.info(f"📚 Total de textos a procesar: {len(all_texts)}")
            
            # TRANSFORM: Procesar y fragmentar
            chunks = self.transform_texts(all_texts)
            
            if not chunks:
                logger.error("❌ No se generaron chunks válidos")
                return False
            
            # LOAD: Cargar en ChromaDB
            success = self.load_to_chromadb(chunks, force=force)
            
            if success:
                elapsed = time.time() - start_time
                logger.info("🎉 PROCESO ETL COMPLETADO EXITOSAMENTE!")
                logger.info(f"⏱️ Tiempo total: {elapsed:.1f} segundos")
                self.print_statistics()
                return True
            else:
                logger.error("❌ Error en proceso ETL")
                return False
                
        except Exception as e:
            logger.error(f"💥 Error crítico en ETL: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Proceso ETL completo para RAG Asistente')
    
    parser.add_argument('--force', action='store_true', 
                       help='Forzar recreación completa de la base de datos')
    parser.add_argument('--no-pdfs', action='store_true',
                       help='No procesar PDFs, solo usar textos existentes')
    parser.add_argument('--chunk-size', type=int, default=800,
                       help='Tamaño de chunks en caracteres (default: 800)')
    parser.add_argument('--model', default='all-mpnet-base-v2',
                       choices=['all-mpnet-base-v2', 'all-MiniLM-L6-v2'],
                       help='Modelo de embeddings a usar')
    
    args = parser.parse_args()
    
    # Crear procesador ETL
    etl = RAGETLProcessor()
    
    # Configurar parámetros
    etl.chunk_size = args.chunk_size
    
    if args.model == 'all-MiniLM-L6-v2':
        etl.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Ejecutar ETL
    success = etl.run_complete_etl(
        force=args.force,
        extract_pdfs=not args.no_pdfs
    )
    
    if success:
        print("\n🎉 ETL completado. El sistema RAG está listo para usar!")
        print("🚀 Ejecuta: python start_rag.py")
    else:
        print("\n❌ ETL falló. Revisa los errores anteriores.")
        sys.exit(1)

if __name__ == "__main__":
    main()