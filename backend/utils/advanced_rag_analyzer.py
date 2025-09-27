"""
Sistema Avanzado de Análisis RAG
Integra modelos LLM potentes para análisis inteligente de documentos
Soporte multi-provider: Groq, Together AI, Gemini, OpenAI
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AnalysisConfig:
    """Configuración del sistema de análisis"""
    primary_provider: str = os.getenv("PRIMARY_LLM_PROVIDER", "groq")
    fallback_providers: List[str] = None
    max_context_length: int = int(os.getenv("MAX_CONTEXT_LENGTH", "4000"))
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "800"))

class AdvancedRAGAnalyzer:
    """Sistema avanzado de análisis RAG con múltiples proveedores LLM"""
    
    def __init__(self, config: AnalysisConfig = None):
        self.config = config or AnalysisConfig()
        self.config.fallback_providers = self.config.fallback_providers or ["together", "gemini", "openai"]
        self.providers = self._initialize_providers()
    
    def _initialize_providers(self) -> Dict[str, Any]:
        """Inicializa todos los proveedores disponibles"""
        providers = {}
        
        # GROQ - Llama 3.3 70B (MUY POTENTE Y RÁPIDO)
        if self._has_api_key("GROQ_API_KEY"):
            try:
                import groq
                providers["groq"] = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
                logger.info("✅ Groq provider initialized (Llama 3.3 70B)")
            except ImportError:
                logger.warning("❌ Groq library not available. Install: pip install groq")
        
        # TOGETHER AI - DeepSeek V3, Qwen2.5
        if self._has_api_key("TOGETHER_API_KEY"):
            try:
                import together
                together.api_key = os.getenv("TOGETHER_API_KEY")
                providers["together"] = together
                logger.info("✅ Together AI provider initialized")
            except ImportError:
                logger.warning("❌ Together library not available. Install: pip install together")
        
        # GOOGLE GEMINI - Análisis superior de contexto
        if self._has_api_key("GEMINI_API_KEY"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                providers["gemini"] = genai.GenerativeModel('gemini-1.5-pro')
                logger.info("✅ Gemini provider initialized")
            except ImportError:
                logger.warning("❌ Google AI library not available. Install: pip install google-generativeai")
        
        # OPENAI - Backup confiable
        if self._has_api_key("OPENAI_API_KEY"):
            try:
                import openai
                providers["openai"] = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                logger.info("✅ OpenAI provider initialized")
            except ImportError:
                logger.warning("❌ OpenAI library not available. Install: pip install openai")
        
        if not providers:
            logger.error("❌ No LLM providers available. Check API keys.")
        
        return providers
    
    def _has_api_key(self, key_name: str) -> bool:
        """Verifica si existe la API key"""
        return bool(os.getenv(key_name))
    
    def generate_advanced_response(self, query: str, context_chunks: List[str]) -> str:
        """
        Genera respuesta avanzada usando el mejor modelo disponible
        """
        # Preparar contexto optimizado
        context = self._prepare_context(context_chunks)
        
        # Crear prompt sofisticado para análisis profundo
        prompt = self._create_analysis_prompt(query, context)
        
        # Intentar con proveedor principal
        response = self._try_provider(self.config.primary_provider, prompt)
        if response:
            return self._clean_response(response)
        
        # Fallback a otros proveedores
        for provider in self.config.fallback_providers:
            response = self._try_provider(provider, prompt)
            if response:
                logger.info(f"Respuesta generada con fallback: {provider}")
                return self._clean_response(response)
        
        # Si todos fallan, respuesta estructurada básica
        return self._generate_structured_fallback(query, context_chunks)
    
    def _prepare_context(self, chunks: List[str]) -> str:
        """Prepara el contexto optimizando para el límite de tokens"""
        # Limpiar y concatenar chunks
        clean_chunks = []
        total_length = 0
        
        for chunk in chunks:
            clean_chunk = chunk.strip().replace('\n\n', '\n')
            if total_length + len(clean_chunk) > self.config.max_context_length:
                break
            clean_chunks.append(clean_chunk)
            total_length += len(clean_chunk)
        
        return '\n\n---\n\n'.join(clean_chunks)
    
    def _create_analysis_prompt(self, query: str, context: str) -> str:
        """Crea un prompt sofisticado para análisis profundo y respuestas extensas"""
        return f"""Eres un experto analista especializado en ciencias sociales, política y cultura peruana. Tu tarea es generar análisis profundos, extensos y academicamente rigurosos basados en documentos especializados.

INSTRUCCIONES CRÍTICAS:
1. Analiza EXHAUSTIVAMENTE toda la información presente en los documentos
2. NO inventes información - usa ÚNICAMENTE el contenido proporcionado
3. Genera respuestas EXTENSAS (mínimo 300 palabras) con análisis profundo
4. Estructura tu respuesta de manera académica y profesional
5. Incluye citas específicas de los documentos cuando sea relevante
6. Si hay múltiples perspectivas, analízalas todas detalladamente
7. Contextualiza todo en el marco histórico y social peruano

