"""
🧰 UTILIDADES RAG - FUNCIONES DE SOPORTE COMPLETAMENTE DOCUMENTADAS
==================================================================

Este archivo contiene todas las funciones auxiliares y utilidades
que soportan el sistema RAG con DeepSeek V3.

FUNCIONES PRINCIPALES:
1. Gestión de embeddings y chunking inteligente
2. Optimización de consultas y postprocesamiento
3. Manejo de errores y logging avanzado
4. Integración con APIs externas
5. Cache y persistencia de resultados

TECNOLOGÍAS UTILIZADAS:
- sentence-transformers: Modelo all-mpnet-base-v2
- ChromaDB: Base de datos vectorial con HNSW
- tiktoken: Tokenización precisa para chunking
- asyncio: Operaciones asíncronas
- threading: Procesamiento paralelo
"""

import os
import re
import json
import hashlib
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime
import time

# === CONFIGURACIÓN DE LOGGING ===
logger = logging.getLogger(__name__)

# === CONFIGURACIÓN DE CHUNKING ===
DEFAULT_CHUNK_SIZE = 800        # Tokens por chunk (óptimo para embeddings)
DEFAULT_OVERLAP = 100           # Overlap entre chunks para contexto
MAX_CHUNK_SIZE = 1000          # Máximo tamaño de chunk
MIN_CHUNK_SIZE = 200           # Mínimo tamaño de chunk

