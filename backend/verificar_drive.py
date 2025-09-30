#!/usr/bin/env python3
"""
🔍 VERIFICADOR DE CONFIGURACIÓN GOOGLE DRIVE
============================================

Script para verificar la configuración de Google Drive paso a paso.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_credentials():
    """Verifica que las credenciales funcionen"""
    print("🔐 VERIFICANDO CREDENCIALES")
    print("=" * 30)
    print("")
    
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        # Cargar credenciales
        credentials_file = "credentials.json"
        if not os.path.exists(credentials_file):
            print(f"❌ Archivo {credentials_file} no encontrado")
            return False
        
        print(f"✅ Archivo {credentials_file} encontrado")
        
        # Verificar formato del archivo
        import json
        with open(credentials_file, 'r') as f:
            creds_data = json.load(f)
        
        if creds_data.get('type') != 'service_account':
            print("❌ El archivo no es de cuenta de servicio")
            return False
        
        print(f"✅ Cuenta de servicio: {creds_data.get('client_email', 'N/A')}")
        
        # Inicializar API
        scopes = ['https://www.googleapis.com/auth/drive.readonly']
        creds = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=scopes
        )
        
        service = build('drive', 'v3', credentials=creds)
        print("✅ API de Google Drive inicializada")
        
        # Probar listado básico (sin especificar carpeta)
        print("🔍 Probando acceso básico...")
        results = service.files().list(pageSize=5).execute()
        files = results.get('files', [])
        
        print(f"✅ Acceso exitoso. Archivos visibles: {len(files)}")
        
        if files:
            print("📄 Primeros archivos encontrados:")
            for i, file in enumerate(files[:3], 1):
                print(f"   {i}. {file.get('name', 'Sin nombre')} (ID: {file.get('id', 'N/A')})")
        
        return service, creds_data.get('client_email')
        
    except Exception as e:
        print(f"❌ Error verificando credenciales: {e}")
        return False

def find_pdf_folders(service):
    """Busca carpetas que contengan PDFs"""
    print("")
    print("📁 BUSCANDO CARPETAS CON PDFS")
    print("=" * 30)
    print("")
    
    try:
        # Buscar carpetas
        print("🔍 Buscando todas las carpetas accesibles...")
        folders_query = "mimeType='application/vnd.google-apps.folder' and trashed=false"
        folders_result = service.files().list(
            q=folders_query,
            pageSize=20,
            fields="files(id, name, parents)"
        ).execute()
        
        folders = folders_result.get('files', [])
        print(f"📁 Encontradas {len(folders)} carpetas")
        
        pdf_folders = []
        
        for folder in folders:
            folder_id = folder['id']
            folder_name = folder['name']
            
            # Buscar PDFs en esta carpeta
            pdf_query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
            pdf_result = service.files().list(
                q=pdf_query,
                pageSize=5,
                fields="files(id, name)"
            ).execute()
            
            pdfs = pdf_result.get('files', [])
            
            if pdfs:
                pdf_folders.append({
                    'id': folder_id,
                    'name': folder_name,
                    'pdf_count': len(pdfs),
                    'sample_pdfs': [pdf['name'] for pdf in pdfs[:3]]
                })
                print(f"✅ {folder_name} (ID: {folder_id}) - {len(pdfs)} PDFs")
                for pdf in pdfs[:3]:
                    print(f"      📄 {pdf['name']}")
                print("")
        
        return pdf_folders
        
    except Exception as e:
        print(f"❌ Error buscando carpetas: {e}")
        return []

def test_specific_folder(service, folder_id):
    """Prueba acceso a una carpeta específica"""
    print("")
    print(f"🎯 PROBANDO CARPETA ESPECÍFICA: {folder_id}")
    print("=" * 50)
    print("")
    
    try:
        # Verificar que la carpeta existe
        folder_info = service.files().get(fileId=folder_id).execute()
        print(f"✅ Carpeta encontrada: {folder_info.get('name', 'Sin nombre')}")
        
        # Buscar PDFs en la carpeta
        pdf_query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        pdf_result = service.files().list(
            q=pdf_query,
            pageSize=10,
            fields="files(id, name, size, modifiedTime)"
        ).execute()
        
        pdfs = pdf_result.get('files', [])
        
        if pdfs:
            print(f"✅ Encontrados {len(pdfs)} PDFs en la carpeta")
            print("")
            print("📄 ARCHIVOS ENCONTRADOS:")
            print("-" * 25)
            for i, pdf in enumerate(pdfs, 1):
                size_mb = int(pdf.get('size', 0)) / (1024 * 1024)
                print(f"{i:2d}. {pdf['name']}")
                print(f"     📊 {size_mb:.1f} MB | 📅 {pdf.get('modifiedTime', 'N/A')[:10]}")
                print("")
            return True
        else:
            print("⚠️ No se encontraron PDFs en esta carpeta")
            return False
            
    except Exception as e:
        print(f"❌ Error accediendo a la carpeta: {e}")
        return False

def main():
    print("🔍 VERIFICADOR COMPLETO DE GOOGLE DRIVE")
    print("=" * 45)
    print("")
    
    # Paso 1: Verificar credenciales
    creds_result = test_credentials()
    if not creds_result:
        print("\n❌ No se pueden verificar las credenciales. Revisa el archivo credentials.json")
        return False
    
    service, email = creds_result
    print(f"\n🎉 Credenciales válidas para: {email}")
    
    # Paso 2: Buscar carpetas con PDFs
    pdf_folders = find_pdf_folders(service)
    
    if pdf_folders:
        print("\n📋 RESUMEN DE CARPETAS CON PDFS:")
        print("=" * 35)
        for i, folder in enumerate(pdf_folders, 1):
            print(f"{i}. {folder['name']}")
            print(f"   ID: {folder['id']}")
            print(f"   PDFs: {folder['pdf_count']}")
            print(f"   Muestra: {', '.join(folder['sample_pdfs'])}")
            print("")
    
    # Paso 3: Probar carpeta del .env si existe
    folder_id = os.getenv("DRIVE_FOLDER_ID")
    if folder_id and folder_id != "tu_folder_id_aqui":
        print(f"\n🔧 Probando carpeta configurada en .env: {folder_id}")
        if test_specific_folder(service, folder_id):
            print("\n✅ La carpeta configurada funciona correctamente")
        else:
            print("\n❌ Problema con la carpeta configurada")
            if pdf_folders:
                print("\n💡 Sugerencia: Usa una de las carpetas encontradas arriba")
                print("   Actualiza DRIVE_FOLDER_ID en el archivo .env")
    
    # Resumen final
    print("\n🎯 RECOMENDACIONES:")
    print("=" * 20)
    
    if pdf_folders:
        best_folder = max(pdf_folders, key=lambda x: x['pdf_count'])
        print(f"✅ Carpeta recomendada: {best_folder['name']}")
        print(f"✅ ID para .env: {best_folder['id']}")
        print(f"✅ Contiene {best_folder['pdf_count']} PDFs")
    else:
        print("⚠️ No se encontraron carpetas con PDFs")
        print("💡 Verifica que:")
        print("   1. La cuenta de servicio tenga acceso a las carpetas")
        print("   2. Las carpetas contengan archivos PDF")
        print("   3. Los PDFs no estén en la papelera")
    
    print("\n🚀 Para continuar:")
    print("   1. Actualiza DRIVE_FOLDER_ID en .env con el ID correcto")
    print("   2. Ejecuta: .\\SINCRONIZAR_DRIVE.ps1")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Verificación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)