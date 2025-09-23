import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DRIVE_FOLDER_ID, DOWNLOAD_DIR
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import io

# Configuración
from config import DRIVE_FOLDER_ID, DOWNLOAD_DIR

# Credenciales (descarga credentials.json desde Google Cloud Console)
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = '../credentials.json'

# Crear directorio de descarga si no existe
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_pdfs_from_drive():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    # Buscar todos los PDFs en la carpeta
    query = f"'{DRIVE_FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
    results = service.files().list(q=query, pageSize=1000, fields="files(id, name)").execute()
    files = results.get('files', [])

    for file in files:
        file_id = file['id']
        file_name = file['name']
        local_path = os.path.join(DOWNLOAD_DIR, file_name)
        if os.path.exists(local_path):
            print(f"Ya existe: {file_name}")
            continue
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(local_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        print(f"Descargando: {file_name}")
        while done is False:
            status, done = downloader.next_chunk()
            print(f"  Descargado {int(status.progress() * 100)}%.")
    print("Descarga completada.")

if __name__ == '__main__':
    download_pdfs_from_drive()
