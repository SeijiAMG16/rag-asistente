"""
Pipeline completo de ETL + RAG
Ejecuta todo el proceso: Descarga de Google Drive -> Extracción de texto -> Ingesta a ChromaDB
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def run_command(command: str, description: str) -> bool:
    """Ejecutar un comando y manejar errores"""
    logger.info(f"🔄 {description}")
    logger.info(f"Ejecutando: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            print(result.stdout)
        
        logger.info(f"✅ {description} - Completado")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} - Falló")
        logger.error(f"Error: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def check_requirements():
    """Verificar que existan los archivos necesarios"""
    required_files = [
        "../credentials.json",
        "config.py",
        "etl_drive.py",
        "ingest_chromadb.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        logger.error("❌ Archivos faltantes:")
        for file in missing_files:
            logger.error(f"   - {file}")
        return False
    
    logger.info("✅ Todos los archivos necesarios están presentes")
    return True

def run_full_pipeline():
    """Ejecutar el pipeline completo"""
    start_time = datetime.now()
    
    print("🚀 INICIANDO PIPELINE COMPLETO DE RAG")
    print("=" * 50)
    print("Este proceso incluye:")
    print("1. ⬇️  Descarga de archivos desde Google Drive")
    print("2. 📄 Extracción de texto de PDFs y documentos")
    print("3. 🧠 Generación de embeddings e ingesta a ChromaDB")
    print("=" * 50)
    
    # Verificar requisitos
    if not check_requirements():
        return False
    
    success = True
    
    # Paso 1: ETL de Google Drive
    if success:
        success = run_command(
            "python etl_drive.py",
            "Paso 1: ETL de Google Drive (descarga y extracción)"
        )
    
    # Paso 2: Ingesta a ChromaDB
    if success:
        success = run_command(
            "python ingest_chromadb.py",
            "Paso 2: Ingesta de documentos a ChromaDB"
        )
    
    # Resultados finales
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 PIPELINE COMPLETADO EXITOSAMENTE")
        print(f"⏱️  Tiempo total: {duration}")
        print("\n📋 Recursos disponibles:")
        print(f"   📁 Documentos descargados: ./data/pdfs/")
        print(f"   📄 Textos extraídos: ./data/texts/")
        print(f"   🧠 Base de datos vectorial: ./chroma_db/")
        print("\n🚀 ¡Tu sistema RAG está listo para usar!")
    else:
        print("❌ PIPELINE FALLÓ")
        print("Revisa los logs anteriores para más detalles")
    
    return success

def main():
    """Función principal"""
    try:
        # Cambiar al directorio de scripts
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        success = run_full_pipeline()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Proceso interrumpido por el usuario")
        return 1
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return 1

if __name__ == "__main__":
    exit(main())