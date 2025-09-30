"""
SISTEMA RAG OPTIMIZADO - VERSIÓN MEJORADA
=========================================

Mejoras implementadas:
1. Cache inteligente de embeddings y resultados
2. Procesamiento asíncrono y paralelo
3. Reranking avanzado con múltiples estrategias
4. Fusión de resultados de múltiples búsquedas
5. Filtrado dinámico por relevancia
6. Optimización de memoria y rendimiento
7. Sistema de scoring híbrido (semántico + léxico)
"""

import os
import sys
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import pickle
from functools import lru_cache
import threading

# Imports especializados con manejo de errores
try:
    import numpy as np
except ImportError:
    print("❌ NumPy no disponible. Instalar con: pip install numpy")
    raise

try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
except ImportError:
    print("❌ SentenceTransformers no disponible. Instalar con: pip install sentence-transformers")
    raise

try:
    import chromadb
except ImportError:
    print("❌ ChromaDB no disponible. Instalar con: pip install chromadb")
    raise

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    print("⚠️ rank-bm25 no disponible. Funciones BM25 deshabilitadas. Instalar con: pip install rank-bm25")
    BM25Okapi = None
    HAS_BM25 = False

import re
from collections import defaultdict

# Configuración de logging optimizada
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedRAGSystem:
    """Sistema RAG optimizado con múltiples mejoras de rendimiento"""
    
    def __init__(self, chroma_path: str = None):
        self.chroma_path = chroma_path or str(Path(__file__).parent.parent.parent / "chroma_db_simple")
        
        # Modelos optimizados
        self.embedding_model = None
        self.reranker = None
        self.cross_encoder = None
        
        # Cache optimizado
        self.embedding_cache = {}
        self.results_cache = {}
        self.cache_max_size = 1000
        self.cache_ttl = 3600  # 1 hora
        
        # Cliente ChromaDB
        self.client = None
        self.collection = None
        
        # Índices BM25 para búsqueda híbrida
        self.bm25_index = None
        self.documents_texts = []
        self.documents_metadata = []
        
        # Pool de threads para paralelización
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Lock para thread safety
        self._lock = threading.Lock()
        
        # Inicialización lazy
        self._initialized = False
    
    def _initialize_models(self):
        """Inicialización lazy de modelos para mejor rendimiento"""
        if self._initialized:
            return
            
        logger.info("🚀 Inicializando sistema RAG optimizado...")
        
        # Modelo de embeddings principal (mejorado)
        self.embedding_model = SentenceTransformer(
            'sentence-transformers/all-mpnet-base-v2',
            device='cpu'  # Optimizar según hardware
        )
        
        # Cross-encoder para reranking fino
        self.cross_encoder = CrossEncoder(
            'cross-encoder/ms-marco-MiniLM-L-2-v2',
            max_length=512
        )
        
        # Cliente ChromaDB optimizado
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        try:
            self.collection = self.client.get_collection("simple_rag_docs")
            logger.info(f"✅ Colección cargada: {self.collection.count()} documentos")
        except Exception as e:
            logger.error(f"❌ Error cargando colección: {e}")
            raise
        
        # Inicializar índice BM25
        self._build_bm25_index()
        
        self._initialized = True
        logger.info("✅ Sistema RAG optimizado inicializado")
    
    def _build_bm25_index(self):
        """Construir índice BM25 para búsqueda híbrida"""
        if not HAS_BM25:
            logger.warning("⚠️ BM25 no disponible - funcionalidad híbrida deshabilitada")
            self.bm25_index = None
            return
            
        logger.info("🔧 Construyendo índice BM25...")
        
        # Obtener todos los documentos
        all_data = self.collection.get(include=['documents', 'metadatas'])
        
        self.documents_texts = all_data['documents']
        self.documents_metadata = all_data['metadatas']
        
        # Tokenizar documentos para BM25
        tokenized_docs = [self._tokenize_text(doc) for doc in self.documents_texts]
        self.bm25_index = BM25Okapi(tokenized_docs)
        
        logger.info(f"✅ Índice BM25 construido con {len(tokenized_docs)} documentos")
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenización optimizada para BM25"""
        # Limpiar y tokenizar
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = text.split()
        # Filtrar tokens muy cortos o muy largos
        return [token for token in tokens if 2 <= len(token) <= 20]
    
    def _get_cache_key(self, query: str, search_type: str = "semantic") -> str:
        """Generar clave única para cache"""
        return hashlib.md5(f"{query}_{search_type}".encode()).hexdigest()
    
    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Verificar si el cache sigue siendo válido"""
        return datetime.now() - timestamp < timedelta(seconds=self.cache_ttl)
    
    @lru_cache(maxsize=500)
    def _get_embedding_cached(self, text: str) -> Tuple[float, ...]:
        """Cache LRU para embeddings computados"""
        embedding = self.embedding_model.encode(text, normalize_embeddings=True)
        return tuple(embedding.tolist())
    
    def semantic_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Búsqueda semántica optimizada con cache"""
        self._initialize_models()  # Asegurar que esté inicializado
        
        cache_key = self._get_cache_key(query, "semantic")
        
        # Verificar cache
        if cache_key in self.results_cache:
            cached_result, timestamp = self.results_cache[cache_key]
            if self._is_cache_valid(timestamp):
                logger.info("📋 Resultado obtenido del cache")
                return cached_result[:top_k]
        
        # Generar embedding con cache
        query_embedding = list(self._get_embedding_cached(query))
        
        # Búsqueda en ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k * 2, 50),  # Obtener más para reranking
            include=['documents', 'metadatas', 'distances']
        )
        
        # Formatear resultados
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
                    'distance': distance,
                    'metadata': meta,
                    'search_type': 'semantic'
                })
        
        # Guardar en cache
        self.results_cache[cache_key] = (formatted_results, datetime.now())
        
        # Limpiar cache si está muy grande
        if len(self.results_cache) > self.cache_max_size:
            oldest_key = min(self.results_cache.keys(), 
                           key=lambda k: self.results_cache[k][1])
            del self.results_cache[oldest_key]
        
        return formatted_results[:top_k]
    
    def bm25_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Búsqueda BM25 (léxica) para complementar búsqueda semántica"""
        self._initialize_models()  # Asegurar que esté inicializado
        
        if not HAS_BM25 or not self.bm25_index:
            logger.warning("⚠️ BM25 no disponible - usando solo búsqueda semántica")
            return []
        
        cache_key = self._get_cache_key(query, "bm25")
        
        # Verificar cache
        if cache_key in self.results_cache:
            cached_result, timestamp = self.results_cache[cache_key]
            if self._is_cache_valid(timestamp):
                return cached_result[:top_k]
        
        # Tokenizar query
        query_tokens = self._tokenize_text(query)
        
        # Obtener scores BM25
        bm25_scores = self.bm25_index.get_scores(query_tokens)
        
        # Ordenar por score
        ranked_indices = np.argsort(bm25_scores)[::-1]
        
        # Formatear resultados
        formatted_results = []
        for i, idx in enumerate(ranked_indices[:top_k]):
            if bm25_scores[idx] > 0:  # Solo incluir resultados con score positivo
                formatted_results.append({
                    'texto': self.documents_texts[idx],
                    'archivo': self.documents_metadata[idx].get('archivo', 'Unknown'),
                    'chunk': self.documents_metadata[idx].get('chunk', 'Unknown'),
                    'similarity_score': round(bm25_scores[idx], 4),
                    'bm25_score': bm25_scores[idx],
                    'metadata': self.documents_metadata[idx],
                    'search_type': 'bm25'
                })
        
        # Guardar en cache
        self.results_cache[cache_key] = (formatted_results, datetime.now())
        
        return formatted_results
    
    def hybrid_search(self, query: str, top_k: int = 10, 
                     semantic_weight: float = 0.7,
                     bm25_weight: float = 0.3) -> List[Dict[str, Any]]:
        """Búsqueda híbrida combinando semántica y BM25"""
        
        # Búsquedas paralelas
        futures = {
            self.executor.submit(self.semantic_search, query, top_k * 2): 'semantic',
            self.executor.submit(self.bm25_search, query, top_k * 2): 'bm25'
        }
        
        semantic_results = []
        bm25_results = []
        
        for future in as_completed(futures):
            search_type = futures[future]
            try:
                results = future.result()
                if search_type == 'semantic':
                    semantic_results = results
                else:
                    bm25_results = results
            except Exception as e:
                logger.error(f"Error en búsqueda {search_type}: {e}")
        
        # Fusión de resultados con puntuación híbrida
        combined_results = {}
        
        # Procesar resultados semánticos
        for result in semantic_results:
            key = f"{result['archivo']}_{result['chunk']}"
            combined_results[key] = result.copy()
            combined_results[key]['hybrid_score'] = result['similarity_score'] * semantic_weight
            combined_results[key]['semantic_score'] = result['similarity_score']
        
        # Procesar y combinar resultados BM25
        for result in bm25_results:
            key = f"{result['archivo']}_{result['chunk']}"
            if key in combined_results:
                # Combinar scores
                combined_results[key]['hybrid_score'] += result['similarity_score'] * bm25_weight
                combined_results[key]['bm25_score'] = result['similarity_score']
                combined_results[key]['search_type'] = 'hybrid'
            else:
                # Nuevo resultado solo de BM25
                combined_results[key] = result.copy()
                combined_results[key]['hybrid_score'] = result['similarity_score'] * bm25_weight
                combined_results[key]['bm25_score'] = result['similarity_score']
                combined_results[key]['semantic_score'] = 0.0
        
        # Ordenar por score híbrido
        final_results = sorted(
            combined_results.values(),
            key=lambda x: x['hybrid_score'],
            reverse=True
        )
        
        return final_results[:top_k]
    
    def rerank_with_cross_encoder(self, query: str, 
                                 results: List[Dict[str, Any]], 
                                 top_k: int = 5) -> List[Dict[str, Any]]:
        """Reranking avanzado usando cross-encoder"""
        if not results or not self.cross_encoder:
            return results[:top_k]
        
        # Preparar pares query-documento
        pairs = [(query, result['texto']) for result in results]
        
        # Obtener scores del cross-encoder
        try:
            cross_scores = self.cross_encoder.predict(pairs)
            
            # Actualizar resultados con nuevos scores
            for i, result in enumerate(results):
                result['cross_encoder_score'] = float(cross_scores[i])
                # Score final combinado
                result['final_score'] = (
                    result.get('hybrid_score', result['similarity_score']) * 0.6 +
                    result['cross_encoder_score'] * 0.4
                )
            
            # Reordenar por score final
            reranked = sorted(results, key=lambda x: x['final_score'], reverse=True)
            
            logger.info(f"🔄 Reranking completado: {len(reranked)} resultados")
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f"Error en reranking: {e}")
            return results[:top_k]
    
    def advanced_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Búsqueda avanzada con todas las optimizaciones"""
        self._initialize_models()
        
        logger.info(f"🔍 Búsqueda avanzada: '{query}'")
        start_time = datetime.now()
        
        # 1. Búsqueda híbrida inicial
        hybrid_results = self.hybrid_search(query, top_k * 3)
        
        # 2. Filtrado por relevancia mínima
        min_threshold = 0.1
        filtered_results = [
            r for r in hybrid_results 
            if r.get('hybrid_score', r['similarity_score']) > min_threshold
        ]
        
        # 3. Reranking con cross-encoder
        final_results = self.rerank_with_cross_encoder(
            query, filtered_results, top_k
        )
        
        # 4. Enriquecimiento de metadatos
        for result in final_results:
            result['query'] = query
            result['timestamp'] = datetime.now().isoformat()
            result['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Búsqueda completada en {processing_time:.3f}s")
        
        return final_results
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema"""
        self._initialize_models()
        
        return {
            'collection_count': self.collection.count() if self.collection else 0,
            'cache_size': len(self.results_cache),
            'embedding_cache_size': len(self.embedding_cache),
            'bm25_docs': len(self.documents_texts),
            'models_loaded': {
                'embedding_model': self.embedding_model is not None,
                'cross_encoder': self.cross_encoder is not None,
                'bm25_index': self.bm25_index is not None
            }
        }
    
    def clear_cache(self):
        """Limpiar todos los caches"""
        with self._lock:
            self.results_cache.clear()
            self.embedding_cache.clear()
            self._get_embedding_cached.cache_clear()
        logger.info("🧹 Cache limpiado")

# Instancia global optimizada
_optimized_rag = None

def get_optimized_rag() -> OptimizedRAGSystem:
    """Obtener instancia singleton del sistema RAG optimizado"""
    global _optimized_rag
    if _optimized_rag is None:
        _optimized_rag = OptimizedRAGSystem()
    return _optimized_rag

def perform_optimized_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Función principal de búsqueda optimizada"""
    rag_system = get_optimized_rag()
    return rag_system.advanced_search(query, top_k)

if __name__ == "__main__":
    # Ejemplo de uso
    rag = OptimizedRAGSystem()
    
    # Pruebas
    test_queries = [
        "variables según Arias",
        "operacionalización de variables", 
        "El corazón de la investigación Según Arias"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = rag.advanced_search(query, 3)
        
        for i, result in enumerate(results):
            print(f"  {i+1}. {result['archivo']}")
            print(f"     Score: {result.get('final_score', result['similarity_score']):.4f}")
            print(f"     Texto: {result['texto'][:100]}...")
    
    # Estadísticas
    stats = rag.get_system_stats()
    print(f"\n📊 Estadísticas del sistema: {stats}")