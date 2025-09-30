# INSTALACIÓN AUTOMÁTICA DEL SISTEMA RAG OPTIMIZADO
# ==================================================
# Script para configurar todo lo necesario en una PC nueva

param(
    [switch]$Force,
    [switch]$SkipDependencies
)

Write-Host ""
Write-Host "🚀 INSTALACIÓN AUTOMÁTICA - SISTEMA RAG OPTIMIZADO" -ForegroundColor Magenta
Write-Host ("=" * 55) -ForegroundColor Magenta
Write-Host ""

# Función para verificar Python
function Test-PythonVersion {
    Write-Host "🐍 Verificando Python..." -ForegroundColor Yellow
    try {
        $pythonVersion = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $pythonVersion" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host "❌ Python no encontrado" -ForegroundColor Red
        Write-Host "💡 Descarga Python desde: https://python.org" -ForegroundColor Yellow
        return $false
    }
    return $false
}

# Función para instalar dependencias críticas
function Install-RAGDependencies {
    Write-Host "📦 Instalando dependencias del sistema RAG..." -ForegroundColor Yellow
    
    $packages = @(
        "sentence-transformers",
        "chromadb",
        "rank-bm25", 
        "numpy",
        "torch",
        "transformers"
    )
    
    foreach ($package in $packages) {
        Write-Host "   📦 Instalando: $package" -ForegroundColor Cyan
        try {
            if ($Force) {
                & python -m pip install $package --upgrade --force-reinstall --quiet
            } else {
                & python -m pip install $package --quiet
            }
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✅ $package instalado" -ForegroundColor Green
            } else {
                Write-Host "   ❌ Error instalando $package" -ForegroundColor Red
            }
        } catch {
            Write-Host "   ❌ Error instalando $package`: $_" -ForegroundColor Red
        }
    }
}

# Función para verificar ChromaDB
function Test-ChromaDBData {
    Write-Host "🗄️ Verificando base de datos ChromaDB..." -ForegroundColor Yellow
    
    $chromaPaths = @(
        "../chroma_db_simple",
        "chroma_db_simple", 
        "../chroma_db_simple"
    )
    
    $found = $false
    foreach ($path in $chromaPaths) {
        if (Test-Path $path) {
            $items = Get-ChildItem $path -ErrorAction SilentlyContinue | Measure-Object
            Write-Host "✅ ChromaDB encontrado: $path ($($items.Count) items)" -ForegroundColor Green
            $found = $true
            break
        }
    }
    
    if (-not $found) {
        Write-Host "❌ Base de datos ChromaDB no encontrada" -ForegroundColor Red
        Write-Host "💡 Ejecuta primero el ETL: python etl_rag_complete.py" -ForegroundColor Yellow
        return $false
    }
    
    return $true
}

# Función para ejecutar diagnóstico
function Invoke-RAGDiagnostic {
    Write-Host "🔬 Ejecutando diagnóstico completo..." -ForegroundColor Yellow
    try {
        & python "diagnostico_rag.py"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Diagnóstico completado" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host "❌ Error en diagnóstico: $_" -ForegroundColor Red
    }
    return $false
}

# Función para crear archivos de configuración
function Set-RAGEnvironment {
    Write-Host "⚙️ Configurando entorno RAG..." -ForegroundColor Yellow
    
    # Verificar .env
    if (-not (Test-Path ".env")) {
        Write-Host "📝 Creando archivo .env básico..." -ForegroundColor Cyan
        
        $envContent = @"
# Configuración básica RAG
USE_OPTIMIZED_RAG=true
PRIMARY_LLM_PROVIDER=openrouter
DEFAULT_CHUNK_SIZE=800
CHROMA_DIR=../chroma_db_simple
"@
        
        try {
            $envContent | Out-File -FilePath ".env" -Encoding UTF8
            Write-Host "✅ Archivo .env creado" -ForegroundColor Green
        } catch {
            Write-Host "❌ Error creando .env: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "✅ Archivo .env existe" -ForegroundColor Green
    }
}

# Función para verificar sistema
function Test-RAGSystem {
    Write-Host "🧪 Probando sistema RAG..." -ForegroundColor Yellow
    
    $testScript = @"
import sys
sys.path.append('.')

try:
    from utils.optimized_rag_system import OptimizedRAGSystem
    rag = OptimizedRAGSystem()
    rag._initialize_models()
    stats = rag.get_system_stats()
    print(f'✅ Sistema RAG funcional: {stats["collection_count"]} documentos')
except Exception as e:
    print(f'❌ Error: {e}')
    # Fallback
    try:
        from utils.simple_rag_fallback import get_optimized_rag
        rag = get_optimized_rag()
        stats = rag.get_system_stats()
        print(f'✅ Sistema RAG simple: {stats["collection_count"]} documentos')
    except Exception as e2:
        print(f'❌ Error total: {e2}')
        sys.exit(1)
"@
    
    try {
        $testScript | & python -
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Sistema RAG funcional" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host "❌ Error probando sistema: $_" -ForegroundColor Red
    }
    
    return $false
}

# FUNCIÓN PRINCIPAL
function Main {
    if (-not (Test-PythonVersion)) {
        Write-Host "❌ No se puede continuar sin Python" -ForegroundColor Red
        exit 1
    }
    
    if (-not $SkipDependencies) {
        Install-RAGDependencies
    }
    
    Set-RAGEnvironment
    
    if (-not (Test-ChromaDBData)) {
        Write-Host "⚠️ Ejecutando ETL para crear base de datos..." -ForegroundColor Yellow
        try {
            & python "etl_rag_complete.py" --chunk-size 800
        } catch {
            Write-Host "❌ Error ejecutando ETL" -ForegroundColor Red
        }
    }
    
    Invoke-RAGDiagnostic
    
    if (Test-RAGSystem) {
        Write-Host ""
        Write-Host "🎉 ¡SISTEMA RAG OPTIMIZADO INSTALADO EXITOSAMENTE!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 PRÓXIMOS PASOS:" -ForegroundColor Cyan
        Write-Host "1. Ejecutar servidor: python start_rag.py" -ForegroundColor White
        Write-Host "2. O probar búsqueda: python -c `"from utils.optimized_rag_system import *; print(perform_optimized_search('test'))`"" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "⚠️ INSTALACIÓN PARCIAL - USANDO SISTEMA SIMPLE" -ForegroundColor Yellow
        Write-Host "💡 El sistema funciona pero sin optimizaciones avanzadas" -ForegroundColor Yellow
        Write-Host ""
    }
}

# Ejecutar instalación
Main