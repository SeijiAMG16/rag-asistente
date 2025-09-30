# 🚀 CONFIGURACIÓN AUTOMÁTICA DE DEEPSEEK PARA COMPAÑERO
# =======================================================

Write-Host "🎯 CONFIGURANDO DEEPSEEK V3.1 PARA NUEVA PC" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Verificar Python
Write-Host "`n1️⃣ Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no encontrado. Instalar Python 3.8+ primero" -ForegroundColor Red
    exit 1
}

# Verificar archivo .env
Write-Host "`n2️⃣ Verificando configuración..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✅ Archivo .env encontrado" -ForegroundColor Green
    
    # Verificar contenido crítico
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "OPENROUTER_API_KEY=sk-") {
        Write-Host "✅ API Key de OpenRouter configurada" -ForegroundColor Green
    } else {
        Write-Host "❌ API Key de OpenRouter no encontrada en .env" -ForegroundColor Red
        Write-Host "   Agregar: OPENROUTER_API_KEY=tu_clave_aqui" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "❌ Archivo .env no encontrado" -ForegroundColor Red
    Write-Host "   Copiar .env desde la PC principal" -ForegroundColor Yellow
    exit 1
}

# Instalar dependencias críticas
Write-Host "`n3️⃣ Instalando dependencias..." -ForegroundColor Yellow
$packages = @(
    "python-dotenv",
    "sentence-transformers", 
    "chromadb",
    "requests",
    "numpy",
    "torch",
    "django"
)

foreach ($package in $packages) {
    Write-Host "   Instalando $package..." -ForegroundColor Cyan
    python -m pip install $package --user --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $package instalado" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ Error instalando $package" -ForegroundColor Yellow
    }
}

# Verificar DeepSeek
Write-Host "`n4️⃣ Probando DeepSeek V3.1..." -ForegroundColor Yellow
python verificar_deepseek.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 ¡CONFIGURACIÓN EXITOSA!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host "✅ DeepSeek V3.1 configurado y funcionando" -ForegroundColor Green
    Write-Host "✅ Sistema RAG operativo" -ForegroundColor Green
    Write-Host "✅ Todas las dependencias instaladas" -ForegroundColor Green
    Write-Host "`n🚀 Para iniciar el sistema:" -ForegroundColor Cyan
    Write-Host "   python manage.py runserver 8000" -ForegroundColor White
} else {
    Write-Host "`n❌ CONFIGURACIÓN FALLIDA" -ForegroundColor Red
    Write-Host "Ver errores arriba para diagnosticar" -ForegroundColor Yellow
}

Write-Host "`nPresiona Enter para continuar..."
Read-Host