PREGUNTA: {query}

DOCUMENTOS PARA ANÁLISIS:
{context}

FORMATO DE RESPUESTA REQUERIDO:
Genera un análisis académico estructurado y extenso que incluya:

**Análisis Principal:**
[Respuesta principal de al menos 200 palabras que responda directamente a la pregunta basándose en los documentos]

**Evidencias y Citas Específicas:**
[Referencias directas de los textos con análisis de su significado - mínimo 3-4 evidencias]

**Perspectivas y Matices:**
[Diferentes enfoques o interpretaciones encontradas en los documentos]

**Contextualización Histórica y Social:**
[Situación del tema en el contexto específico peruano con profundidad histórica]

**Síntesis y Conclusiones:**
[Conclusiones analíticas que integren toda la información presentada]

IMPORTANTE: Tu respuesta debe ser sustancial, académicamente rigurosa y basada completamente en el contenido de los documentos. Desarrolla cada punto con profundidad y detalle.

Respuesta:"""
    
    def _try_provider(self, provider_name: str, prompt: str) -> Optional[str]:
        """Intenta generar respuesta con un proveedor específico"""
        if provider_name not in self.providers:
            return None
        
        try:
            if provider_name == "groq":
                return self._call_groq(prompt)
            elif provider_name == "together":
                return self._call_together(prompt)
            elif provider_name == "gemini":
                return self._call_gemini(prompt)
            elif provider_name == "openai":
                return self._call_openai(prompt)
        except Exception as e:
            logger.error(f"Error with {provider_name}: {str(e)}")
        
        return None
    
    def _call_groq(self, prompt: str) -> str:
        """Llamada a Groq API (Llama 3.3 70B)"""
        response = self.providers["groq"].chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",  # Modelo más potente
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content
    
    def _call_together(self, prompt: str) -> str:
        """Llamada a Together AI (DeepSeek V3)"""
        response = self.providers["together"].Complete.create(
            prompt=prompt,
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",  # Modelo potente
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response['output']['choices'][0]['text']
    
    def _call_gemini(self, prompt: str) -> str:
        """Llamada a Gemini API"""
        response = self.providers["gemini"].generate_content(
            prompt,
            generation_config={
                'temperature': self.config.temperature,
                'max_output_tokens': self.config.max_tokens,
            }
        )
        return response.text
    
    def _call_openai(self, prompt: str) -> str:
        """Llamada a OpenAI API (Backup)"""
        response = self.providers["openai"].chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-4o",  # Modelo más potente de OpenAI
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content
    
    def _clean_response(self, response: str) -> str:
        """Limpia y formatea la respuesta final"""
        # Remover posibles artefactos del prompt
        cleaned = response.strip()
        
        # Remover patrones comunes de modelos
        patterns_to_remove = [
            r"^Respuesta:?\s*",
            r"^Análisis:?\s*",
            r"^Basándome en los documentos:?\s*",
        ]
        
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    def _generate_structured_fallback(self, query: str, chunks: List[str]) -> str:
        """Fallback estructurado si todos los LLM fallan"""
        context_text = ' '.join(chunks[:2])  # Usar solo primeros 2 chunks
        
        # Análisis básico de palabras clave
        query_words = set(query.lower().split())
        relevant_sentences = []
        
        import re
        sentences = re.split(r'[.!?]+', context_text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 50:  # Solo oraciones sustanciales
                sentence_words = set(sentence.lower().split())
                # Calcular overlap
                overlap = len(query_words.intersection(sentence_words))
                if overlap > 0:
                    relevant_sentences.append((sentence, overlap))
        
        # Ordenar por relevancia
        relevant_sentences.sort(key=lambda x: x[1], reverse=True)
        
        if relevant_sentences:
            response = f"**Análisis basado en los documentos:**\n\n"
            
            for i, (sentence, _) in enumerate(relevant_sentences[:3], 1):
                clean_sentence = sentence.replace('\n', ' ').strip()
                response += f"{i}. {clean_sentence}.\n\n"
            
            response += "**Nota:** Esta respuesta se basa directamente en el contenido de los documentos analizados."
            return response
        
        return f"Los documentos contienen información relacionada con '{query}', pero se requiere un análisis más específico para generar una respuesta detallada."

# Instancia global del analizador
_analyzer = None

def get_analyzer() -> AdvancedRAGAnalyzer:
    """Obtiene instancia global del analizador"""
    global _analyzer
    if _analyzer is None:
        _analyzer = AdvancedRAGAnalyzer()
    return _analyzer

def generate_intelligent_response(query: str, context_chunks: List[str]) -> str:
    """
    Función principal para generar respuestas inteligentes
    """
    analyzer = get_analyzer()
    return analyzer.generate_advanced_response(query, context_chunks)