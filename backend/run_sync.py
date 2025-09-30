#!/usr/bin/env python3
"""
Script principal para ejecutar sincronización de Google Drive
"""

import sys
import os
from pathlib import Path

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Ejecutar sincronización completa"""
    print("🔄 SINCRONIZACIÓN GOOGLE DRIVE - RAG ASISTENTE")
    print("=" * 50)
    print("")
    
    try:
        # Importar el sistema de sincronización
        from google_drive_sync import GoogleDriveSync, create_sync_config
        
        print("🔗 Inicializando conexión con Google Drive...")
        
        # Cargar configuración
        config = create_sync_config()
        sync = GoogleDriveSync(config)
        
        if not sync.initialize_drive_api():
            print("❌ Error inicializando Google Drive API")
            print("💡 Verifica credentials.json y permisos")
            sys.exit(1)
        
        print("✅ Conexión establecida")
        print("")
        
        # Ejecutar sincronización
        print("📥 Ejecutando sincronización...")
        stats = sync.sync_once()
        
        print("")
        print("📊 RESULTADOS DE SINCRONIZACIÓN:")
        print("=" * 40)
        print(f"   📄 Archivos encontrados en Drive: {stats['files_found']}")
        print(f"   📥 Archivos descargados: {stats['files_downloaded']}")
        print(f"   🔄 Archivos procesados con ETL: {stats['files_processed']}")
        print(f"   ❌ Errores: {stats['errors']}")
        print(f"   ⏱️ Iniciado: {stats['start_time']}")
        
        if stats['errors'] == 0:
            print("")
            print("✅ Sincronización completada exitosamente")
            
            # Mostrar estadísticas adicionales
            if stats['files_downloaded'] > 0:
                print(f"💾 Espacio usado: ~{stats['files_downloaded'] * 2:.1f}MB")
                print("📁 Archivos guardados en: data/pdfs/")
            
            if stats['files_processed'] > 0:
                print("🧠 Vectores actualizados en Chroma DB")
            
            print("")
            print("🚀 El sistema RAG está listo para usar")
        else:
            print("")
            print("⚠️ Sincronización completada con errores")
            print("💡 Revisa los logs para más detalles")
            
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        print("💡 Ejecuta primero: pip install google-api-python-client python-dotenv")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error durante sincronización: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()