# 🚀 INSTRUCCIONES ACTUALIZADAS PARA DEEPSEEK V3.1

## ✅ CAMBIOS CRÍTICOS REALIZADOS

### 🔧 **MODELO CORREGIDO**
- **ANTES**: `deepseek/deepseek-v3` ❌ (No existía)
- **AHORA**: `deepseek/deepseek-chat-v3.1` ✅ (Funcionando)

### 📁 **ARCHIVOS ACTUALIZADOS**
1. `backend/utils/rag_utils.py` - Línea 243
2. `backend/rag_system_comentado.py` - Línea 345

---

## 🎯 PASOS PARA TU COMPAÑERO

### 1️⃣ **ACTUALIZAR CÓDIGO**
```bash
# Descargar los archivos actualizados desde el repositorio
git pull origin main
```

### 2️⃣ **VERIFICAR ARCHIVO .env**
Asegúrate de que tenga este archivo: `backend/.env`
```env
# === DEEPSEEK V3 VIA OPENROUTER (PRINCIPAL) ===
OPENROUTER_API_KEY=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

# === SISTEMA RAG OPTIMIZADO ===
USE_OPTIMIZED_RAG=true
USE_ENHANCED_RAG=false
```

### 3️⃣ **PROBAR CONEXIÓN DEEPSEEK**
```bash
cd backend
python -c "
import os
import requests
from dotenv import load_dotenv
load_dotenv()

openrouter_key = os.getenv('OPENROUTER_API_KEY')
if openrouter_key:
    print('✅ API Key configurada')
    
    # Probar modelo correcto
    headers = {
        'Authorization': f'Bearer {openrouter_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': 'deepseek/deepseek-chat-v3.1',
        'messages': [{'role': 'user', 'content': 'Hola, funciona?'}],
        'max_tokens': 50
    }
    
    response = requests.post(
        'https://openrouter.ai/api/v1/chat/completions',
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result['choices'][0]['message']['content']
        print(f'🎉 DEEPSEEK FUNCIONA: {content}')
    else:
        print(f'❌ Error: {response.status_code} - {response.text}')
else:
    print('❌ API Key no configurada')
"
```

### 4️⃣ **VERIFICAR SISTEMA COMPLETO**
```bash
cd backend
python diagnostico_rag.py
```

---

## 🔍 DIAGNÓSTICO DE PROBLEMAS

### ❌ **Si sale error de modelo**
```
"deepseek/deepseek-v3 is not a valid model ID"
```
**Solución**: Los archivos no están actualizados. Descargar versión nueva.

### ❌ **Si no encuentra la API Key**
```
"OPENROUTER_API_KEY: NO CONFIGURADA"
```
**Solución**: Copiar el archivo `.env` desde tu computadora.

### ❌ **Si fallan las dependencias**
```
ImportError: No module named 'sentence_transformers'
```
**Solución**: Ejecutar `python instalar_rag_automatico.py`

---

## 📊 VERIFICACIÓN EXITOSA

Tu compañero debería ver:
```
🧪 Probando llamada con modelo correcto...
📡 Enviando request a OpenRouter con deepseek-chat-v3.1...
📊 Status Code: 200
✅ ¡FUNCIONA! Respuesta de DeepSeek: [respuesta del modelo]
📏 Longitud respuesta: XX caracteres
📊 Tokens usados: {'prompt_tokens': XX, 'completion_tokens': XX, 'total_tokens': XX}
```

---

## 🚀 ARCHIVOS CLAVE QUE NECESITA

1. **Código actualizado**: `backend/utils/rag_utils.py`
2. **Configuración**: `backend/.env`
3. **Diagnóstico**: `backend/diagnostico_rag.py`
4. **Instalador**: `backend/instalar_rag_automatico.py`

---

## ⚡ COMANDO RÁPIDO PARA PROBAR TODO

```bash
cd backend
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from utils.rag_utils import perform_semantic_search, generate_rag_response

query = 'Test de DeepSeek'
search_results = perform_semantic_search(query, top_k=2)
response = generate_rag_response(query, search_results)
print('✅ SISTEMA RAG + DEEPSEEK FUNCIONANDO')
print(f'📏 Respuesta: {len(response)} caracteres')
"
```

---

🎯 **Si todo sale bien, tu compañero tendrá acceso completo a DeepSeek V3.1!**