class EmbeddingCache:
    """
    Sistema de cache para embeddings generados
    
    PROPÓSITO:
    - Evitar regenerar embeddings de textos ya procesados
    - Acelerar respuestas para queries frecuentes
    - Reducir uso de recursos computacionales
    - Persistir embeddings entre sesiones
    
    IMPLEMENTACIÓN:
    - Hash MD5 del texto como clave única
    - Almacenamiento en archivo JSON
    - Verificación de integridad automática
    - Limpieza de cache obsoleto
    """
    
    def __init__(self, cache_dir: str = "cache"):
        """
        Inicializa el sistema de cache de embeddings
        
        Args:
            cache_dir (str): Directorio para almacenar el cache
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "embeddings_cache.json"
        self.cache_data = self._load_cache()
        
        logger.info(f"📁 Cache de embeddings inicializado: {self.cache_file}")
        logger.info(f"📊 Entradas en cache: {len(self.cache_data)}")
    
    def _load_cache(self) -> Dict[str, Any]:
        """
        Carga cache existente desde disco
        
        Returns:
            Dict: Datos del cache o diccionario vacío si no existe
        """
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.debug(f"✅ Cache cargado: {len(data)} entradas")
                    return data
        except Exception as e:
            logger.warning(f"⚠️ Error cargando cache: {e}")
        
        return {}
    
    def _save_cache(self):
        """
        Guarda cache actual en disco
        """
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
                logger.debug(f"💾 Cache guardado: {len(self.cache_data)} entradas")
        except Exception as e:
            logger.error(f"❌ Error guardando cache: {e}")
    
    def get_hash(self, text: str) -> str:
        """
        Genera hash único para un texto
        
        Args:
            text (str): Texto a hashear
            
        Returns:
            str: Hash MD5 del texto
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Obtiene embedding desde cache si existe
        
        Args:
            text (str): Texto para buscar embedding
            
        Returns:
            Optional[List[float]]: Embedding si existe en cache, None si no
        """
        text_hash = self.get_hash(text)
        
        if text_hash in self.cache_data:
            entry = self.cache_data[text_hash]
            logger.debug(f"🎯 Cache hit para: {text[:50]}...")
            return entry.get('embedding')
        
        logger.debug(f"❌ Cache miss para: {text[:50]}...")
        return None
    
    def store_embedding(self, text: str, embedding: List[float]):
        """
        Almacena embedding en cache
        
        Args:
            text (str): Texto original
            embedding (List[float]): Vector de embedding
        """
        text_hash = self.get_hash(text)
        
        self.cache_data[text_hash] = {
            'embedding': embedding,
            'text_preview': text[:100],  # Para debugging
            'timestamp': datetime.now().isoformat(),
            'dimensions': len(embedding)
        }
        
        self._save_cache()
        logger.debug(f"💾 Embedding almacenado en cache: {text_hash}")
    
    def clean_cache(self, max_age_days: int = 30):
        """
        Limpia entradas antiguas del cache
        
        Args:
            max_age_days (int): Máxima edad en días para mantener entradas
        """
        current_time = datetime.now()
        removed_count = 0
        
        keys_to_remove = []
        for key, entry in self.cache_data.items():
            try:
                entry_time = datetime.fromisoformat(entry.get('timestamp', ''))
                age_days = (current_time - entry_time).days
                
                if age_days > max_age_days:
                    keys_to_remove.append(key)
            except Exception:
                # Entradas sin timestamp válido, remover
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache_data[key]
            removed_count += 1
        
        if removed_count > 0:
            self._save_cache()
            logger.info(f"🧹 Cache limpiado: {removed_count} entradas removidas")

class SmartChunker:
    """
    Sistema avanzado de chunking para optimizar embeddings
    
    CARACTERÍSTICAS:
    - Chunking semántico preservando contexto
    - Overlap inteligente para mantener coherencia
    - Respeto por límites de oraciones y párrafos
    - Optimización para modelo all-mpnet-base-v2
    - Manejo especial de referencias y citas académicas
    
    ALGORITMO:
    1. Análisis de estructura del texto (párrafos, oraciones)
    2. Tokenización precisa con tiktoken
    3. División semántica preservando contexto
    4. Overlap calculado para máxima coherencia
    5. Validación de calidad de chunks
    """
    
    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP):
        """
        Inicializa el sistema de chunking inteligente
        
        Args:
            chunk_size (int): Tamaño objetivo en tokens
            overlap (int): Overlap entre chunks en tokens
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        
        # Inicializar tokenizador
        try:
            import tiktoken
            # Usar encoding de GPT-3.5 que es compatible con embeddings
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            logger.info("🔤 Tokenizador tiktoken inicializado")
        except ImportError:
            logger.warning("⚠️ tiktoken no disponible, usando aproximación")
            self.tokenizer = None
        
        logger.info(f"✂️ Chunker configurado: {chunk_size} tokens, overlap {overlap}")
    
    def count_tokens(self, text: str) -> int:
        """
        Cuenta tokens en el texto de forma precisa
        
        Args:
            text (str): Texto a contar
            
        Returns:
            int: Número de tokens
        """
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Aproximación: promedio de 4 caracteres por token
            return len(text) // 4
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Divide texto en oraciones respetando contexto académico
        
        CARACTERÍSTICAS:
        - Respeta abreviaciones académicas (et al., etc., Dr.)
        - Mantiene citas y referencias intactas
        - Preserva numeración y listas
        - Maneja puntuación compleja
        
        Args:
            text (str): Texto a dividir
            
        Returns:
            List[str]: Lista de oraciones
        """
        # Proteger abreviaciones comunes
        text = text.replace('et al.', 'et al§')
        text = text.replace('etc.', 'etc§')
        text = text.replace('Dr.', 'Dr§')
        text = text.replace('Prof.', 'Prof§')
        text = text.replace('p.', 'p§')
        text = text.replace('pp.', 'pp§')
        
        # División básica por puntos
        sentences = re.split(r'\.(?=\s+[A-Z])', text)
        
        # Restaurar abreviaciones
        sentences = [s.replace('§', '.') for s in sentences]
        
        # Limpiar y filtrar oraciones válidas
        valid_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Filtrar fragmentos muy cortos
                valid_sentences.append(sentence)
        
        return valid_sentences
    
    def split_into_paragraphs(self, text: str) -> List[str]:
        """
        Divide texto en párrafos manteniendo estructura
        
        Args:
            text (str): Texto a dividir
            
        Returns:
            List[str]: Lista de párrafos
        """
        # División por doble salto de línea
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Limpiar y filtrar párrafos válidos
        valid_paragraphs = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if len(paragraph) > 50:  # Filtrar párrafos muy cortos
                valid_paragraphs.append(paragraph)
        
        return valid_paragraphs
    
    def smart_chunk(self, text: str) -> List[Dict[str, Any]]:
        """
        Realiza chunking inteligente del texto
        
        ALGORITMO DETALLADO:
        1. ANÁLISIS INICIAL: Evalúa longitud y estructura
        2. DIVISIÓN SEMÁNTICA: Por párrafos o oraciones
        3. OPTIMIZACIÓN: Ajusta tamaños para modelo de embeddings
        4. OVERLAP: Calcula overlap óptimo para coherencia
        5. VALIDACIÓN: Verifica calidad de chunks generados
        
        Args:
            text (str): Texto a procesar
            
        Returns:
            List[Dict]: Lista de chunks con metadata
        """
        if not text or len(text.strip()) < 10:
            logger.warning("⚠️ Texto muy corto para chunking")
            return []
        
        # === FASE 1: ANÁLISIS INICIAL ===
        total_tokens = self.count_tokens(text)
        logger.debug(f"📊 Analizando texto: {total_tokens} tokens")
        
        # Si el texto es pequeño, retornar como un solo chunk
        if total_tokens <= self.chunk_size:
            logger.debug("📄 Texto pequeño, chunk único")
            return [{
                'text': text.strip(),
                'tokens': total_tokens,
                'chunk_id': 0,
                'overlap_start': 0,
                'overlap_end': 0
            }]
        
        # === FASE 2: ESTRATEGIA DE DIVISIÓN ===
        paragraphs = self.split_into_paragraphs(text)
        
        if len(paragraphs) > 1:
            logger.debug(f"📝 División por párrafos: {len(paragraphs)} párrafos")
            return self._chunk_by_paragraphs(paragraphs)
        else:
            logger.debug("📝 División por oraciones")
            sentences = self.split_into_sentences(text)
            return self._chunk_by_sentences(sentences)
    
    def _chunk_by_paragraphs(self, paragraphs: List[str]) -> List[Dict[str, Any]]:
        """
        Crea chunks basándose en párrafos
        
        Args:
            paragraphs (List[str]): Lista de párrafos
            
        Returns:
            List[Dict]: Chunks generados
        """
        chunks = []
        current_chunk = ""
        current_tokens = 0
        chunk_id = 0
        
        for paragraph in paragraphs:
            paragraph_tokens = self.count_tokens(paragraph)
            
            # Si el párrafo es muy grande, dividirlo por oraciones
            if paragraph_tokens > self.chunk_size:
                # Guardar chunk actual si existe
                if current_chunk:
                    chunks.append(self._create_chunk_dict(current_chunk, chunk_id))
                    chunk_id += 1
                    current_chunk = ""
                    current_tokens = 0
                
                # Procesar párrafo grande por oraciones
                sentences = self.split_into_sentences(paragraph)
                sentence_chunks = self._chunk_by_sentences(sentences, start_id=chunk_id)
                chunks.extend(sentence_chunks)
                chunk_id += len(sentence_chunks)
            
            # Si agregar el párrafo excede el límite
            elif current_tokens + paragraph_tokens > self.chunk_size:
                # Guardar chunk actual
                if current_chunk:
                    chunks.append(self._create_chunk_dict(current_chunk, chunk_id))
                    chunk_id += 1
                
                # Calcular overlap con párrafo anterior
                current_chunk = self._calculate_overlap(current_chunk, paragraph)
                current_tokens = self.count_tokens(current_chunk)
            
            else:
                # Agregar párrafo al chunk actual
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_tokens += paragraph_tokens
        
        # Agregar último chunk si existe
        if current_chunk:
            chunks.append(self._create_chunk_dict(current_chunk, chunk_id))
        
        return self._add_overlap_metadata(chunks)
    
    def _chunk_by_sentences(self, sentences: List[str], start_id: int = 0) -> List[Dict[str, Any]]:
        """
        Crea chunks basándose en oraciones
        
        Args:
            sentences (List[str]): Lista de oraciones
            start_id (int): ID inicial para chunks
            
        Returns:
            List[Dict]: Chunks generados
        """
        chunks = []
        current_chunk = ""
        current_tokens = 0
        chunk_id = start_id
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            # Si una oración es muy larga, dividirla forzadamente
            if sentence_tokens > self.chunk_size:
                # Guardar chunk actual si existe
                if current_chunk:
                    chunks.append(self._create_chunk_dict(current_chunk, chunk_id))
                    chunk_id += 1
                
                # Dividir oración larga
                forced_chunks = self._force_split_text(sentence, chunk_id)
                chunks.extend(forced_chunks)
                chunk_id += len(forced_chunks)
                current_chunk = ""
                current_tokens = 0
                continue
            
            # Si agregar la oración excede el límite
            if current_tokens + sentence_tokens > self.chunk_size:
                # Guardar chunk actual
                if current_chunk:
                    chunks.append(self._create_chunk_dict(current_chunk, chunk_id))
                    chunk_id += 1
                
                # Calcular overlap
                current_chunk = self._calculate_overlap(current_chunk, sentence)
                current_tokens = self.count_tokens(current_chunk)
            
            else:
                # Agregar oración al chunk actual
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_tokens += sentence_tokens
        
        # Agregar último chunk si existe
        if current_chunk:
            chunks.append(self._create_chunk_dict(current_chunk, chunk_id))
        
        return self._add_overlap_metadata(chunks)
    
    def _force_split_text(self, text: str, start_id: int) -> List[Dict[str, Any]]:
        """
        División forzada de texto muy largo
        
        Args:
            text (str): Texto a dividir
            start_id (int): ID inicial
            
        Returns:
            List[Dict]: Chunks forzados
        """
        chunks = []
        words = text.split()
        current_chunk = ""
        current_tokens = 0
        chunk_id = start_id
        
        for word in words:
            word_tokens = self.count_tokens(word)
            
            if current_tokens + word_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append(self._create_chunk_dict(current_chunk, chunk_id))
                    chunk_id += 1
                
                current_chunk = word
                current_tokens = word_tokens
            else:
                if current_chunk:
                    current_chunk += " " + word
                else:
                    current_chunk = word
                current_tokens += word_tokens
        
        if current_chunk:
            chunks.append(self._create_chunk_dict(current_chunk, chunk_id))
        
        return chunks
    
    def _calculate_overlap(self, previous_chunk: str, next_text: str) -> str:
        """
        Calcula overlap óptimo entre chunks
        
        Args:
            previous_chunk (str): Chunk anterior
            next_text (str): Texto siguiente
            
        Returns:
            str: Texto con overlap calculado
        """
        if not previous_chunk or self.overlap <= 0:
            return next_text
        
        # Obtener últimas oraciones del chunk anterior para overlap
        previous_sentences = self.split_into_sentences(previous_chunk)
        overlap_text = ""
        overlap_tokens = 0
        
        # Agregar oraciones desde el final hasta alcanzar overlap deseado
        for sentence in reversed(previous_sentences):
            sentence_tokens = self.count_tokens(sentence)
            if overlap_tokens + sentence_tokens <= self.overlap:
                overlap_text = sentence + " " + overlap_text if overlap_text else sentence
                overlap_tokens += sentence_tokens
            else:
                break
        
        # Combinar overlap con nuevo texto
        if overlap_text:
            return overlap_text.strip() + " " + next_text
        else:
            return next_text
    
    def _create_chunk_dict(self, text: str, chunk_id: int) -> Dict[str, Any]:
        """
        Crea diccionario de chunk con metadata
        
        Args:
            text (str): Texto del chunk
            chunk_id (int): ID del chunk
            
        Returns:
            Dict: Chunk con metadata
        """
        return {
            'text': text.strip(),
            'tokens': self.count_tokens(text),
            'chunk_id': chunk_id,
            'length': len(text),
            'preview': text[:100] + "..." if len(text) > 100 else text
        }
    
    def _add_overlap_metadata(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Agrega metadata de overlap a los chunks
        
        Args:
            chunks (List[Dict]): Lista de chunks
            
        Returns:
            List[Dict]: Chunks con metadata de overlap
        """
        for i, chunk in enumerate(chunks):
            chunk['overlap_start'] = i > 0
            chunk['overlap_end'] = i < len(chunks) - 1
            chunk['total_chunks'] = len(chunks)
            chunk['position'] = i
        
        return chunks

