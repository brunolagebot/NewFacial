# Changelog - NewFacial

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Não Lançado]
### Planejado
- Scripts de ativação automática do ambiente virtual
- Testes automatizados
- Docker containerization
- Melhorias de performance

## [v1.0.0] - 2024-01-16

### Adicionado
- ✨ Sistema completo de reconhecimento facial usando InsightFace (ArcFace)
- 🌐 Interface web moderna com Bootstrap 5 e JavaScript
- 📱 API REST completa documentada com FastAPI/Swagger
- 🎥 Suporte a streams RTSP em tempo real
- 💾 Banco de dados SQLite com SQLAlchemy para embeddings faciais
- 📊 Dashboard com estatísticas em tempo real
- 🖼️ Suporte a múltiplos formatos de imagem (JPG, PNG, BMP, TIFF, WebP)
- 👥 Sistema de gerenciamento de pessoas
- 📝 Sistema de logs de detecções
- 🔄 Upload de múltiplas imagens para treinamento
- 🎯 Reconhecimento facial com bounding boxes
- 📺 Visualização de streams MJPEG
- ⚡ Processamento em tempo real com threads

### Implementado
- **Backend FastAPI** (`main.py`)
- **Serviços de reconhecimento** (`app/services/face_recognition.py`)
- **Processamento RTSP** (`app/services/rtsp_service.py`)
- **APIs REST** (`app/api/persons.py`, `app/api/recognition.py`, `app/api/rtsp.py`)
- **Modelos de dados** (`app/database/models.py`)
- **Esquemas Pydantic** (`app/models/schemas.py`)
- **Interface web interativa** (`app/templates/index.html`, `app/static/js/app.js`)
- **Configurações centralizadas** (`app/config.py`)

### Configurado
- Estrutura modular do projeto
- Ambiente virtual Python isolado
- Dependências em `requirements.txt`
- Repositório Git com .gitignore
- CORS para desenvolvimento
- Logging estruturado
- Tratamento de erros padronizado

## [v0.1.0] - 2024-01-16

### Adicionado
- 🎯 Configuração inicial do projeto
- 📄 README.md com documentação básica
- 🔧 .gitignore configurado
- 📦 Repositório Git inicializado
- 🔗 Repositório GitHub criado (https://github.com/brunolagebot/NewFacial)

---

## Tipos de Mudanças

- **Adicionado** para novas funcionalidades
- **Modificado** para mudanças em funcionalidades existentes
- **Descontinuado** para funcionalidades que serão removidas
- **Removido** para funcionalidades removidas
- **Corrigido** para correções de bugs
- **Segurança** para vulnerabilidades

## Padrão de Versionamento

- **MAJOR** (v1.0.0): Mudanças incompatíveis na API
- **MINOR** (v0.1.0): Novas funcionalidades compatíveis
- **PATCH** (v0.0.1): Correções de bugs compatíveis 