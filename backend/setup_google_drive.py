#!/usr/bin/env python3
"""
🔧 CONFIGURADOR AUTOMÁTICO DE GOOGLE DRIVE
==========================================

Script para configurar automáticamente la integración con Google Drive.
Incluye asistente interactivo para credenciales y configuración.

Pasos de configuración:
1. Configuración de credenciales de servicio
2. Configuración del ID de carpeta de Drive
3. Configuración de variables de entorno
4. Validación de permisos y conectividad
5. Configuración de sincronización automática

Uso:
    python setup_google_drive.py
    python setup_google_drive.py --auto
    python setup_google_drive.py --validate-only
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple
import argparse

def print_header():
    """Muestra header del configurador"""
    print("🔧 CONFIGURADOR GOOGLE DRIVE - RAG ASISTENTE")
    print("=" * 50)
    print()

def print_step(step_num: int, title: str):
    """Muestra paso de configuración"""
    print(f"📋 PASO {step_num}: {title}")
    print("-" * 30)

def check_dependencies() -> bool:
    """Verifica dependencias necesarias"""
    print_step(1, "VERIFICANDO DEPENDENCIAS")
    
    required_packages = [
        "google-api-python-client",
        "google-auth-httplib2", 
        "google-auth-oauthlib",
        "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "google-api-python-client":
                import googleapiclient
            elif package == "google-auth-httplib2":
                import google.auth.transport.requests
            elif package == "google-auth-oauthlib":
                import google_auth_oauthlib
            elif package == "python-dotenv":
                import dotenv
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Faltan dependencias: {', '.join(missing_packages)}")
        print(f"Instala con: pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True

def setup_credentials(backend_path: Path, auto_mode: bool = False) -> bool:
    """Configura las credenciales de Google Drive"""
    print_step(2, "CONFIGURANDO CREDENCIALES")
    
    creds_path = backend_path / "credentials.json"
    
    if creds_path.exists():
        print(f"✅ Archivo de credenciales encontrado: {creds_path}")
        
        # Validar contenido
        try:
            with open(creds_path, 'r') as f:
                creds_data = json.load(f)
            
            if "type" in creds_data and creds_data["type"] == "service_account":
                print("✅ Credenciales de cuenta de servicio válidas")
                return True
            else:
                print("⚠️ Archivo de credenciales inválido")
        except Exception as e:
            print(f"⚠️ Error leyendo credenciales: {e}")
    
    if auto_mode:
        print("❌ Modo automático: credenciales no encontradas")
        return False
    
    print("\n📝 CONFIGURACIÓN DE CREDENCIALES:")
    print("1. Ve a Google Cloud Console: https://console.cloud.google.com/")
    print("2. Crea un proyecto o selecciona uno existente")
    print("3. Habilita la Google Drive API")
    print("4. Crea una cuenta de servicio:")
    print("   - IAM y administración > Cuentas de servicio")
    print("   - Crear cuenta de servicio")
    print("   - Descargar clave JSON")
    print("5. Copia el archivo JSON a:", str(creds_path))
    print()
    
    while True:
        response = input("¿Has copiado el archivo credentials.json? (s/n): ").lower()
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            if creds_path.exists():
                print("✅ Archivo de credenciales encontrado")
                return True
            else:
                print(f"❌ Archivo no encontrado en: {creds_path}")
        elif response in ['n', 'no']:
            print("⚠️ Configuración cancelada")
            return False
        else:
            print("Respuesta inválida. Usa 's' o 'n'")

def setup_drive_folder(auto_mode: bool = False) -> Optional[str]:
    """Configura el ID de carpeta de Google Drive"""
    print_step(3, "CONFIGURANDO CARPETA DE DRIVE")
    
    if auto_mode:
        folder_id = os.getenv("DRIVE_FOLDER_ID", "")
        if folder_id:
            print(f"✅ ID de carpeta desde env: {folder_id}")
            return folder_id
        else:
            print("❌ DRIVE_FOLDER_ID no configurado en variables de entorno")
            return None
    
    print("\n📝 CONFIGURACIÓN DE CARPETA:")
    print("1. Abre Google Drive en tu navegador")
    print("2. Navega a la carpeta que contiene tus PDFs")
    print("3. Copia el ID de la URL:")
    print("   https://drive.google.com/drive/folders/[ID_AQUÍ]")
    print()
    
    while True:
        folder_id = input("Ingresa el ID de la carpeta de Drive: ").strip()
        if folder_id:
            # Validar formato básico
            if len(folder_id) > 10 and not folder_id.startswith("http"):
                print(f"✅ ID de carpeta configurado: {folder_id}")
                return folder_id
            else:
                print("⚠️ ID inválido. Debe ser solo el ID, no la URL completa")
        else:
            print("⚠️ ID de carpeta requerido")

def create_env_file(backend_path: Path, drive_folder_id: str, auto_mode: bool = False) -> bool:
    """Crea o actualiza archivo .env"""
    print_step(4, "CONFIGURANDO VARIABLES DE ENTORNO")
    
    env_path = backend_path / ".env"
    
    # Variables de configuración
    env_vars = {
        "GOOGLE_DRIVE_ENABLED": "true",
        "DRIVE_FOLDER_ID": drive_folder_id,
        "SERVICE_ACCOUNT_FILE": str(backend_path / "credentials.json"),
        "SYNC_INTERVAL_MINUTES": "30",
        "AUTO_PROCESS_NEW_FILES": "true",
        "MAX_FILE_SIZE_MB": "100",
        "DEFAULT_CHUNK_SIZE": "800",
        "DEFAULT_CHUNK_OVERLAP": "80"
    }
    
    # Leer archivo existente si existe
    existing_vars = {}
    if env_path.exists():
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_vars[key.strip()] = value.strip().strip('"\'')
        except Exception as e:
            print(f"⚠️ Error leyendo .env existente: {e}")
    
    # Merge con configuración nueva
    existing_vars.update(env_vars)
    
    # Escribir archivo .env
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("# Configuración de Google Drive Sync\n")
            f.write("# Generado automáticamente por setup_google_drive.py\n\n")
            
            for key, value in existing_vars.items():
                f.write(f'{key}="{value}"\n')
        
        print(f"✅ Archivo .env actualizado: {env_path}")
        
        # Mostrar configuración
        print("\n📋 CONFIGURACIÓN APLICADA:")
        for key, value in env_vars.items():
            print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando .env: {e}")
        return False

def validate_configuration(backend_path: Path) -> bool:
    """Valida la configuración completa"""
    print_step(5, "VALIDANDO CONFIGURACIÓN")
    
    # Verificar archivos
    creds_path = backend_path / "credentials.json"
    env_path = backend_path / ".env"
    
    if not creds_path.exists():
        print(f"❌ Credenciales no encontradas: {creds_path}")
        return False
    
    if not env_path.exists():
        print(f"❌ Archivo .env no encontrado: {env_path}")
        return False
    
    # Cargar variables de entorno
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        
        drive_folder_id = os.getenv("DRIVE_FOLDER_ID")
        if not drive_folder_id:
            print("❌ DRIVE_FOLDER_ID no configurado")
            return False
        
        print(f"✅ Variables de entorno cargadas")
        
    except Exception as e:
        print(f"❌ Error cargando .env: {e}")
        return False
    
    # Validar conectividad con Google Drive
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        # Cargar credenciales
        scopes = ['https://www.googleapis.com/auth/drive.readonly']
        creds = service_account.Credentials.from_service_account_file(str(creds_path), scopes=scopes)
        service = build('drive', 'v3', credentials=creds)
        
        # Probar acceso a la carpeta
        folder_info = service.files().get(fileId=drive_folder_id, fields="id,name").execute()
        print(f"✅ Acceso a carpeta Drive: {folder_info.get('name', 'Sin nombre')}")
        
        # Probar listado de archivos
        query = f"'{drive_folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(q=query, pageSize=5, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        print(f"✅ PDFs encontrados en carpeta: {len(files)}")
        if files:
            print("   Ejemplos:")
            for f in files[:3]:
                print(f"   - {f.get('name', 'Sin nombre')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error validando conectividad: {e}")
        print("Verifica:")
        print("   - Credenciales de cuenta de servicio correctas")
        print("   - Cuenta de servicio tiene acceso a la carpeta")
        print("   - ID de carpeta es correcto")
        return False

def setup_django_commands(backend_path: Path) -> bool:
    """Verifica que los comandos Django estén disponibles"""
    print_step(6, "VERIFICANDO COMANDOS DJANGO")
    
    # Verificar archivos de comandos
    commands_dir = backend_path / "api" / "management" / "commands"
    
    required_commands = [
        "sync_drive_full.py",
        "start_drive_sync.py"
    ]
    
    missing_commands = []
    for cmd in required_commands:
        cmd_path = commands_dir / cmd
        if cmd_path.exists():
            print(f"✅ {cmd}")
        else:
            print(f"❌ {cmd}")
            missing_commands.append(cmd)
    
    if missing_commands:
        print(f"⚠️ Comandos faltantes: {missing_commands}")
        print("Los comandos se crearán automáticamente cuando ejecutes Django")
    
    # Probar comando básico
    try:
        os.chdir(backend_path)
        result = subprocess.run([
            sys.executable, "manage.py", "help", "sync_drive_full"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Comandos Django disponibles")
            return True
        else:
            print("⚠️ Error en comandos Django - revisar configuración")
            return False
            
    except Exception as e:
        print(f"⚠️ No se pudieron probar comandos Django: {e}")
        return True  # No crítico

def show_usage_instructions():
    """Muestra instrucciones de uso después de la configuración"""
    print("\n🚀 CONFIGURACIÓN COMPLETADA")
    print("=" * 30)
    print("\n📋 COMANDOS DISPONIBLES:")
    print()
    print("🔄 Sincronización manual única:")
    print("   python manage.py sync_drive_full")
    print()
    print("🔄 Sincronización con parámetros:")
    print("   python manage.py sync_drive_full --chunk-size 800 --chunk-overlap 80")
    print()
    print("🔄 Forzar re-descarga completa:")
    print("   python manage.py sync_drive_full --force")
    print()
    print("🔄 Gestión del daemon:")
    print("   python manage.py start_drive_sync --action setup")
    print("   python manage.py start_drive_sync --action sync")
    print("   python manage.py start_drive_sync --action status")
    print()
    print("🔄 Desde PowerShell (script ETL):")
    print("   .\\EJECUTAR_ETL.ps1")
    print("   .\\EJECUTAR_ETL.ps1 -Force")
    print()
    print("📋 CONFIGURACIÓN APLICADA:")
    print("   - Google Drive Sync: HABILITADO")
    print("   - Sincronización automática: Cada 30 minutos") 
    print("   - Procesamiento automático: SÍ")
    print("   - Tamaño máximo archivo: 100MB")
    print()
    print("💡 PRÓXIMOS PASOS:")
    print("   1. Ejecuta: python manage.py sync_drive_full")
    print("   2. Verifica que se descarguen los PDFs")
    print("   3. Confirma que se generen embeddings en ChromaDB")
    print()

def setup_google_drive(auto_mode: bool = False, validate_only: bool = False) -> bool:
    """Función principal de configuración"""
    print_header()
    
    # Detectar directorio backend
    current_path = Path(__file__).parent
    backend_path = current_path
    
    # Verificar que estamos en el directorio correcto
    if not (backend_path / "manage.py").exists():
        print("❌ No se encontró manage.py. Ejecuta desde el directorio backend")
        return False
    
    print(f"📁 Directorio backend: {backend_path}")
    print()
    
    # Si es solo validación
    if validate_only:
        return validate_configuration(backend_path)
    
    # Paso 1: Verificar dependencias
    if not check_dependencies():
        return False
    print()
    
    # Paso 2: Configurar credenciales
    if not setup_credentials(backend_path, auto_mode):
        return False
    print()
    
    # Paso 3: Configurar carpeta de Drive
    drive_folder_id = setup_drive_folder(auto_mode)
    if not drive_folder_id:
        return False
    print()
    
    # Paso 4: Crear archivo .env
    if not create_env_file(backend_path, drive_folder_id, auto_mode):
        return False
    print()
    
    # Paso 5: Validar configuración
    if not validate_configuration(backend_path):
        return False
    print()
    
    # Paso 6: Verificar comandos Django
    setup_django_commands(backend_path)
    print()
    
    # Mostrar instrucciones finales
    if not auto_mode:
        show_usage_instructions()
    
    return True

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Configurador de Google Drive para RAG Asistente")
    parser.add_argument("--auto", action="store_true", help="Modo automático (usa variables de entorno)")
    parser.add_argument("--validate-only", action="store_true", help="Solo validar configuración existente")
    
    args = parser.parse_args()
    
    try:
        success = setup_google_drive(auto_mode=args.auto, validate_only=args.validate_only)
        
        if success:
            print("✅ Configuración exitosa")
            sys.exit(0)
        else:
            print("❌ Error en configuración")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Configuración cancelada por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()