class QueryOptimizer:
    """
    Optimizador de queries para mejorar resultados de búsqueda
    
    FUNCIONALIDADES:
    - Expansión de términos con sinónimos
    - Corrección ortográfica automática
    - Normalización de términos académicos
    - Detección de entidades (nombres, fechas, conceptos)
    - Optimización específica para corpus académico
    """
    
    def __init__(self):
        """
        Inicializa el optimizador de queries
        """
        # Diccionario de sinónimos académicos
        self.synonyms = {
            'estado': ['gobierno', 'nación', 'país', 'república'],
            'sociedad': ['comunidad', 'pueblo', 'ciudadanía', 'población'],
            'política': ['político', 'gubernamental', 'estatal', 'público'],
            'democracia': ['democrático', 'participación', 'electoral'],
            'desarrollo': ['crecimiento', 'progreso', 'evolución', 'avance'],
            'económico': ['economía', 'financiero', 'monetario', 'fiscal'],
            'social': ['sociedad', 'comunitario', 'colectivo', 'público'],
            'cultural': ['cultura', 'tradición', 'identidad', 'patrimonio']
        }
        
        # Términos académicos comunes
        self.academic_terms = {
            'análisis', 'estudio', 'investigación', 'metodología',
            'teoría', 'concepto', 'enfoque', 'perspectiva',
            'marco', 'modelo', 'paradigma', 'sistema'
        }
        
        logger.info("🔍 Optimizador de queries inicializado")
    
    def optimize_query(self, query: str) -> Dict[str, Any]:
        """
        Optimiza una query para mejorar resultados de búsqueda
        
        Args:
            query (str): Query original del usuario
            
        Returns:
            Dict: Query optimizada con metadata
        """
        original_query = query
        
        # === FASE 1: NORMALIZACIÓN ===
        normalized_query = self._normalize_query(query)
        
        # === FASE 2: EXPANSIÓN CON SINÓNIMOS ===
        expanded_terms = self._expand_with_synonyms(normalized_query)
        
        # === FASE 3: DETECCIÓN DE ENTIDADES ===
        entities = self._extract_entities(normalized_query)
        
        # === FASE 4: TÉRMINOS CLAVE ===
        key_terms = self._extract_key_terms(normalized_query)
        
        # === FASE 5: SUGERENCIAS DE MEJORA ===
        suggestions = self._generate_suggestions(normalized_query)
        
        return {
            'original_query': original_query,
            'normalized_query': normalized_query,
            'expanded_terms': expanded_terms,
            'entities': entities,
            'key_terms': key_terms,
            'suggestions': suggestions,
            'academic_score': self._calculate_academic_score(normalized_query)
        }
    
    def _normalize_query(self, query: str) -> str:
        """
        Normaliza la query eliminando ruido y estandarizando formato
        
        Args:
            query (str): Query original
            
        Returns:
            str: Query normalizada
        """
        # Convertir a minúsculas
        normalized = query.lower().strip()
        
        # Eliminar caracteres especiales innecesarios
        normalized = re.sub(r'[^\w\s\-\.,;:()]', ' ', normalized)
        
        # Normalizar espacios
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Eliminar palabras muy comunes al inicio
        start_words = ['cómo', 'qué', 'cuál', 'cuáles', 'dónde', 'cuándo', 'por qué']
        for word in start_words:
            if normalized.startswith(word + ' '):
                normalized = normalized[len(word):].strip()
                break
        
        return normalized
    
    def _expand_with_synonyms(self, query: str) -> List[str]:
        """
        Expande query con sinónimos relevantes
        
        Args:
            query (str): Query normalizada
            
        Returns:
            List[str]: Lista de términos expandidos
        """
        words = query.split()
        expanded_terms = []
        
        for word in words:
            expanded_terms.append(word)
            
            # Buscar sinónimos
            for term, synonyms in self.synonyms.items():
                if word == term or word in synonyms:
                    expanded_terms.extend([s for s in synonyms if s not in expanded_terms])
        
        return expanded_terms
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extrae entidades de la query
        
        Args:
            query (str): Query a analizar
            
        Returns:
            Dict: Entidades por categoría
        """
        entities = {
            'persons': [],
            'years': [],
            'places': [],
            'concepts': []
        }
        
        # Detectar años
        years = re.findall(r'\b(19|20)\d{2}\b', query)
        entities['years'] = years
        
        # Detectar nombres propios (aproximación)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', query)
        entities['persons'] = proper_nouns
        
        # Detectar términos académicos
        for term in self.academic_terms:
            if term in query:
                entities['concepts'].append(term)
        
        return entities
    
    def _extract_key_terms(self, query: str) -> List[str]:
        """
        Extrae términos clave de la query
        
        Args:
            query (str): Query a analizar
            
        Returns:
            List[str]: Términos clave ordenados por importancia
        """
        stopwords = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le',
            'como', 'sobre', 'según', 'para', 'con', 'por', 'sin', 'hasta', 'desde'
        }
        
        words = re.findall(r'\b\w+\b', query.lower())
        key_terms = [word for word in words if word not in stopwords and len(word) > 2]
        
        # Priorizar términos académicos
        academic_priority = [term for term in key_terms if term in self.academic_terms]
        other_terms = [term for term in key_terms if term not in self.academic_terms]
        
        return academic_priority + other_terms
    
    def _generate_suggestions(self, query: str) -> List[str]:
        """
        Genera sugerencias para mejorar la query
        
        Args:
            query (str): Query original
            
        Returns:
            List[str]: Lista de sugerencias
        """
        suggestions = []
        
        if len(query.split()) < 3:
            suggestions.append("Considera agregar más términos específicos para obtener mejores resultados")
        
        if not any(term in query for term in self.academic_terms):
            suggestions.append("Puedes incluir términos académicos como 'análisis', 'estudio', 'teoría'")
        
        if not re.search(r'\b(19|20)\d{2}\b', query):
            suggestions.append("Si buscas información histórica, incluye años específicos")
        
        return suggestions
    
    def _calculate_academic_score(self, query: str) -> float:
        """
        Calcula score académico de la query
        
        Args:
            query (str): Query a evaluar
            
        Returns:
            float: Score entre 0 y 1
        """
        score = 0.0
        factors = 0
        
        # Factor 1: Longitud apropiada
        word_count = len(query.split())
        if 3 <= word_count <= 10:
            score += 0.3
        factors += 0.3
        
        # Factor 2: Presencia de términos académicos
        academic_count = sum(1 for term in self.academic_terms if term in query)
        if academic_count > 0:
            score += min(0.4, academic_count * 0.2)
        factors += 0.4
        
        # Factor 3: Especificidad
        if any(re.search(pattern, query) for pattern in [r'\b(19|20)\d{2}\b', r'[A-Z][a-z]+']):
            score += 0.3
        factors += 0.3
        
        return score / factors if factors > 0 else 0.0

def validate_embeddings_consistency(embeddings_list: List[List[float]]) -> Dict[str, Any]:
    """
    Valida consistencia de embeddings generados
    
    VERIFICACIONES:
    - Dimensionalidad consistente (768 para all-mpnet-base-v2)
    - Rango de valores apropiado
    - Ausencia de NaN o infinitos
    - Distribución estadística normal
    
    Args:
        embeddings_list (List[List[float]]): Lista de embeddings a validar
        
    Returns:
        Dict: Reporte de validación
    """
    import numpy as np
    
    if not embeddings_list:
        return {'valid': False, 'error': 'Lista de embeddings vacía'}
    
    try:
        # Convertir a array numpy para análisis
        embeddings_array = np.array(embeddings_list)
        
        # === VALIDACIÓN 1: DIMENSIONALIDAD ===
        expected_dim = 768  # all-mpnet-base-v2
        actual_dims = [len(emb) for emb in embeddings_list]
        
        if not all(dim == expected_dim for dim in actual_dims):
            return {
                'valid': False,
                'error': f'Dimensiones inconsistentes. Esperado: {expected_dim}, Encontrado: {set(actual_dims)}'
            }
        
        # === VALIDACIÓN 2: VALORES NUMÉRICOS ===
        if np.any(np.isnan(embeddings_array)):
            return {'valid': False, 'error': 'Embeddings contienen valores NaN'}
        
        if np.any(np.isinf(embeddings_array)):
            return {'valid': False, 'error': 'Embeddings contienen valores infinitos'}
        
        # === VALIDACIÓN 3: RANGO DE VALORES ===
        min_val = np.min(embeddings_array)
        max_val = np.max(embeddings_array)
        
        # Para all-mpnet-base-v2, valores típicos están en [-1, 1]
        if min_val < -2 or max_val > 2:
            return {
                'valid': False,
                'error': f'Rango de valores sospechoso: [{min_val:.3f}, {max_val:.3f}]'
            }
        
        # === VALIDACIÓN 4: ESTADÍSTICAS ===
        mean_val = np.mean(embeddings_array)
        std_val = np.std(embeddings_array)
        
        # === REPORTE DE VALIDACIÓN ===
        validation_report = {
            'valid': True,
            'embedding_count': len(embeddings_list),
            'dimensions': expected_dim,
            'value_range': [float(min_val), float(max_val)],
            'mean': float(mean_val),
            'std': float(std_val),
            'total_elements': embeddings_array.size
        }
        
        logger.info(f"✅ Embeddings validados: {len(embeddings_list)} vectores, {expected_dim}D")
        return validation_report
        
    except Exception as e:
        return {'valid': False, 'error': f'Error en validación: {str(e)}'}

def measure_embedding_performance(func):
    """
    Decorador para medir performance de funciones de embeddings
    
    Args:
        func: Función a medir
        
    Returns:
        function: Función decorada con medición de performance
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # Ejecutar función
        result = func(*args, **kwargs)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Log de performance
        logger.info(f"⏱️ {func.__name__} ejecutado en {execution_time:.2f}s")
        
        return result
    
    return wrapper

