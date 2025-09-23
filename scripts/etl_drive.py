"""
ETL completo para extraer documentos de Google Drive y procesarlos para RAG
"""

import os
import sys
import logging
import io
from datetime import datetime
from typing import List, Dict, Tuple

# Configuración de paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuración básica
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, "credentials.json")
DRIVE_FOLDER_ID = "1wAYnaln3Dg-MnFy6rNhwqPlh7Ouc4EP8"
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PDF_DIR = os.path.join(DATA_DIR, "pdfs")
TEXT_DIR = os.path.join(DATA_DIR, "texts")
CHROMA_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

SUPPORTED_MIME_TYPES = {
    'application/pdf': '.pdf',
    'application/vnd.google-apps.document': '.docx',
    'text/plain': '.txt',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx'
}

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/documents.readonly'
]

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Imports de Google Drive
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from googleapiclient.errors import HttpError

# Imports para procesamiento de documentos
import pdfplumber
from docx import Document
import PyPDF2

# Configuración de logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class GoogleDriveETL:
    """ETL para extraer y procesar documentos de Google Drive"""
    
    def __init__(self):
        """Inicializar el ETL"""
        self.service = None
        self.setup_directories()
        self.authenticate()
    
    def setup_directories(self):
        """Crear directorios necesarios"""
        directories = [DATA_DIR, PDF_DIR, TEXT_DIR, CHROMA_DIR]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Directorio verificado: {directory}")
    
    def authenticate(self):
        """Autenticar con Google Drive API"""
        try:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(f"Archivo de credenciales no encontrado: {CREDENTIALS_FILE}")
            
            creds = service_account.Credentials.from_service_account_file(
                CREDENTIALS_FILE, scopes=SCOPES)
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Autenticación con Google Drive exitosa")
            
        except Exception as e:
            logger.error(f"Error en autenticación: {e}")
            raise
    
    def get_files_from_drive(self) -> List[Dict]:
        """Obtener lista de archivos de la carpeta de Google Drive"""
        try:
            files = []
            page_token = None
            
            # Crear query para buscar archivos soportados
            mime_types = list(SUPPORTED_MIME_TYPES.keys())
            mime_query = " or ".join([f"mimeType='{mime}'" for mime in mime_types])
            query = f"'{DRIVE_FOLDER_ID}' in parents and ({mime_query}) and trashed=false"
            
            while True:
                results = self.service.files().list(
                    q=query,
                    pageSize=100,
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)",
                    pageToken=page_token
                ).execute()
                
                files.extend(results.get('files', []))
                page_token = results.get('nextPageToken')
                
                if not page_token:
                    break
            
            logger.info(f"Encontrados {len(files)} archivos en Google Drive")
            return files
            
        except HttpError as e:
            logger.error(f"Error al obtener archivos de Drive: {e}")
            raise
    
    def download_file(self, file_info: Dict) -> Tuple[bool, str]:
        """Descargar un archivo de Google Drive"""
        file_id = file_info['id']
        file_name = file_info['name']
        mime_type = file_info['mimeType']
        
        # Determinar extensión y directorio de destino
        if mime_type == 'application/pdf':
            extension = '.pdf'
            target_dir = PDF_DIR
        elif mime_type in ['application/vnd.google-apps.document']:
            # Google Docs - exportar como DOCX
            extension = '.docx'
            target_dir = PDF_DIR  # Lo ponemos en PDF_DIR para procesamiento conjunto
        else:
            extension = SUPPORTED_MIME_TYPES.get(mime_type, '.txt')
            target_dir = PDF_DIR
        
        # Asegurar que el nombre tenga la extensión correcta
        if not file_name.endswith(extension):
            file_name += extension
        
        local_path = os.path.join(target_dir, file_name)
        
        # Verificar si ya existe
        if os.path.exists(local_path):
            logger.info(f"Archivo ya existe: {file_name}")
            return True, local_path
        
        try:
            logger.info(f"Descargando: {file_name}")
            
            if mime_type == 'application/vnd.google-apps.document':
                # Exportar Google Docs como DOCX
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
            else:
                # Descargar archivo normal
                request = self.service.files().get_media(fileId=file_id)
            
            # Descargar el archivo
            fh = io.FileIO(local_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"  Progreso: {progress}%")
            
            logger.info(f"Descarga completada: {file_name}")
            return True, local_path
            
        except Exception as e:
            logger.error(f"Error descargando {file_name}: {e}")
            return False, ""
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extraer texto de un archivo PDF"""
        text = ""
        try:
            # Intentar con pdfplumber primero
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
        except Exception as e:
            logger.warning(f"pdfplumber falló para {pdf_path}, intentando PyPDF2: {e}")
            try:
                # Fallback a PyPDF2
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + '\n'
            except Exception as e2:
                logger.error(f"Error extrayendo texto de {pdf_path}: {e2}")
        
        return text.strip()
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extraer texto de un archivo DOCX"""
        try:
            doc = Document(docx_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + '\n'
            return text.strip()
        except Exception as e:
            logger.error(f"Error extrayendo texto de {docx_path}: {e}")
            return ""
    
    def extract_text_from_txt(self, txt_path: str) -> str:
        """Extraer texto de un archivo TXT"""
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error leyendo {txt_path}: {e}")
            return ""
    
    def process_documents(self) -> Dict[str, str]:
        """Procesar todos los documentos descargados y extraer texto"""
        processed_texts = {}
        
        # Procesar archivos en PDF_DIR
        for filename in os.listdir(PDF_DIR):
            file_path = os.path.join(PDF_DIR, filename)
            text = ""
            
            logger.info(f"Procesando: {filename}")
            
            if filename.lower().endswith('.pdf'):
                text = self.extract_text_from_pdf(file_path)
            elif filename.lower().endswith(('.docx', '.doc')):
                text = self.extract_text_from_docx(file_path)
            elif filename.lower().endswith('.txt'):
                text = self.extract_text_from_txt(file_path)
            
            if text:
                # Guardar texto extraído
                txt_filename = os.path.splitext(filename)[0] + '.txt'
                txt_path = os.path.join(TEXT_DIR, txt_filename)
                
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                processed_texts[filename] = text
                logger.info(f"Texto extraído y guardado: {txt_filename}")
            else:
                logger.warning(f"No se pudo extraer texto de: {filename}")
        
        return processed_texts
    
    def run_complete_etl(self):
        """Ejecutar el ETL completo"""
        logger.info("=== INICIANDO ETL COMPLETO ===")
        start_time = datetime.now()
        
        try:
            # Paso 1: Obtener lista de archivos
            logger.info("Paso 1: Obteniendo lista de archivos de Google Drive...")
            files = self.get_files_from_drive()
            
            # Paso 2: Descargar archivos
            logger.info("Paso 2: Descargando archivos...")
            downloaded_count = 0
            for file_info in files:
                success, path = self.download_file(file_info)
                if success:
                    downloaded_count += 1
            
            logger.info(f"Archivos descargados: {downloaded_count}/{len(files)}")
            
            # Paso 3: Procesar documentos y extraer texto
            logger.info("Paso 3: Extrayendo texto de documentos...")
            processed_texts = self.process_documents()
            
            # Estadísticas finales
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("=== ETL COMPLETADO ===")
            logger.info(f"Tiempo total: {duration}")
            logger.info(f"Archivos procesados: {len(processed_texts)}")
            logger.info(f"Directorio de textos: {TEXT_DIR}")
            logger.info(f"Directorio de PDFs: {PDF_DIR}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error en ETL: {e}")
            raise

def main():
    """Función principal"""
    try:
        etl = GoogleDriveETL()
        etl.run_complete_etl()
        print("\n🎉 ETL completado exitosamente!")
        print(f"📁 Archivos descargados en: {PDF_DIR}")
        print(f"📄 Textos extraídos en: {TEXT_DIR}")
        print("\n📋 Próximo paso: Ejecutar la ingesta a ChromaDB")
        
    except Exception as e:
        print(f"\n❌ Error en ETL: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())