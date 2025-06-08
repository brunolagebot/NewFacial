#!/bin/bash

# NewFacial - Script de Setup Automático
# Compatível com macOS e Linux

set -e  # Para na primeira falha

echo "🎯 NewFacial - Sistema de Reconhecimento Facial"
echo "================================================"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se está no diretório correto
if [ ! -f "main.py" ]; then
    log_error "Execute este script no diretório raiz do projeto NewFacial"
    exit 1
fi

# Verificar Python
log_info "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 não encontrado. Instale Python 3.8+ primeiro"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
log_success "Python $PYTHON_VERSION encontrado"

# Verificar se versão é adequada
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    log_error "Python 3.8+ é necessário. Versão atual: $PYTHON_VERSION"
    exit 1
fi

# Criar ambiente virtual se não existir
if [ ! -d ".venv" ]; then
    log_info "Criando ambiente virtual..."
    python3 -m venv .venv
    log_success "Ambiente virtual criado"
else
    log_info "Ambiente virtual já existe"
fi

# Ativar ambiente virtual
log_info "Ativando ambiente virtual..."
source .venv/bin/activate

if [ "$VIRTUAL_ENV" ]; then
    log_success "Ambiente virtual ativado: $VIRTUAL_ENV"
else
    log_error "Falha ao ativar ambiente virtual"
    exit 1
fi

# Atualizar pip
log_info "Atualizando pip..."
pip install --upgrade pip

# Instalar dependências
log_info "Instalando dependências do NewFacial..."
pip install -r requirements.txt

# Verificar instalações críticas
log_info "Verificando instalações críticas..."

# FastAPI
python -c "import fastapi; print('✓ FastAPI:', fastapi.__version__)" 2>/dev/null || log_warning "FastAPI não instalado corretamente"

# InsightFace
python -c "import insightface; print('✓ InsightFace:', insightface.__version__)" 2>/dev/null || log_warning "InsightFace não instalado corretamente"

# OpenCV
python -c "import cv2; print('✓ OpenCV:', cv2.__version__)" 2>/dev/null || log_warning "OpenCV não instalado corretamente"

# YOLOv8 (opcional)
python -c "import ultralytics; print('✓ YOLOv8:', ultralytics.__version__)" 2>/dev/null || log_warning "YOLOv8 não instalado (detecção de objetos limitada)"

# Criar diretórios necessários
log_info "Criando diretórios necessários..."
mkdir -p uploads temp models docs

# Inicializar banco de dados
log_info "Inicializando banco de dados..."
python -c "
from app.database.connection import init_database
try:
    init_database()
    print('✓ Banco de dados inicializado')
except Exception as e:
    print(f'✗ Erro ao inicializar banco: {e}')
"

log_success "Setup concluído!"
echo ""
echo "🚀 Para iniciar a aplicação:"
echo "   source .venv/bin/activate"
echo "   python main.py"
echo ""
echo "🌐 Acesse: http://localhost:8000"
echo "📚 Docs:   http://localhost:8000/docs"
echo ""
echo "💡 Dicas:"
echo "   - Para detecção de objetos, instale: pip install ultralytics"
echo "   - Para análise LLM, configure OPENAI_API_KEY ou instale Ollama"
echo "   - Para RTSP, use URLs como: rtsp://camera_ip:554/stream" 