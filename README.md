# NewFacial

Sistema moderno de reconhecimento facial utilizando InsightFace (ArcFace) com interface web e suporte a streams RTSP.

## Características

- 🔍 **Detecção e reconhecimento facial** usando InsightFace (ArcFace)
- 🌐 **Interface web moderna** com Bootstrap e JavaScript
- 📱 **API REST completa** documentada com FastAPI
- 🎥 **Suporte a streams RTSP** em tempo real
- 💾 **Banco de dados SQLite** para armazenar embeddings faciais
- 📊 **Dashboard com estatísticas** em tempo real
- 🖼️ **Suporte a múltiplos formatos** de imagem (JPG, PNG, BMP, TIFF, WebP)

## Instalação

### Pré-requisitos

- Python 3.8+
- pip
- Câmera IP com suporte RTSP (opcional)

### Passos de instalação

```bash
# Clone o repositório
git clone https://github.com/brunolagebot/NewFacial.git

# Entre no diretório
cd NewFacial

# Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt
```

## Uso

### Iniciando o servidor

```bash
# Método 1: Usando uvicorn diretamente
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Método 2: Executando o arquivo main.py
python main.py
```

### Acessando a aplicação

- **Interface Web**: http://localhost:8000
- **Documentação da API**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

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

4. **Logs e Estatísticas**
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