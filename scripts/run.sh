#!/bin/bash

# NewFacial - Script de Execução com Ativação Automática do Ambiente Virtual
# Compatível com macOS e Linux

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🎯 NewFacial - Iniciando Sistema${NC}"
echo "=================================="

# Verificar se está no diretório correto
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Execute este script no diretório raiz do projeto NewFacial${NC}"
    exit 1
fi

# Verificar se ambiente virtual existe
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Ambiente virtual não encontrado${NC}"
    echo "Execute primeiro: ./scripts/setup.sh"
    exit 1
fi

# Ativar ambiente virtual automaticamente
echo -e "${BLUE}🔄 Ativando ambiente virtual...${NC}"
source .venv/bin/activate

if [ "$VIRTUAL_ENV" ]; then
    echo -e "${GREEN}✅ Ambiente virtual ativado${NC}"
else
    echo -e "${RED}❌ Falha ao ativar ambiente virtual${NC}"
    exit 1
fi

# Verificar dependências críticas
echo -e "${BLUE}🔍 Verificando dependências...${NC}"
python -c "
import sys
try:
    import fastapi, uvicorn, insightface, cv2
    print('✅ Dependências principais OK')
except ImportError as e:
    print(f'❌ Dependência faltando: {e}')
    print('Execute: pip install -r requirements.txt')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Verificar YOLOv8 (opcional)
python -c "
try:
    import ultralytics
    print('✅ YOLOv8 disponível para detecção de objetos')
except ImportError:
    print('⚠️  YOLOv8 não instalado (detecção de objetos limitada)')
" 2>/dev/null

# Verificar LLM (opcional)
python -c "
import os
try:
    import openai
    if 'OPENAI_API_KEY' in os.environ:
        print('✅ OpenAI API configurada')
    else:
        print('⚠️  OpenAI API key não configurada')
except ImportError:
    print('⚠️  OpenAI não instalado')

# Verificar Ollama
import requests
try:
    response = requests.get('http://localhost:11434/api/tags', timeout=2)
    if response.status_code == 200:
        print('✅ Ollama disponível localmente')
except:
    print('⚠️  Ollama não disponível')
" 2>/dev/null

echo ""
echo -e "${GREEN}🚀 Iniciando NewFacial...${NC}"
echo ""

# Executar aplicação
python main.py 