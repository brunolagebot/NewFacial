# NewFacial

Sistema moderno de reconhecimento facial utilizando InsightFace (ArcFace) com interface web e suporte a streams RTSP.

## Características

- 🔍 **Detecção e reconhecimento facial** usando InsightFace (ArcFace)
- 🎯 **Detecção de objetos e animais** com YOLOv8 (80+ classes)
- 🧠 **Análise contextual com LLM** (OpenAI GPT-4V ou Ollama local)
- 🎬 **Processamento de vídeo completo** incluindo YouTube com análise temporal
- 🌐 **Interface web moderna** com Bootstrap e JavaScript
- 📱 **API REST completa** documentada com FastAPI
- 🎥 **Suporte a streams RTSP** em tempo real
- 💾 **Banco de dados SQLite** para armazenar embeddings faciais
- 📊 **Dashboard com estatísticas** em tempo real
- 🖼️ **Suporte a múltiplos formatos** de imagem (JPG, PNG, BMP, TIFF, WebP)
- 🎨 **Detecção multimodal** combinando faces, objetos e análise inteligente

## Instalação

### Pré-requisitos

- Python 3.8+
- pip
- Câmera IP com suporte RTSP (opcional)

### Instalação Automática (Recomendada)

```bash
# Clone o repositório
git clone https://github.com/brunolagebot/NewFacial.git

# Entre no diretório
cd NewFacial

# Execute o setup automático (macOS/Linux)
./scripts/setup.sh

# Para Windows, use instalação manual abaixo
```

### Instalação Manual

```bash
# Crie um ambiente virtual
python3 -m venv .venv

# Ative o ambiente virtual
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt
```

## Uso

### Iniciando o servidor

#### Execução Automática (Recomendada)
```bash
# Script que ativa ambiente virtual automaticamente
./scripts/run.sh
```

#### Execução Manual
```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Método 1: Executando o arquivo main.py
python main.py

# Método 2: Usando uvicorn diretamente
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Acessando a aplicação

- **Interface Web**: http://localhost:8000
- **Documentação da API**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Configuração Opcional

#### Para Detecção de Objetos (YOLOv8)
```bash
pip install ultralytics
```

#### Para Análise LLM

**Opção 1: OpenAI API**
```bash
export OPENAI_API_KEY="sua_api_key_aqui"
```

**Opção 2: Ollama Local**
```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Baixar modelo multimodal
ollama pull llava
```

### Funcionalidades principais

1. **Cadastro de Pessoas**
   - Adicione pessoas ao sistema
   - Faça upload de múltiplas imagens para treinamento
   - Gerencie informações das pessoas cadastradas

2. **Reconhecimento de Imagens**
   - Envie imagens para reconhecimento facial
   - Visualize resultados com bounding boxes
   - Obtenha confiança do reconhecimento

3. **Streams RTSP**
   - Conecte câmeras IP via RTSP
   - Monitoramento em tempo real
   - Detecção automática de faces conhecidas

4. **Detecção Multimodal**
   - Detecte 80+ classes de objetos e animais
   - Análise contextual com LLM (GPT-4V/Ollama)
   - Combinação inteligente de faces + objetos
   - Anotação automática de imagens

5. **Processamento de Vídeo (Novo!)**
   - Upload de vídeos locais (MP4, AVI, MOV, MKV, etc.)
   - Download e processamento de vídeos do YouTube
   - Análise temporal com timeline de aparições
   - Geração de vídeos anotados com detecções
   - Relatórios detalhados (JSON, HTML, TXT)
   - Processamento assíncrono com monitoramento

6. **Logs e Estatísticas**
   - Visualize logs de detecções
   - Acompanhe estatísticas do sistema
   - Monitore performance dos streams

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## Contato

Bruno Lage - [bruno.lage@hotmail.com]

Link do Projeto: [https://github.com/brunolagebot/NewFacial](https://github.com/brunolagebot/NewFacial) 