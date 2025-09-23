import os
import pdfplumber

# Calcula la ruta absoluta a la carpeta raíz (igual que antes)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(PROJECT_ROOT, "data", "pdfs")
TEXT_DIR = os.path.join(PROJECT_ROOT, "data", "texts")

os.makedirs(TEXT_DIR, exist_ok=True)

for filename in os.listdir(PDF_DIR):
    if filename.lower().endswith('.pdf'):
        pdf_path = os.path.join(PDF_DIR, filename)
        txt_path = os.path.join(TEXT_DIR, filename.replace('.pdf', '.txt'))

        print(f"Procesando: {filename}")
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ''
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
            # Guarda el texto extraído
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as e:
            print(f"Error procesando {filename}: {e}")

print("Extracción completada.")
