Param(
  [string]$ServiceAccountFile = "",
  [string]$DriveFolderId = "1wAYnaln3Dg-MnFy6rNhwqPlh7Ouc4EP8",
  [int]$ChunkSize = 500,
  [int]$ChunkOverlap = 50
)

# Intento de auto-deteción del credentials.json en backend/ si no se pasó por parámetro
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$defaultCreds = Join-Path $repoRoot "backend\credentials.json"
if ([string]::IsNullOrWhiteSpace($ServiceAccountFile) -or -not (Test-Path -LiteralPath $ServiceAccountFile)) {
  if (Test-Path -LiteralPath $defaultCreds) {
    $ServiceAccountFile = $defaultCreds
  }
}
if (-not (Test-Path -LiteralPath $ServiceAccountFile)) {
  Write-Error "No se encontró el archivo de credenciales de Google. Pasa -ServiceAccountFile \"C:\\ruta\\a\\service_account.json\" o coloca backend\\credentials.json"
  exit 1
}

if ([string]::IsNullOrWhiteSpace($DriveFolderId)) {
  Write-Error "DRIVE_FOLDER_ID es requerido. Ejemplo: 1wAYnaln3Dg-MnFy6rNhwqPlh7Ouc4EP8"
  exit 1
}

$env:USE_SQLITE = "0"
$env:DB_HOST = "127.0.0.1"
$env:DB_PORT = "3306"
$env:DB_NAME = "rag"
$env:DB_USER = "rag_user"
$env:DB_PASSWORD = "strong_password"
$env:SERVICE_ACCOUNT_FILE = $ServiceAccountFile
$env:DRIVE_FOLDER_ID = $DriveFolderId

Write-Host "Sync+Ingest desde Drive..."
python manage.py sync_drive_full --chunk-size $ChunkSize --chunk-overlap $ChunkOverlap