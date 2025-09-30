#!/usr/bin/env python3
"""
🔄 SISTEMA DE SINCRONIZACIÓN GOOGLE DRIVE
=========================================

Sistema completo para sincronización automática de PDFs desde Google Drive.
Incluye descarga, procesamiento y ingesta en ChromaDB.

Características:
- Sincronización automática con intervalo configurable
- Detección de archivos nuevos/modificados
- Procesamiento automático con ETL
- Sistema de logs y notificaciones
- Configuración mediante variables de entorno

Dependencias:
- google-api-python-client
- google-auth-httplib2 
- google-auth-oauthlib
"""

import os
import sys
import time
import json
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Dependencias de Google Drive API
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    import io
except ImportError as e:
    print(f"❌ Faltan dependencias de Google Drive: {e}")
    print("Instala con: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SyncConfig:
    """Configuración del sistema de sincronización"""
    # Credenciales
    service_account_file: str = ""
    drive_folder_id: str = ""
    
    # Directorios
    backend_path: str = ""
    downloads_dir: str = ""
    pdfs_dir: str = ""
    texts_dir: str = ""
    
    # Configuración de sync
    sync_interval_minutes: int = 30
    auto_process_new_files: bool = True
    max_file_size_mb: int = 100
    
    # Configuración de ETL
    chunk_size: int = 800
    chunk_overlap: int = 80
    force_redownload: bool = False

def create_sync_config() -> SyncConfig:
    """Crea configuración desde variables de entorno"""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Detectar path del backend
    backend_path = Path(__file__).parent
    
    config = SyncConfig()
    config.backend_path = str(backend_path)
    config.service_account_file = os.getenv("SERVICE_ACCOUNT_FILE", str(backend_path / "credentials.json"))
    config.drive_folder_id = os.getenv("DRIVE_FOLDER_ID", "")
    
    # Directorios
    data_dir = backend_path / "data"
    config.downloads_dir = str(data_dir / "downloads")
    config.pdfs_dir = str(data_dir / "pdfs")
    config.texts_dir = str(data_dir / "texts")
    
    # Configuración de sync
    config.sync_interval_minutes = int(os.getenv("SYNC_INTERVAL_MINUTES", "30"))
    config.auto_process_new_files = os.getenv("AUTO_PROCESS_NEW_FILES", "true").lower() == "true"
    config.max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    
    # Configuración ETL
    config.chunk_size = int(os.getenv("DEFAULT_CHUNK_SIZE", "800"))
    config.chunk_overlap = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "80"))
    config.force_redownload = os.getenv("FORCE_REDOWNLOAD", "false").lower() == "true"
    
    return config

