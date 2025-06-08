# Estrutura do Projeto NewFacial

## Hierarquia de Diretórios

```
NewFacial/
├── app/                    # Aplicação principal
│   ├── api/               # Rotas da API REST
│   │   ├── __init__.py
│   │   ├── persons.py     # Gerenciamento de pessoas
│   │   ├── recognition.py # Reconhecimento facial
│   │   └── rtsp.py        # Streams RTSP
│   ├── database/          # Modelos e conexão BD
│   │   ├── __init__.py
│   │   ├── connection.py  # Configuração SQLAlchemy
│   │   └── models.py      # Modelos de dados
│   ├── models/            # Esquemas Pydantic
│   │   ├── __init__.py
│   │   └── schemas.py     # Validação de dados
│   ├── services/          # Lógica de negócio
│   │   ├── __init__.py
│   │   ├── face_recognition.py # InsightFace ArcFace
│   │   └── rtsp_service.py     # Processamento RTSP
│   ├── static/            # Arquivos estáticos
│   │   ├── css/          # Estilos CSS
│   │   └── js/           # JavaScript
│   │       └── app.js    # Interface interativa
│   ├── templates/         # Templates HTML
│   │   └── index.html    # Interface principal
│   ├── __init__.py
│   └── config.py         # Configurações centralizadas
├── cursor/               # Regras do projeto
│   └── rules/           # Regras automatizadas
├── docs/                # Documentação obrigatória
│   ├── structure.md     # Este arquivo
│   ├── changelog.md     # Histórico de mudanças
│   ├── roadmap.md       # Planejamento futuro
│   ├── routes.md        # Documentação das rotas
│   ├── constants.md     # Constantes do sistema
│   └── dependencies.md  # Dependências externas
├── uploads/             # Imagens enviadas
├── temp/                # Arquivos temporários
├── .venv/              # Ambiente virtual Python
├── main.py             # Aplicação FastAPI principal
├── requirements.txt    # Dependências Python
├── .gitignore         # Arquivos ignorados pelo Git
└── README.md          # Documentação principal
```

## Convenções de Nomenclatura

### Arquivos e Diretórios
- **snake_case** para nomes de arquivos Python
- **kebab-case** para diretórios quando necessário
- **PascalCase** para classes
- **snake_case** para variáveis e funções

### Estrutura de Código
- Máximo **150 linhas por arquivo**
- Princípio de **responsabilidade única** (SRP)
- Modularização obrigatória para arquivos longos

## Padrões de Organização

### API (app/api/)
Cada arquivo de rota deve conter:
- Máximo 5-7 endpoints relacionados
- Validação com Pydantic
- Documentação OpenAPI integrada
- Tratamento de erros padronizado

### Services (app/services/)
Lógica de negócio isolada:
- Classes com responsabilidade única
- Métodos públicos documentados
- Tratamento de exceções centralizado
- Interface consistente

### Database (app/database/)
Camada de dados padronizada:
- Modelos SQLAlchemy organizados
- Migrations quando necessário
- Conexões centralizadas

### Static/Templates (app/static/, app/templates/)
Interface web moderna:
- Bootstrap 5 para UI
- JavaScript modular
- CSS organizado por componentes

## Versionamento

- **Semantic Versioning** (v1.2.3)
- Tags de versão no Git
- Changelog atualizado por versão
- Branches nomeadas: `tipo/nome-funcionalidade`

## Ambiente Virtual

Obrigatório isolamento Python:
```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

## Dependências

Todas registradas em `requirements.txt`:
```bash
pip install -r requirements.txt
pip freeze > requirements.txt  # Após novas instalações
``` 