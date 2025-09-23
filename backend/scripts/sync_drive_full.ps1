Param(
  [string]$ServiceAccountFile,
  [string]$DriveFolderId,
  [int]$ChunkSize = 500,
  [int]$ChunkOverlap = 50,
  [switch]$Force
)

# Rutas relativas basadas en la ubicación de este script
$backendDir = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $backendDir

# Auto-detección de credentials.json en rutas relativas comunes
$candidateCreds = @(
  (Join-Path $repoRoot "credentials.json"),
  (Join-Path $backendDir "credentials.json")
)

if ([string]::IsNullOrWhiteSpace($ServiceAccountFile)) {
  foreach ($c in $candidateCreds) {
    if (Test-Path -LiteralPath $c) { $ServiceAccountFile = $c; break }
  }
}

if (-not (Test-Path -LiteralPath $ServiceAccountFile)) {
  Write-Error "No se encontró credentials.json. Colócalo en 'credentials.json' (raíz del repo) o 'backend/credentials.json', o pasa -ServiceAccountFile .\credentials.json"
  exit 1
}

# DRIVE_FOLDER_ID puede venir por parámetro o variable de entorno
if ([string]::IsNullOrWhiteSpace($DriveFolderId)) {
  $DriveFolderId = $env:DRIVE_FOLDER_ID
}
if ([string]::IsNullOrWhiteSpace($DriveFolderId)) {
  Write-Error "DRIVE_FOLDER_ID es requerido. Pásalo con -DriveFolderId o define $env:DRIVE_FOLDER_ID"
  exit 1
}

# Variables de entorno necesarias para la vista de Django (usar path relativo al backend)
if ($ServiceAccountFile -eq (Join-Path $backendDir "credentials.json")) {
  $env:SERVICE_ACCOUNT_FILE = "credentials.json"
} elseif ($ServiceAccountFile -eq (Join-Path $repoRoot "credentials.json")) {
  $env:SERVICE_ACCOUNT_FILE = "..\credentials.json"
} else {
  # fallback si el archivo está en otra ubicación (no recomendada)
  $env:SERVICE_ACCOUNT_FILE = $ServiceAccountFile
}
$env:DRIVE_FOLDER_ID = $DriveFolderId
# Asegura que el backend use la base en la raíz del repo
$env:CHROMA_DIR = (Join-Path $repoRoot "chroma_db")

# Preparar flags
$forceFlag = if ($Force) { "--force" } else { "" }

Write-Host "Usando credentials: $([IO.Path]::GetFileName($ServiceAccountFile))"
Write-Host "Sync+Ingest desde Drive (chunk-size=$ChunkSize, chunk-overlap=$ChunkOverlap, force=$($Force.IsPresent))..."

# Ejecutar manage.py desde backend con rutas relativas
Push-Location $backendDir
try {
  python manage.py sync_drive_full --chunk-size $ChunkSize --chunk-overlap $ChunkOverlap $forceFlag
}
finally {
  Pop-Location
}