class GoogleDriveSync:
    """Sistema principal de sincronización con Google Drive"""
    
    def __init__(self, config: SyncConfig):
        self.config = config
        self.service = None
        self.running = False
        self.sync_thread = None
        
        # Estado de archivos procesados
        self.processed_files_path = Path(config.backend_path) / "data" / "processed_files.json"
        self.processed_files = self._load_processed_files()
        
        # Crear directorios necesarios
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Asegura que existan todos los directorios necesarios"""
        dirs = [
            self.config.downloads_dir,
            self.config.pdfs_dir,
            self.config.texts_dir,
            str(Path(self.config.backend_path) / "data")
        ]
        
        for directory in dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _load_processed_files(self) -> Dict:
        """Carga el registro de archivos procesados"""
        if self.processed_files_path.exists():
            try:
                with open(self.processed_files_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando archivos procesados: {e}")
        
        return {"processed_files": {}, "last_sync": None}
    
    def _save_processed_files(self):
        """Guarda el registro de archivos procesados"""
        try:
            with open(self.processed_files_path, 'w', encoding='utf-8') as f:
                json.dump(self.processed_files, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando archivos procesados: {e}")
    
    def initialize_drive_api(self) -> bool:
        """Inicializa la API de Google Drive"""
        try:
            if not os.path.exists(self.config.service_account_file):
                logger.error(f"Archivo de credenciales no encontrado: {self.config.service_account_file}")
                return False
            
            scopes = ['https://www.googleapis.com/auth/drive.readonly']
            creds = service_account.Credentials.from_service_account_file(
                self.config.service_account_file, scopes=scopes
            )
            
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("✅ API de Google Drive inicializada")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando Google Drive API: {e}")
            return False
    
    def get_drive_files(self) -> List[Dict]:
        """Obtiene lista de PDFs desde Google Drive"""
        try:
            if not self.service:
                raise Exception("API de Google Drive no inicializada")
            
            query = f"'{self.config.drive_folder_id}' in parents and mimeType='application/pdf' and trashed=false"
            results = self.service.files().list(
                q=query, 
                pageSize=1000, 
                fields="files(id, name, modifiedTime, size)"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"📄 Encontrados {len(files)} PDFs en Drive")
            return files
            
        except Exception as e:
            logger.error(f"Error obteniendo archivos de Drive: {e}")
            return []
    
    def download_file(self, file_info: Dict) -> bool:
        """Descarga un archivo específico desde Drive"""
        try:
            file_id = file_info['id']
            file_name = file_info['name']
            file_size = int(file_info.get('size', 0))
            
            # Verificar tamaño
            if file_size > self.config.max_file_size_mb * 1024 * 1024:
                logger.warning(f"⚠️ Archivo muy grande saltado: {file_name} ({file_size/1024/1024:.1f}MB)")
                return False
            
            local_path = Path(self.config.pdfs_dir) / file_name
            
            # Verificar si ya existe y no es forzado
            if local_path.exists() and not self.config.force_redownload:
                # Verificar si fue modificado
                local_modified = datetime.fromtimestamp(local_path.stat().st_mtime).isoformat()
                drive_modified = file_info.get('modifiedTime', '')
                
                if local_modified >= drive_modified:
                    logger.debug(f"⏭️ Archivo sin cambios: {file_name}")
                    return True
            
            # Descargar archivo
            logger.info(f"📥 Descargando: {file_name}")
            request = self.service.files().get_media(fileId=file_id)
            
            with io.FileIO(str(local_path), 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.debug(f"📥 {file_name}: {progress}%")
            
            # Actualizar registro
            self.processed_files["processed_files"][file_name] = {
                "downloaded_at": datetime.now().isoformat(),
                "drive_modified": file_info.get('modifiedTime', ''),
                "file_id": file_id,
                "size": file_size
            }
            
            logger.info(f"✅ Descargado: {file_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error descargando {file_info.get('name', 'archivo')}: {e}")
            return False
    
    def process_with_etl(self, force_all: bool = False) -> Dict:
        """Procesa archivos usando el sistema ETL"""
        stats = {"processed": 0, "errors": 0, "skipped": 0}
        
        try:
            # Importar ETL processor
            etl_path = Path(self.config.backend_path) / "etl_rag_complete.py"
            if not etl_path.exists():
                logger.warning("⚠️ ETL processor no encontrado, creando básico...")
                self._create_basic_etl()
            
            # Ejecutar ETL
            import subprocess
            
            etl_cmd = [
                sys.executable, 
                str(etl_path),
                "--chunk-size", str(self.config.chunk_size),
                "--chunk-overlap", str(self.config.chunk_overlap)
            ]
            
            if force_all:
                etl_cmd.append("--force")
            
            logger.info(f"🔄 Ejecutando ETL: {' '.join(etl_cmd)}")
            result = subprocess.run(etl_cmd, capture_output=True, text=True, cwd=self.config.backend_path)
            
            if result.returncode == 0:
                logger.info("✅ ETL completado exitosamente")
                stats["processed"] = len([f for f in Path(self.config.pdfs_dir).glob("*.pdf")])
            else:
                logger.error(f"❌ Error en ETL: {result.stderr}")
                stats["errors"] = 1
                
        except Exception as e:
            logger.error(f"Error en procesamiento ETL: {e}")
            stats["errors"] = 1
        
        return stats
    
    def _create_basic_etl(self):
        """Crea un ETL básico si no existe"""
        etl_content = '''#!/usr/bin/env python3
"""ETL Básico auto-generado"""
import sys
from pathlib import Path

# Agregar backend al path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

try:
    from etl_rag_complete import RAGETLProcessor
    
    if __name__ == "__main__":
        processor = RAGETLProcessor()
        processor.run_complete_etl()
        print("✅ ETL completado")
        
except ImportError:
    print("❌ ETL processor no disponible")
    sys.exit(1)
'''
        etl_path = Path(self.config.backend_path) / "basic_etl.py"
        with open(etl_path, 'w', encoding='utf-8') as f:
            f.write(etl_content)
    
    def sync_once(self) -> Dict:
        """Ejecuta una sincronización única"""
        logger.info("🔄 Iniciando sincronización única...")
        stats = {
            "files_found": 0,
            "files_downloaded": 0,
            "files_processed": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Obtener archivos de Drive
            files = self.get_drive_files()
            stats["files_found"] = len(files)
            
            if not files:
                logger.info("📭 No se encontraron archivos nuevos")
                return stats
            
            # Descargar archivos
            downloaded_count = 0
            for file_info in files:
                if self.download_file(file_info):
                    downloaded_count += 1
            
            stats["files_downloaded"] = downloaded_count
            
            # Procesar con ETL si está habilitado
            if self.config.auto_process_new_files and downloaded_count > 0:
                etl_stats = self.process_with_etl()
                stats["files_processed"] = etl_stats["processed"]
                stats["errors"] += etl_stats["errors"]
            
            # Actualizar timestamp
            self.processed_files["last_sync"] = datetime.now().isoformat()
            self._save_processed_files()
            
            logger.info(f"✅ Sincronización completada: {downloaded_count} descargados, {stats['files_processed']} procesados")
            
        except Exception as e:
            logger.error(f"Error en sincronización: {e}")
            stats["errors"] += 1
        
        stats["end_time"] = datetime.now().isoformat()
        return stats
    
    def start_background_sync(self):
        """Inicia sincronización en background con intervalo"""
        if self.running:
            logger.warning("⚠️ Sincronización ya está ejecutándose")
            return
        
        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_daemon)
        self.sync_thread.daemon = True
        self.sync_thread.start()
        
        logger.info(f"🚀 Sincronización automática iniciada (cada {self.config.sync_interval_minutes} minutos)")
    
    def stop_background_sync(self):
        """Detiene la sincronización en background"""
        self.running = False
        if self.sync_thread and self.sync_thread.is_alive():
            logger.info("🛑 Deteniendo sincronización automática...")
            self.sync_thread.join(timeout=5)
        logger.info("✅ Sincronización automática detenida")
    
    def _sync_daemon(self):
        """Daemon de sincronización automática"""
        logger.info("🔄 Daemon de sincronización iniciado")
        
        while self.running:
            try:
                # Ejecutar sincronización
                stats = self.sync_once()
                
                # Log de resultados
                if stats["errors"] == 0:
                    logger.info(f"✅ Sync automático: {stats['files_downloaded']} descargados")
                else:
                    logger.error(f"❌ Errores en sync automático: {stats['errors']}")
                
                # Esperar hasta el próximo ciclo
                for _ in range(self.config.sync_interval_minutes * 60):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error en daemon de sync: {e}")
                time.sleep(60)  # Esperar 1 minuto antes de reintentar
        
        logger.info("🛑 Daemon de sincronización detenido")
    
    def get_status(self) -> Dict:
        """Obtiene el estado actual del sistema"""
        status = {
            "enabled": bool(self.config.drive_folder_id),
            "running": self.running,
            "config": {
                "folder_id": self.config.drive_folder_id,
                "interval_minutes": self.config.sync_interval_minutes,
                "auto_process": self.config.auto_process_new_files,
                "service_account_file": self.config.service_account_file
            },
            "directories": {
                "downloads": {"exists": Path(self.config.downloads_dir).exists()},
                "pdfs": {"exists": Path(self.config.pdfs_dir).exists()},
                "texts": {"exists": Path(self.config.texts_dir).exists()}
            },
            "files": {
                "credentials": {"exists": Path(self.config.service_account_file).exists()},
                "processed_files": {"exists": self.processed_files_path.exists()}
            },
            "stats": self.processed_files
        }
        
        # Contar archivos
        try:
            status["directories"]["pdfs"]["count"] = len(list(Path(self.config.pdfs_dir).glob("*.pdf")))
            status["directories"]["texts"]["count"] = len(list(Path(self.config.texts_dir).glob("*.txt")))
        except:
            pass
        
        return status

def main():
    """Función principal para testing"""
    print("🔄 GOOGLE DRIVE SYNC - Testing")
    print("=" * 40)
    
    config = create_sync_config()
    sync_system = GoogleDriveSync(config)
    
    if not sync_system.initialize_drive_api():
        print("❌ Error inicializando API")
        return
    
    # Mostrar estado
    status = sync_system.get_status()
    print(f"📁 Carpeta ID: {status['config']['folder_id']}")
    print(f"⏱️ Intervalo: {status['config']['interval_minutes']} minutos")
    print(f"🔄 Auto-proceso: {status['config']['auto_process']}")
    
    # Ejecutar sync único
    stats = sync_system.sync_once()
    print(f"\n✅ Sync completado:")
    print(f"   📄 Archivos encontrados: {stats['files_found']}")
    print(f"   📥 Archivos descargados: {stats['files_downloaded']}")
    print(f"   🔄 Archivos procesados: {stats['files_processed']}")
    
    if stats['errors'] > 0:
        print(f"   ⚠️ Errores: {stats['errors']}")

if __name__ == "__main__":
    main()