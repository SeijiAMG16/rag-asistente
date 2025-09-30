#!/usr/bin/env python3
"""
🧪 PRUEBA BÁSICA DE DESCARGA GOOGLE DRIVE
========================================

Script simple para probar que la descarga de PDFs funciona correctamente.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_basic_download():
    """Prueba básica de descarga desde Google Drive"""
    print("🧪 PRUEBA BÁSICA DE DESCARGA GOOGLE DRIVE")
    print("=" * 50)
    print("")
    
    # Verificar dependencias
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
        import io
        print("✅ Dependencias de Google Drive disponibles")
    except ImportError as e:
        print(f"❌ Faltan dependencias: {e}")
        print("💡 Instala con: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return False
    
    # Verificar configuración
    credentials_file = "credentials.json"
    if not os.path.exists(credentials_file):
        print(f"❌ Archivo de credenciales no encontrado: {credentials_file}")
        print("💡 Descarga credentials.json desde Google Cloud Console")
        return False
    
    folder_id = os.getenv("DRIVE_FOLDER_ID")
    if not folder_id:
        print("❌ DRIVE_FOLDER_ID no configurado en .env")
        return False
    
    print(f"📁 ID de carpeta: {folder_id}")
    print("")
    
    try:
        # Inicializar API
        print("🔗 Conectando con Google Drive...")
        scopes = ['https://www.googleapis.com/auth/drive.readonly']
        creds = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=scopes
        )
        service = build('drive', 'v3', credentials=creds)
        print(f"✅ Conectado como: {creds.service_account_email}")
        print("")
        
        # Listar archivos en la carpeta
        print("📋 Listando PDFs en la carpeta...")
        query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(
            q=query, 
            pageSize=10, 
            fields="files(id, name, size, modifiedTime)"
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            print("⚠️ No se encontraron PDFs en la carpeta")
            print("💡 Verifica que:")
            print("   1. El ID de carpeta sea correcto")
            print("   2. La cuenta de servicio tenga acceso a la carpeta")
            print("   3. Hay PDFs en la carpeta")
            return False
        
        print(f"✅ Encontrados {len(files)} PDFs")
        print("")
        
        # Mostrar lista de archivos
        print("📄 ARCHIVOS ENCONTRADOS:")
        print("-" * 30)
        for i, file in enumerate(files, 1):
            size_mb = int(file.get('size', 0)) / (1024 * 1024)
            modified = file.get('modifiedTime', 'N/A')[:10]  # Solo fecha
            print(f"{i:2d}. {file['name']}")
            print(f"     📊 Tamaño: {size_mb:.1f} MB")
            print(f"     📅 Modificado: {modified}")
            print("")
        
        # Intentar descargar el primer archivo como prueba
        if files:
            test_file = files[0]
            print(f"📥 Probando descarga de: {test_file['name']}")
            
            # Crear directorio data/pdfs si no existe
            pdfs_dir = Path("data/pdfs")
            pdfs_dir.mkdir(parents=True, exist_ok=True)
            
            # Descargar archivo
            request = service.files().get_media(fileId=test_file['id'])
            local_path = pdfs_dir / test_file['name']
            
            with open(local_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        print(f"   📥 Descargando... {progress}%", end='\r')
            
            print("")
            print(f"✅ Archivo descargado: {local_path}")
            print(f"📊 Tamaño en disco: {local_path.stat().st_size / (1024*1024):.1f} MB")
            
        print("")
        print("🎉 ¡Prueba de descarga exitosa!")
        print("")
        print("🚀 Para sincronización completa ejecuta:")
        print("   .\\SINCRONIZAR_DRIVE.ps1")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        print("")
        print("🔍 Detalles del error:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_download()
    sys.exit(0 if success else 1)