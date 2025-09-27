"""
🚀 SCRIPT MAESTRO PARA RAG ASISTENTE 
Ejecuta todo automáticamente en un solo comando

Este script:
1. Verifica e instala dependencias de Python
2. Configura la base de datos MySQL automáticamente
3. Ejecuta migraciones de Django
4. Crea usuario administrador
5. Inicia el servidor Django
"""

import subprocess
import sys
import os
import time

def run_command(command, description="", check=True):
    """Ejecutar comando con descripción"""
    if description:
        print(f"🔄 {description}")
    
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print(f"❌ Error: {e.stderr}")
        return False

def main():
    print("🚀 INICIANDO RAG ASISTENTE")
    print("=" * 50)
    
    # 1. Verificar que estamos en el directorio correcto
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    print(f"📁 Directorio de trabajo: {backend_dir}")
    
    # 2. Instalar dependencias automáticamente
    print("\n📦 FASE 1: INSTALANDO DEPENDENCIAS")
    print("-" * 30)
    
    dependencies = [
        'mysql-connector-python',
        'django',
        'djangorestframework', 
        'django-cors-headers',
        'djangorestframework-simplejwt',
        'python-dotenv',
        'chromadb',
        'sentence-transformers',
        'requests',
        'groq'
    ]
    
    for dep in dependencies:
        print(f"Instalando {dep}...")
        if run_command(f"{sys.executable} -m pip install {dep}", check=False):
            print(f"✅ {dep}")
        else:
            print(f"⚠️  {dep} (puede que ya esté instalado)")
    
    # 3. Configurar variables de entorno si no existen
    print("\n🔧 FASE 2: CONFIGURANDO ENTORNO")
    print("-" * 30)
    
    env_file = ".env"
    if not os.path.exists(env_file):
        print("Creando archivo .env...")
        env_content = """# Configuración de base de datos MySQL
DB_ENGINE=django.db.backends.mysql
DB_NAME=rag_asistente
DB_USER=root  
DB_PASSWORD=sistemas
DB_HOST=localhost
DB_PORT=3306

# Configuración automática
AUTO_INIT_DB=1
USE_SQLITE=0

# Configuración de seguridad
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True

# APIs (opcional - el sistema funciona sin ellas)
GROQ_API_KEY=
OPENAI_API_KEY=
"""
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Archivo .env creado")
    else:
        print("✅ Archivo .env ya existe")
    
    # 4. Iniciar Django (la autoconfiguración se ejecuta automáticamente)
    print("\n🎯 FASE 3: INICIANDO SERVIDOR DJANGO")
    print("-" * 30)
    print("⚡ La base de datos y configuraciones se crearán automáticamente")
    print("🔑 Usuario admin se creará automáticamente: admin/admin123")
    print("🌐 El servidor estará disponible en: http://localhost:8000")
    print("\n🚀 Iniciando servidor...")
    print("=" * 50)
    
    # Ejecutar Django server (esto activa toda la autoconfiguración)
    try:
        subprocess.run([sys.executable, "manage.py", "runserver"], check=True)
    except KeyboardInterrupt:
        print("\n\n👋 Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error ejecutando servidor: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ PROCESO COMPLETADO")
        else:
            print("\n❌ PROCESO CON ERRORES")
    except KeyboardInterrupt:
        print("\n\n👋 Proceso cancelado por el usuario")
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")