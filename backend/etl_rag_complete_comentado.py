#!/usr/bin/env python3
"""
🔄 PROCESO ETL COMPLETO PARA RAG ASISTENTE - CÓDIGO DOCUMENTADO
==============================================================

Este archivo contiene el procesador ETL completo con comentarios detallados
explicando cada función y bloque de código para entender el funcionamiento
del sistema de embeddings y procesamiento de documentos.

TECNOLOGÍAS UTILIZADAS:
- PyPDF2 / pdfplumber: Extracción de texto de PDFs
- sentence-transformers: Generación de embeddings (all-mpnet-base-v2)
- ChromaDB: Base de datos vectorial para almacenamiento
- PyTorch: Framework de deep learning (backend de transformers)
- SQLite: Backend de persistencia para metadata
- HNSW: Algoritmo de búsqueda vectorial eficiente

FLUJO ETL:
1. EXTRACT: Extrae texto de PDFs usando pdfplumber
2. TRANSFORM: Procesa y fragmenta texto en chunks inteligentes
3. LOAD: Genera embeddings 768D y almacena en ChromaDB
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import re
import logging

# Configurar logging para monitorear el proceso
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGETLProcessor:
    """
    Procesador ETL completo para el sistema RAG
    
    Esta clase maneja todo el pipeline de procesamiento:
    - Extracción de texto de documentos PDF
    - Transformación y limpieza de texto
    - Fragmentación inteligente (chunking)
    - Generación de embeddings vectoriales
    - Carga en base de datos vectorial ChromaDB
    """
    
    def __init__(self, project_root: Path = None):
        """
        Inicializa el procesador ETL con configuración por defecto
        
        Args:
            project_root: Ruta raíz del proyecto (se detecta automáticamente si no se proporciona)
        """
        # === CONFIGURACIÓN DE DIRECTORIOS ===
        # Detectar automáticamente la ruta del proyecto si no se proporciona
        self.project_root = project_root or Path(__file__).parent.parent
        
        # Definir estructura de directorios del proyecto
        self.data_dir = self.project_root / "data"  # Directorio principal de datos
        self.pdfs_dir = self.data_dir / "pdfs"      # PDFs originales
        self.texts_dir = self.data_dir / "texts"    # Textos extraídos (.txt)
        self.chroma_dir = self.project_root / "chroma_db_simple"  # Base vectorial
        
        # === CONFIGURACIÓN DE EMBEDDINGS ===
        # Parámetros para el chunking (fragmentación de texto)
        self.chunk_size = 800      # Tamaño máximo de cada fragmento (tokens)
        self.chunk_overlap = 100   # Solapamiento entre fragmentos (preserva contexto)
        
        # Modelo de embeddings optimizado - all-mpnet-base-v2
        # Este modelo genera vectores de 768 dimensiones con alta calidad semántica
        self.embedding_model = "sentence-transformers/all-mpnet-base-v2"
        
        # === ESTADÍSTICAS DEL PROCESO ===
        # Contadores para monitorear el progreso
        self.stats = {
            'pdfs_processed': 0,     # Número de PDFs procesados
            'texts_created': 0,      # Archivos TXT generados
            'chunks_generated': 0,   # Fragmentos de texto creados
            'embeddings_created': 0, # Vectores de embeddings generados
            'total_time': 0,         # Tiempo total de procesamiento
            'errors': []             # Lista de errores encontrados
        }
        
        logger.info(f"🔧 ETL Processor inicializado")
        logger.info(f"📁 Directorio de datos: {self.data_dir}")
        logger.info(f"🤖 Modelo de embeddings: {self.embedding_model}")
        logger.info(f"📊 Chunk size: {self.chunk_size}, Overlap: {self.chunk_overlap}")

    def create_directories(self):
        """
        Crea la estructura de directorios necesaria para el proyecto
        
        Esta función asegura que todos los directorios requeridos existan
        antes de comenzar el procesamiento de documentos.
        """
        directories = [
            self.data_dir,     # data/
            self.pdfs_dir,     # data/pdfs/
            self.texts_dir,    # data/texts/
            self.chroma_dir    # chroma_db_simple/
        ]
        
        for directory in directories:
            try:
                # Crear directorio con parents=True (crea directorios padre si no existen)
                # exist_ok=True evita errores si el directorio ya existe
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"📁 Directorio asegurado: {directory}")
            except Exception as e:
                error_msg = f"❌ Error creando directorio {directory}: {e}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)

    def extract_from_pdfs(self) -> bool:
        """
        FASE EXTRACT: Extrae texto de todos los PDFs en el directorio pdfs/
        
        Utiliza pdfplumber como biblioteca principal para extracción de texto,
        con PyPDF2 como fallback en caso de errores.
        
        Returns:
            bool: True si la extracción fue exitosa, False en caso de errores críticos
        """
        logger.info("🔄 FASE EXTRACT: Iniciando extracción de PDFs")
        
        # Verificar que el directorio de PDFs existe
        if not self.pdfs_dir.exists():
            logger.warning(f"⚠️ Directorio de PDFs no existe: {self.pdfs_dir}")
            return False
        
        # Buscar todos los archivos PDF en el directorio
        pdf_files = list(self.pdfs_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"⚠️ No se encontraron archivos PDF en {self.pdfs_dir}")
            return False
        
        logger.info(f"📄 Encontrados {len(pdf_files)} archivos PDF para procesar")
        
        # Procesar cada PDF individualmente
        for pdf_file in pdf_files:
            try:
                self._extract_single_pdf(pdf_file)
                self.stats['pdfs_processed'] += 1
                
            except Exception as e:
                error_msg = f"❌ Error procesando {pdf_file.name}: {e}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)
                continue  # Continuar con el siguiente PDF
        
        logger.info(f"✅ Extracción completada: {self.stats['pdfs_processed']} PDFs procesados")
        return True

    def _extract_single_pdf(self, pdf_path: Path):
        """
        Extrae texto de un único archivo PDF
        
        Esta función utiliza pdfplumber como método principal de extracción
        porque ofrece mejor calidad en la extracción de texto y manejo de layout.
        
        Args:
            pdf_path: Ruta al archivo PDF a procesar
        """
        logger.info(f"📖 Procesando: {pdf_path.name}")
        
        # Determinar el nombre del archivo TXT de salida
        txt_filename = pdf_path.stem + ".txt"  # stem = nombre sin extensión
        txt_path = self.texts_dir / txt_filename
        
        # Si el archivo TXT ya existe, saltar (evitar reprocesamiento)
        if txt_path.exists():
            logger.info(f"⏭️ Archivo TXT ya existe: {txt_filename}")
            return
        
        extracted_text = ""
        
        try:
            # === MÉTODO PRINCIPAL: pdfplumber ===
            # pdfplumber ofrece extracción de texto más precisa y manejo de tablas
            import pdfplumber
            
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"📑 Extrayendo texto de {len(pdf.pages)} páginas")
                
                # Procesar cada página del PDF
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        # Extraer texto de la página actual
                        page_text = page.extract_text()
                        
                        if page_text:
                            # Limpiar y procesar el texto extraído
                            cleaned_text = self._clean_extracted_text(page_text)
                            extracted_text += f"\n{cleaned_text}\n"
                            
                        if page_num % 10 == 0:  # Log cada 10 páginas
                            logger.info(f"   📄 Procesadas {page_num}/{len(pdf.pages)} páginas")
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error en página {page_num}: {e}")
                        continue  # Continuar con la siguiente página
        
        except ImportError:
            # Si pdfplumber no está disponible, usar PyPDF2 como fallback
            logger.warning("⚠️ pdfplumber no disponible, usando PyPDF2")
            extracted_text = self._extract_with_pypdf2(pdf_path)
            
        except Exception as e:
            # Si pdfplumber falla, intentar con PyPDF2
            logger.warning(f"⚠️ Error con pdfplumber: {e}, intentando PyPDF2")
            extracted_text = self._extract_with_pypdf2(pdf_path)
        
        # Verificar que se extrajo texto válido
        if not extracted_text or len(extracted_text.strip()) < 100:
            logger.warning(f"⚠️ Texto extraído insuficiente de {pdf_path.name}")
            return
        
        # Guardar el texto extraído en archivo TXT
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            
            self.stats['texts_created'] += 1
            logger.info(f"💾 Texto guardado: {txt_filename} ({len(extracted_text)} caracteres)")
            
        except Exception as e:
            error_msg = f"❌ Error guardando {txt_filename}: {e}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)

    def _clean_extracted_text(self, text: str) -> str:
        """
        Limpia y normaliza el texto extraído de PDFs
        
        Esta función aplica una serie de transformaciones para mejorar
        la calidad del texto antes del procesamiento de embeddings.
        
        Args:
            text: Texto crudo extraído del PDF
            
        Returns:
            str: Texto limpio y normalizado
        """
        if not text:
            return ""
        
        # === LIMPIEZA DE CARACTERES ===
        # Normalizar espacios en blanco
        text = re.sub(r'\s+', ' ', text)  # Múltiples espacios → un espacio
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Múltiples saltos → doble salto
        
        # Eliminar caracteres de control y caracteres especiales problemáticos
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', text)
        
        # === NORMALIZACIÓN DE TEXTO ACADÉMICO ===
        # Preservar referencias académicas importantes
        # Patrón para referencias como (Autor, 2020) o (Autor et al., 2020)
        text = re.sub(r'\(\s*([A-Z][a-zA-Z]+(?:\s+et\s+al\.)?),?\s*(\d{4})\s*\)', 
                     r'(\1, \2)', text)
        
        # Normalizar puntuación
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)  # Espacios después de puntos
        text = re.sub(r'\s*([,;:])\s*', r'\1 ', text)  # Espacios alrededor de puntuación
        
        # === LIMPIEZA ESPECÍFICA DE PDFs ===
        # Eliminar headers/footers comunes
        text = re.sub(r'^página\s+\d+.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)  # Números de página solos
        
        # Limpiar espacios finales
        text = text.strip()
        
        return text

    def _extract_with_pypdf2(self, pdf_path: Path) -> str:
        """
        Método de fallback para extracción usando PyPDF2
        
        Se utiliza cuando pdfplumber no está disponible o falla.
        PyPDF2 es más básico pero más compatible.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            str: Texto extraído con PyPDF2
        """
        try:
            import PyPDF2
            
            extracted_text = ""
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                logger.info(f"📑 Extrayendo con PyPDF2: {len(pdf_reader.pages)} páginas")
                
                # Procesar cada página
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            cleaned_text = self._clean_extracted_text(page_text)
                            extracted_text += f"\n{cleaned_text}\n"
                    except Exception as e:
                        logger.warning(f"⚠️ Error PyPDF2 página {page_num}: {e}")
                        continue
            
            return extracted_text
            
        except ImportError:
            logger.error("❌ PyPDF2 no disponible")
            return ""
        except Exception as e:
            logger.error(f"❌ Error con PyPDF2: {e}")
            return ""

    def smart_chunk_text(self, force_rechunk: bool = False) -> List[Dict]:
        """
        FASE TRANSFORM: Fragmenta texto en chunks inteligentes
        
        Esta función implementa un algoritmo de chunking que:
        1. Respeta la estructura del documento (párrafos, secciones)
        2. Preserva referencias académicas
        3. Mantiene contexto con overlap entre chunks
        4. Optimiza para embeddings de 768 dimensiones
        
        Args:
            force_rechunk: Si True, reprocessa todos los textos
            
        Returns:
            List[Dict]: Lista de chunks con metadata
        """
        logger.info("🔄 FASE TRANSFORM: Iniciando chunking inteligente")
        
        # Buscar todos los archivos TXT
        txt_files = list(self.texts_dir.glob("*.txt"))
        
        if not txt_files:
            logger.warning(f"⚠️ No se encontraron archivos TXT en {self.texts_dir}")
            return []
        
        logger.info(f"📝 Encontrados {len(txt_files)} archivos TXT para chunking")
        
        all_chunks = []
        
        # Procesar cada archivo TXT
        for txt_file in txt_files:
            try:
                chunks = self._chunk_single_file(txt_file, force_rechunk)
                all_chunks.extend(chunks)
                
            except Exception as e:
                error_msg = f"❌ Error chunking {txt_file.name}: {e}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)
                continue
        
        self.stats['chunks_generated'] = len(all_chunks)
        logger.info(f"✅ Chunking completado: {len(all_chunks)} chunks generados")
        
        return all_chunks

    def _chunk_single_file(self, txt_path: Path, force_rechunk: bool) -> List[Dict]:
        """
        Fragmenta un único archivo de texto en chunks inteligentes
        
        Args:
            txt_path: Ruta al archivo TXT
            force_rechunk: Si True, regenera chunks aunque ya existan
            
        Returns:
            List[Dict]: Lista de chunks con metadata para este archivo
        """
        logger.info(f"✂️ Chunking: {txt_path.name}")
        
        # Leer el contenido del archivo
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"❌ Error leyendo {txt_path.name}: {e}")
            return []
        
        if not content.strip():
            logger.warning(f"⚠️ Archivo vacío: {txt_path.name}")
            return []
        
        # === ALGORITMO DE CHUNKING INTELIGENTE ===
        
        # 1. Dividir en párrafos (preservar estructura)
        paragraphs = self._split_into_paragraphs(content)
        
        # 2. Agrupar párrafos en chunks respetando límites
        chunks = self._group_paragraphs_into_chunks(paragraphs)
        
        # 3. Aplicar overlap entre chunks (preservar contexto)
        chunks_with_overlap = self._apply_chunk_overlap(chunks)
        
        # 4. Crear metadata para cada chunk
        chunks_with_metadata = []
        for i, chunk_text in enumerate(chunks_with_overlap):
            # Crear identificador único para el chunk
            chunk_id = f"{txt_path.stem}_chunk_{i:03d}"
            
            # Metadata completa para trazabilidad
            metadata = {
                'chunk_id': chunk_id,           # ID único del chunk
                'source_file': txt_path.name,   # Archivo fuente
                'chunk_index': i,               # Índice dentro del archivo
                'total_chunks': len(chunks_with_overlap),  # Total de chunks del archivo
                'char_count': len(chunk_text),  # Número de caracteres
                'word_count': len(chunk_text.split()),  # Número aproximado de palabras
                'has_references': self._detect_academic_references(chunk_text),  # Referencias académicas
                'file_stem': txt_path.stem      # Nombre del archivo sin extensión
            }
            
            chunks_with_metadata.append({
                'text': chunk_text,
                'metadata': metadata
            })
        
        logger.info(f"✂️ {txt_path.name}: {len(chunks_with_metadata)} chunks creados")
        return chunks_with_metadata

    def _split_into_paragraphs(self, content: str) -> List[str]:
        """
        Divide el contenido en párrafos respetando la estructura del documento
        
        Args:
            content: Texto completo del documento
            
        Returns:
            List[str]: Lista de párrafos
        """
        # Dividir por dobles saltos de línea (párrafos)
        paragraphs = re.split(r'\n\s*\n', content)
        
        # Limpiar y filtrar párrafos
        cleaned_paragraphs = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            
            # Filtrar párrafos muy cortos (probablemente ruido)
            if len(paragraph) > 50:  # Mínimo 50 caracteres
                cleaned_paragraphs.append(paragraph)
        
        return cleaned_paragraphs

    def _group_paragraphs_into_chunks(self, paragraphs: List[str]) -> List[str]:
        """
        Agrupa párrafos en chunks respetando el límite de tamaño
        
        Args:
            paragraphs: Lista de párrafos
            
        Returns:
            List[str]: Lista de chunks
        """
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Verificar si agregar este párrafo excedería el límite
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            
            if len(potential_chunk) <= self.chunk_size:
                # El párrafo cabe en el chunk actual
                current_chunk = potential_chunk
            else:
                # El párrafo no cabe, finalizar chunk actual
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Iniciar nuevo chunk
                if len(paragraph) <= self.chunk_size:
                    current_chunk = paragraph
                else:
                    # Párrafo muy largo, dividir en sub-chunks
                    sub_chunks = self._split_long_paragraph(paragraph)
                    chunks.extend(sub_chunks[:-1])  # Agregar todos excepto el último
                    current_chunk = sub_chunks[-1]  # El último se vuelve el chunk actual
        
        # Agregar el último chunk si no está vacío
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """
        Divide un párrafo muy largo en sub-chunks más pequeños
        
        Args:
            paragraph: Párrafo que excede el tamaño máximo
            
        Returns:
            List[str]: Lista de sub-chunks
        """
        # Intentar dividir por oraciones
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Si la oración sola es muy larga, dividir por palabras
                if len(sentence) > self.chunk_size:
                    word_chunks = self._split_by_words(sentence)
                    chunks.extend(word_chunks[:-1])
                    current_chunk = word_chunks[-1]
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def _split_by_words(self, text: str) -> List[str]:
        """
        Divide texto por palabras cuando las oraciones son muy largas
        
        Args:
            text: Texto a dividir
            
        Returns:
            List[str]: Lista de chunks por palabras
        """
        words = text.split()
        chunks = []
        current_chunk = ""
        
        for word in words:
            potential_chunk = current_chunk + " " + word if current_chunk else word
            
            if len(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = word
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def _apply_chunk_overlap(self, chunks: List[str]) -> List[str]:
        """
        Aplica overlap entre chunks para preservar contexto
        
        El overlap ayuda a mantener continuidad semántica entre fragmentos,
        especialmente importante para referencias que cruzan límites de chunks.
        
        Args:
            chunks: Lista de chunks sin overlap
            
        Returns:
            List[str]: Lista de chunks con overlap aplicado
        """
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = [chunks[0]]  # El primer chunk no necesita overlap previo
        
        for i in range(1, len(chunks)):
            current_chunk = chunks[i]
            previous_chunk = chunks[i-1]
            
            # Extraer las últimas palabras del chunk anterior para overlap
            overlap_text = self._extract_overlap_text(previous_chunk, self.chunk_overlap)
            
            # Combinar overlap con chunk actual
            if overlap_text:
                overlapped_chunk = overlap_text + "\n\n" + current_chunk
            else:
                overlapped_chunk = current_chunk
            
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks

    def _extract_overlap_text(self, chunk: str, overlap_size: int) -> str:
        """
        Extrae texto de overlap del final de un chunk
        
        Args:
            chunk: Chunk del cual extraer overlap
            overlap_size: Tamaño del overlap en caracteres
            
        Returns:
            str: Texto de overlap
        """
        if len(chunk) <= overlap_size:
            return chunk
        
        # Extraer últimos caracteres
        overlap_text = chunk[-overlap_size:]
        
        # Intentar cortar en límite de palabra para evitar cortes bruscos
        space_index = overlap_text.find(' ')
        if space_index > 0:
            overlap_text = overlap_text[space_index:].strip()
        
        return overlap_text

    def _detect_academic_references(self, text: str) -> bool:
        """
        Detecta si el texto contiene referencias académicas
        
        Args:
            text: Texto a analizar
            
        Returns:
            bool: True si contiene referencias académicas
        """
        # Patrones de referencias académicas comunes
        patterns = [
            r'\([A-Z][a-zA-Z]+,?\s+\d{4}\)',  # (Autor, 2020)
            r'\([A-Z][a-zA-Z]+\s+et\s+al\.,?\s+\d{4}\)',  # (Autor et al., 2020)
            r'\d{4}[\):]',  # Años seguidos de ) o :
            r'[Ss]egún\s+[A-Z][a-zA-Z]+',  # Según Autor
            r'[Cc]omo\s+señala\s+[A-Z][a-zA-Z]+',  # Como señala Autor
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        
        return False

    def generate_embeddings_and_load(self, chunks: List[Dict]) -> bool:
        """
        FASE LOAD: Genera embeddings y carga en ChromaDB
        
        Esta es la fase final del ETL que:
        1. Inicializa el modelo de embeddings (all-mpnet-base-v2)
        2. Genera vectores de 768 dimensiones para cada chunk
        3. Almacena vectores y metadata en ChromaDB
        4. Crea índices para búsqueda eficiente
        
        Args:
            chunks: Lista de chunks con metadata
            
        Returns:
            bool: True si la carga fue exitosa
        """
        logger.info("🔄 FASE LOAD: Generando embeddings y cargando en ChromaDB")
        
        if not chunks:
            logger.warning("⚠️ No hay chunks para procesar")
            return False
        
        try:
            # === INICIALIZACIÓN DE COMPONENTES ===
            
            # 1. Importar bibliotecas necesarias
            from sentence_transformers import SentenceTransformer
            import chromadb
            
            # 2. Inicializar modelo de embeddings
            logger.info(f"🤖 Cargando modelo: {self.embedding_model}")
            model = SentenceTransformer(self.embedding_model)
            
            # Información del modelo cargado
            logger.info(f"📊 Dimensiones del modelo: {model.get_sentence_embedding_dimension()}")
            
            # 3. Inicializar cliente ChromaDB
            logger.info(f"🗄️ Inicializando ChromaDB en: {self.chroma_dir}")
            client = chromadb.PersistentClient(path=str(self.chroma_dir))
            
            # 4. Crear o obtener colección
            collection_name = "simple_rag_docs"
            
            # Eliminar colección existente si se está forzando recreación
            try:
                existing_collection = client.get_collection(collection_name)
                logger.info("🗑️ Eliminando colección existente para recrear")
                client.delete_collection(collection_name)
            except:
                pass  # La colección no existe, continuar
            
            # Crear nueva colección
            collection = client.create_collection(
                name=collection_name,
                metadata={"description": "RAG documents with academic embeddings"}
            )
            
            logger.info(f"✅ Colección '{collection_name}' creada")
            
            # === PROCESAMIENTO EN LOTES ===
            
            batch_size = 50  # Procesar en lotes para eficiencia de memoria
            total_chunks = len(chunks)
            
            logger.info(f"📦 Procesando {total_chunks} chunks en lotes de {batch_size}")
            
            for i in range(0, total_chunks, batch_size):
                batch = chunks[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_chunks + batch_size - 1) // batch_size
                
                logger.info(f"🔄 Procesando lote {batch_num}/{total_batches} ({len(batch)} chunks)")
                
                # Procesar lote actual
                success = self._process_embedding_batch(model, collection, batch, i)
                
                if not success:
                    logger.error(f"❌ Error en lote {batch_num}")
                    continue
                
                # Actualizar estadísticas
                self.stats['embeddings_created'] += len(batch)
                
                # Log de progreso
                progress = (i + len(batch)) / total_chunks * 100
                logger.info(f"📈 Progreso: {progress:.1f}% ({i + len(batch)}/{total_chunks})")
            
            # === VERIFICACIÓN FINAL ===
            
            # Verificar que la colección se pobló correctamente
            final_count = collection.count()
            logger.info(f"🎯 Verificación final: {final_count} documentos en ChromaDB")
            
            if final_count != total_chunks:
                logger.warning(f"⚠️ Discrepancia: esperados {total_chunks}, guardados {final_count}")
            
            logger.info(f"✅ LOAD completado: {final_count} embeddings generados y almacenados")
            return True
            
        except Exception as e:
            error_msg = f"❌ Error en generación de embeddings: {e}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return False

    def _process_embedding_batch(self, model, collection, batch: List[Dict], start_index: int) -> bool:
        """
        Procesa un lote de chunks para generar embeddings
        
        Args:
            model: Modelo de SentenceTransformers cargado
            collection: Colección de ChromaDB
            batch: Lote de chunks a procesar
            start_index: Índice de inicio para IDs únicos
            
        Returns:
            bool: True si el lote se procesó exitosamente
        """
        try:
            # === PREPARACIÓN DE DATOS ===
            
            # Extraer textos y metadatos del lote
            texts = [chunk['text'] for chunk in batch]
            metadatas = [chunk['metadata'] for chunk in batch]
            
            # Generar IDs únicos para cada chunk
            ids = [f"doc_{start_index + i:06d}" for i in range(len(batch))]
            
            # === GENERACIÓN DE EMBEDDINGS ===
            
            logger.info(f"🧠 Generando embeddings para {len(texts)} textos...")
            
            # Generar embeddings usando el modelo
            # El modelo all-mpnet-base-v2 produce vectores de 768 dimensiones
            embeddings = model.encode(
                texts,
                batch_size=32,          # Lotes internos para eficiencia GPU/CPU
                show_progress_bar=False, # Evitar logs excesivos
                convert_to_numpy=True   # Convertir a numpy para ChromaDB
            )
            
            logger.info(f"🎯 Embeddings generados: {embeddings.shape}")
            
            # === ALMACENAMIENTO EN CHROMADB ===
            
            # Convertir embeddings a lista (requerido por ChromaDB)
            embeddings_list = embeddings.tolist()
            
            # Insertar en ChromaDB
            collection.add(
                embeddings=embeddings_list,  # Vectores de 768 dimensiones
                metadatas=metadatas,         # Metadata de cada chunk
                documents=texts,             # Texto original para referencia
                ids=ids                      # IDs únicos
            )
            
            logger.info(f"💾 Lote guardado en ChromaDB: {len(ids)} documentos")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error procesando lote: {e}")
            return False

    def run_complete_etl(self, force: bool = False):
        """
        Ejecuta el pipeline ETL completo
        
        Esta función orquesta todo el proceso ETL:
        1. Crear directorios necesarios
        2. Extraer texto de PDFs (EXTRACT)
        3. Procesar y fragmentar texto (TRANSFORM)
        4. Generar embeddings y cargar en ChromaDB (LOAD)
        5. Generar reporte de estadísticas
        
        Args:
            force: Si True, regenera todo desde cero
        """
        start_time = time.time()
        
        logger.info("🚀 INICIANDO PROCESO ETL COMPLETO")
        logger.info("=" * 50)
        
        try:
            # === FASE 0: PREPARACIÓN ===
            logger.info("📁 Fase 0: Preparación de directorios")
            self.create_directories()
            
            # === FASE 1: EXTRACT ===
            logger.info("\n📖 Fase 1: EXTRACT - Extracción de PDFs")
            extract_success = self.extract_from_pdfs()
            
            if not extract_success:
                logger.error("❌ Error en fase EXTRACT")
                return False
            
            # === FASE 2: TRANSFORM ===
            logger.info("\n✂️ Fase 2: TRANSFORM - Chunking inteligente")
            chunks = self.smart_chunk_text(force_rechunk=force)
            
            if not chunks:
                logger.error("❌ Error en fase TRANSFORM")
                return False
            
            # === FASE 3: LOAD ===
            logger.info("\n🧠 Fase 3: LOAD - Embeddings y ChromaDB")
            load_success = self.generate_embeddings_and_load(chunks)
            
            if not load_success:
                logger.error("❌ Error en fase LOAD")
                return False
            
            # === FINALIZACIÓN ===
            end_time = time.time()
            self.stats['total_time'] = end_time - start_time
            
            # Generar reporte final
            self._generate_final_report()
            
            logger.info("🎉 PROCESO ETL COMPLETADO EXITOSAMENTE")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error crítico en ETL: {e}")
            self.stats['errors'].append(f"Error crítico: {e}")
            return False

    def _generate_final_report(self):
        """
        Genera reporte final con estadísticas del proceso ETL
        """
        logger.info("\n📊 REPORTE FINAL DEL PROCESO ETL")
        logger.info("=" * 40)
        
        # Estadísticas de archivos
        logger.info(f"📄 PDFs procesados: {self.stats['pdfs_processed']}")
        logger.info(f"📝 Archivos TXT creados: {self.stats['texts_created']}")
        logger.info(f"✂️ Chunks generados: {self.stats['chunks_generated']}")
        logger.info(f"🧠 Embeddings creados: {self.stats['embeddings_created']}")
        
        # Tiempo total
        total_minutes = self.stats['total_time'] / 60
        logger.info(f"⏱️ Tiempo total: {total_minutes:.2f} minutos")
        
        # Métricas de rendimiento
        if self.stats['total_time'] > 0:
            chunks_per_second = self.stats['chunks_generated'] / self.stats['total_time']
            logger.info(f"🚀 Velocidad: {chunks_per_second:.2f} chunks/segundo")
        
        # Errores encontrados
        if self.stats['errors']:
            logger.warning(f"⚠️ Errores encontrados: {len(self.stats['errors'])}")
            for error in self.stats['errors'][-5:]:  # Mostrar últimos 5 errores
                logger.warning(f"   - {error}")
        else:
            logger.info("✅ Proceso completado sin errores")
        
        # Información de la base de datos
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(self.chroma_dir))
            collection = client.get_collection("simple_rag_docs")
            final_count = collection.count()
            logger.info(f"🗄️ ChromaDB: {final_count} documentos almacenados")
        except:
            logger.warning("⚠️ No se pudo verificar ChromaDB")

def main():
    """
    Función principal para ejecutar el ETL desde línea de comandos
    
    Acepta argumentos de línea de comandos para personalizar el procesamiento:
    - --force: Regenerar todo desde cero
    - --chunk-size: Tamaño de chunks personalizado
    - --model: Modelo de embeddings alternativo
    """
    # === CONFIGURACIÓN DE ARGUMENTOS ===
    parser = argparse.ArgumentParser(description='Procesador ETL completo para RAG Asistente')
    
    parser.add_argument('--force', action='store_true', 
                       help='Regenerar todo desde cero (eliminar datos existentes)')
    
    parser.add_argument('--chunk-size', type=int, default=800,
                       help='Tamaño de chunks en caracteres (default: 800)')
    
    parser.add_argument('--chunk-overlap', type=int, default=100,
                       help='Solapamiento entre chunks (default: 100)')
    
    parser.add_argument('--model', type=str, default='sentence-transformers/all-mpnet-base-v2',
                       help='Modelo de embeddings a utilizar')
    
    args = parser.parse_args()
    
    # === INICIALIZACIÓN DEL PROCESADOR ===
    logger.info("🔧 Inicializando procesador ETL con configuración:")
    logger.info(f"   - Force rebuild: {args.force}")
    logger.info(f"   - Chunk size: {args.chunk_size}")
    logger.info(f"   - Chunk overlap: {args.chunk_overlap}")
    logger.info(f"   - Modelo: {args.model}")
    
    # Crear procesador con configuración personalizada
    processor = RAGETLProcessor()
    processor.chunk_size = args.chunk_size
    processor.chunk_overlap = args.chunk_overlap
    processor.embedding_model = args.model
    
    # === EJECUCIÓN DEL PROCESO ===
    try:
        success = processor.run_complete_etl(force=args.force)
        
        if success:
            logger.info("🎉 ETL completado exitosamente")
            sys.exit(0)
        else:
            logger.error("❌ ETL falló")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("⚠️ Proceso interrumpido por usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()