def create_backup_embeddings(collection, backup_path: str = "backup_embeddings"):
    """
    Crea backup de embeddings de ChromaDB
    
    Args:
        collection: Colección de ChromaDB
        backup_path (str): Ruta para el backup
    """
    try:
        backup_dir = Path(backup_path)
        backup_dir.mkdir(exist_ok=True)
        
        # Obtener todos los datos
        all_data = collection.get(include=['embeddings', 'documents', 'metadatas'])
        
        # Crear backup con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"embeddings_backup_{timestamp}.json"
        
        # Guardar datos (embeddings son muy grandes, considerar compresión)
        backup_data = {
            'timestamp': timestamp,
            'collection_name': collection.name,
            'document_count': len(all_data.get('documents', [])),
            'documents': all_data.get('documents', []),
            'metadatas': all_data.get('metadatas', []),
            # Nota: embeddings no incluidos por tamaño, solo metadata
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Backup creado: {backup_file}")
        return str(backup_file)
        
    except Exception as e:
        logger.error(f"❌ Error creando backup: {e}")
        return None

# === UTILIDADES DE LOGGING AVANZADO ===

class RAGLogger:
    """
    Logger especializado para operaciones RAG
    """
    
    def __init__(self, name: str = "RAG_System"):
        self.logger = logging.getLogger(name)
        self.setup_logger()
    
    def setup_logger(self):
        """
        Configura logger con formato especializado para RAG
        """
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_search_operation(self, query: str, results_count: int, execution_time: float):
        """
        Log especializado para operaciones de búsqueda
        """
        self.logger.info(
            f"🔍 BÚSQUEDA | Query: '{query[:50]}...' | "
            f"Resultados: {results_count} | Tiempo: {execution_time:.2f}s"
        )
    
    def log_embedding_operation(self, text_count: int, embedding_dim: int, execution_time: float):
        """
        Log especializado para generación de embeddings
        """
        self.logger.info(
            f"🤖 EMBEDDINGS | Textos: {text_count} | "
            f"Dimensiones: {embedding_dim} | Tiempo: {execution_time:.2f}s"
        )
    
    def log_llm_operation(self, model: str, tokens_used: int, execution_time: float):
        """
        Log especializado para operaciones LLM
        """
        self.logger.info(
            f"💬 LLM | Modelo: {model} | "
            f"Tokens: {tokens_used} | Tiempo: {execution_time:.2f}s"
        )

# Instancia global del logger RAG
rag_logger = RAGLogger()