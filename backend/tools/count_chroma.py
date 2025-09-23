import os
import sys
import chromadb


def count_collection(db_path: str, collection_name: str = "documents") -> int:
	client = chromadb.PersistentClient(path=db_path)
	try:
		col = client.get_collection(collection_name)
	except Exception:
		col = client.get_or_create_collection(collection_name)
	try:
		return col.count()
	except Exception:
		return 0


def main():
	# Repo root = tres niveles arriba de este archivo (backend/tools/*.py)
	repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

	chroma_repo = os.path.join(repo_root, "chroma_db")
	chroma_backend = os.path.join(backend_dir, "chroma_db")

	used_paths = []
	if os.path.isdir(chroma_repo):
		used_paths.append(("repo_root/chroma_db", chroma_repo))
	if os.path.isdir(chroma_backend) and chroma_backend != chroma_repo:
		used_paths.append(("backend/chroma_db", chroma_backend))

	if not used_paths:
		print("No se encontró ninguna carpeta 'chroma_db'. Ejecuta el ETL o crea la base.")
		sys.exit(1)

	# Reportar conteos por cada ubicación detectada
	print("Rutas detectadas de ChromaDB:")
	total_reported = 0
	for label, path in used_paths:
		cnt = count_collection(path)
		total_reported += cnt
		print(f"- {label}: {path}")
		print(f"  Colección 'documents' -> {cnt} chunks")

	# Sugerencia si hay dos ubicaciones
	if len(used_paths) > 1:
		print("\nAVISO: Existen dos carpetas 'chroma_db'. El proyecto usa la de repo_root por defecto.")
		print("Recomendación: mantén solo una para evitar confusiones.")


if __name__ == "__main__":
	main()
