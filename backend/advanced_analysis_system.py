"""
Sistema de Análisis Avanzado con múltiples proveedores LLM
Soporta Ollama (local), OpenAI, y otros proveedores
"""

import logging
import re
import json
import requests
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class AdvancedAnalysisSystem:
    """Sistema de análisis avanzado con múltiples proveedores LLM"""
    
    def __init__(self):
        self.is_loaded = False
        self.model_name = "Análisis Avanzado Multi-LLM"
        self.provider = None
        self.fallback_system = None
        
        # Configuración de proveedores
        self.providers = {
            'ollama': {
                'url': 'http://localhost:11434',
                'model': 'llama3.1:8b',
                'available': False
            },
            'openai': {
                'url': 'https://api.openai.com/v1',
                'model': 'gpt-3.5-turbo',
                'api_key': os.getenv('OPENAI_API_KEY'),
                'available': False
            },
            'groq': {
                'url': 'https://api.groq.com/openai/v1',
                'model': 'llama-3.3-70b-versatile',
                'api_key': os.getenv('GROQ_API_KEY'),
                'available': False
            }
        }
        
    def initialize(self):
        """Inicializar el sistema detectando proveedores disponibles"""
        print("🧠 Inicializando Sistema de Análisis Avanzado...")
        
        # Probar proveedores en orden de preferencia
        for provider_name in ['ollama', 'groq', 'openai']:
            if self._test_provider(provider_name):
                self.provider = provider_name
                print(f"✅ Usando proveedor: {provider_name.upper()}")
                self.is_loaded = True
                return True
        
        # Fallback al sistema local
        print("⚠️  Ningún proveedor LLM disponible - Usando análisis local mejorado")
        try:
            from intelligent_analysis_system import IntelligentAnalysisSystem
            self.fallback_system = IntelligentAnalysisSystem()
            self.fallback_system.initialize()
            self.is_loaded = True
            self.provider = 'local'
            return True
        except Exception as e:
            print(f"❌ Error inicializando sistema local: {e}")
            self.is_loaded = False
            return False
    
    def _test_provider(self, provider_name: str) -> bool:
        """Probar si un proveedor está disponible"""
        
        provider = self.providers.get(provider_name)
        if not provider:
            return False
        
        try:
            if provider_name == 'ollama':
                # Probar Ollama
                response = requests.get(f"{provider['url']}/api/tags", timeout=3)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    if models:
                        # Usar el primer modelo disponible
                        provider['model'] = models[0]['name']
                        provider['available'] = True
                        return True
                        
            elif provider_name in ['openai', 'groq']:
                # Probar proveedores con API key
                api_key = provider['api_key']
                if not api_key:
                    return False
                
                # Test simple
                headers = {'Authorization': f'Bearer {api_key}'}
                response = requests.get(f"{provider['url']}/models", headers=headers, timeout=5)
                if response.status_code == 200:
                    provider['available'] = True
                    return True
                    
        except Exception as e:
            logger.debug(f"Proveedor {provider_name} no disponible: {e}")
        
        return False
    
    def generate_response_with_context(self, question: str, context_chunks: List[str]) -> str:
        """Generar respuesta usando el proveedor disponible"""
        
        try:
            print(f"🧠 Análisis avanzado con {self.provider.upper()}...")
            print(f"📄 Procesando {len(context_chunks)} fragmentos de contexto")
            
            if self.provider == 'local':
                return self.fallback_system.generate_response_with_context(question, context_chunks)
            else:
                return self._generate_llm_response(question, context_chunks)
                
        except Exception as e:
            logger.error(f"Error en análisis avanzado: {e}")
            return self._generate_emergency_response(question, context_chunks)
    
    def _generate_llm_response(self, question: str, context_chunks: List[str]) -> str:
        """Generar respuesta usando LLM real"""
        
        # Preparar contexto
        combined_context = self._prepare_context_for_llm(context_chunks)
        
        # Crear prompt especializado
        system_prompt = self._create_analysis_prompt()
        user_prompt = self._create_user_prompt(question, combined_context)
        
        try:
            if self.provider == 'ollama':
                return self._call_ollama(system_prompt, user_prompt)
            elif self.provider in ['openai', 'groq']:
                return self._call_openai_compatible(system_prompt, user_prompt)
            else:
                raise Exception(f"Proveedor no soportado: {self.provider}")
                
        except Exception as e:
            logger.error(f"Error llamando a {self.provider}: {e}")
            # Fallback
            if self.fallback_system:
                return self.fallback_system.generate_response_with_context(question, context_chunks)
            return "Error procesando la consulta con LLM."
    
    def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Llamar a Ollama"""
        
        provider = self.providers['ollama']
        
        response = requests.post(
            f"{provider['url']}/api/generate",
            json={
                "model": provider['model'],
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 800
                }
            },
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            llm_response = result.get('response', '').strip()
            return self._post_process_response(llm_response)
        else:
            raise Exception(f"Error Ollama: {response.status_code}")
    
    def _call_openai_compatible(self, system_prompt: str, user_prompt: str) -> str:
        """Llamar a APIs compatibles con OpenAI (OpenAI, Groq)"""
        
        provider = self.providers[self.provider]
        
        headers = {
            'Authorization': f'Bearer {provider["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "model": provider['model'],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 800
        }
        
        response = requests.post(
            f"{provider['url']}/chat/completions",
            headers=headers,
            json=data,
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            llm_response = result['choices'][0]['message']['content'].strip()
            return self._post_process_response(llm_response)
        else:
            raise Exception(f"Error {self.provider}: {response.status_code} - {response.text}")
    
    def _prepare_context_for_llm(self, context_chunks: List[str]) -> str:
        """Preparar contexto optimizado para LLM"""
        
        combined = ' '.join(context_chunks)
        
        # Limpiar caracteres problemáticos
        combined = re.sub(r'[^\w\sáéíóúñüÁÉÍÓÚÑÜ.,;:()\-"\'¿?¡!]', ' ', combined)
        combined = re.sub(r'\s+', ' ', combined).strip()
        
        # Limitar longitud (para tokens)
        if len(combined) > 8000:
            sentences = re.split(r'[.!?]+', combined)
            important_sentences = sentences[:25]
            combined = '. '.join(important_sentences) + '.'
        
        return combined
    
    def _create_analysis_prompt(self) -> str:
        """Crear prompt del sistema"""
        
        return """Eres un experto analista de documentos académicos sobre Perú, especializado en sociedad, política, cultura e historia peruana.

INSTRUCCIONES CRÍTICAS:
1. Analiza ÚNICAMENTE la información presente en los documentos proporcionados
2. Responde ESPECÍFICAMENTE lo que se pregunta, no temas generales
3. Sé PRECISO y DIRECTO - evita ambigüedades
4. NO inventes información que no esté en los documentos
5. Si preguntan sobre racismo, responde sobre racismo. Si preguntan sobre política, responde sobre política.

FORMATO DE RESPUESTA:
- Respuesta directa a la pregunta específica
- 3-5 puntos clave numerados con evidencia de los documentos
- Síntesis concreta final

EVITA: Respuestas genéricas, información no relacionada, ambigüedades."""
    
    def _create_user_prompt(self, question: str, context: str) -> str:
        """Crear prompt del usuario"""
        
        return f"""PREGUNTA ESPECÍFICA: {question}

DOCUMENTOS PARA ANÁLISIS:
{context}

INSTRUCCIONES:
- Responde EXACTAMENTE lo que se pregunta
- Usa ÚNICAMENTE información de los documentos
- Sé específico y directo
- Proporciona evidencia concreta
- Máximo 5 puntos numerados
- Síntesis final en 1 oración"""
    
    def _post_process_response(self, llm_response: str) -> str:
        """Post-procesar respuesta del LLM"""
        
        response = llm_response.strip()
        
        # Remover prefijos comunes
        prefixes = [
            "Respuesta:", "Análisis:", "Basándome en los documentos:",
            "De acuerdo con los documentos:", "Según el análisis:"
        ]
        
        for prefix in prefixes:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        # Limitar longitud si es muy larga
        if len(response) > 1000:
            sentences = re.split(r'[.!?]+', response)
            response = '. '.join(sentences[:6]) + '.'
        
        return response
    
    def _generate_emergency_response(self, question: str, context_chunks: List[str]) -> str:
        """Respuesta de emergencia"""
        
        if not context_chunks:
            return "No se encontró información relevante para responder a esta consulta específica."
        
        best_chunk = max(context_chunks, key=len)
        clean_chunk = re.sub(r'[^\w\sáéíóúñüÁÉÍÓÚÑÜ.,;:()\-"]', ' ', best_chunk)
        clean_chunk = re.sub(r'\s+', ' ', clean_chunk).strip()
        
        if len(clean_chunk) > 400:
            clean_chunk = clean_chunk[:400] + "..."
        
        return f"Información relevante encontrada en los documentos:\n\n{clean_chunk}\n\nEsta información puede ayudar a responder su consulta específica."

# Función de compatibilidad
def create_advanced_analysis_system():
    """Crear sistema de análisis avanzado"""
    system = AdvancedAnalysisSystem()
    system.initialize()
    return system