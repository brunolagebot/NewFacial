# Constantes do Sistema - NewFacial

Documentação de todas as constantes, configurações e valores padrão utilizados no sistema.

## 📁 Configurações de Diretórios

### Localização: `app/config.py`

```python
# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
TEMP_DIR = BASE_DIR / "temp"
MODELS_DIR = BASE_DIR / "models"
```

| Constante | Valor | Descrição |
|-----------|-------|-----------|
| `BASE_DIR` | Diretório raiz do projeto | Diretório base calculado dinamicamente |
| `UPLOADS_DIR` | `{BASE_DIR}/uploads` | Armazenamento de imagens enviadas |
| `TEMP_DIR` | `{BASE_DIR}/temp` | Arquivos temporários de processamento |
| `MODELS_DIR` | `{BASE_DIR}/models` | Modelos de IA baixados |

---

## 🗄️ Configurações de Banco de Dados

```python
DATABASE_URL = "sqlite:///./face_recognition.db"
```

| Constante | Valor | Descrição |
|-----------|-------|-----------|
| `DATABASE_URL` | `sqlite:///./face_recognition.db` | URL de conexão SQLite |

---

## 📱 Configurações da Aplicação

```python
APP_NAME = "NewFacial - Sistema de Reconhecimento Facial"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
```

| Constante | Valor | Descrição |
|-----------|-------|-----------|
| `APP_NAME` | `"NewFacial - Sistema de Reconhecimento Facial"` | Nome da aplicação |
| `APP_VERSION` | `"1.0.0"` | Versão atual do sistema |
| `DEBUG` | Variável de ambiente ou `False` | Modo de debug |

---

## 🤖 Configurações do InsightFace

```python
INSIGHTFACE_MODEL = "buffalo_l"
FACE_DETECTION_THRESHOLD = 0.6
FACE_RECOGNITION_THRESHOLD = 0.4
```

| Constante | Valor | Descrição | Impacto |
|-----------|-------|-----------|---------|
| `INSIGHTFACE_MODEL` | `"buffalo_l"` | Modelo ArcFace utilizado | Precisão vs Performance |
| `FACE_DETECTION_THRESHOLD` | `0.6` | Threshold para detecção de faces | Mais baixo = mais detecções |
| `FACE_RECOGNITION_THRESHOLD` | `0.4` | Threshold para reconhecimento | Mais baixo = mais matches |

### Modelos Disponíveis
- `buffalo_l`: Modelo grande, alta precisão
- `buffalo_m`: Modelo médio, balanceado
- `buffalo_s`: Modelo pequeno, rápido

---

## 📤 Configurações de Upload

```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
```

| Constante | Valor | Descrição |
|-----------|-------|-----------|
| `MAX_FILE_SIZE` | `10485760` bytes (10MB) | Tamanho máximo por arquivo |
| `ALLOWED_EXTENSIONS` | `{".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}` | Formatos aceitos |

### Formatos Suportados
- **JPEG/JPG**: Formato mais comum, compressão com perda
- **PNG**: Suporte a transparência, sem perda
- **BMP**: Formato Windows, sem compressão
- **TIFF**: Formato profissional, alta qualidade
- **WebP**: Formato moderno do Google

---

## 📹 Configurações RTSP

```python
RTSP_TIMEOUT = 30
MAX_CONCURRENT_STREAMS = 5
```

| Constante | Valor | Descrição | Limitação |
|-----------|-------|-----------|-----------|
| `RTSP_TIMEOUT` | `30` segundos | Timeout para conexão RTSP | Evita travamentos |
| `MAX_CONCURRENT_STREAMS` | `5` streams | Máximo de streams simultâneos | Performance do servidor |

---

## 🎨 Configurações da Interface

### CSS Classes (Bootstrap)
```css
.navbar-brand { font-weight: bold; }
.card { border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.stats-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.upload-area { border: 2px dashed #ddd; border-radius: 10px; }
```

### JavaScript Intervals
```javascript
setInterval(() => this.loadStats(), 30000);    // 30 segundos
setInterval(() => this.loadStreams(), 10000);  // 10 segundos
setInterval(() => this.loadLogs(), 30000);     // 30 segundos
```

---

## 🔧 Configurações de Performance

### OpenCV Settings
```python
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer mínimo
cap.set(cv2.CAP_PROP_FPS, 30)        # 30 FPS máximo
```

### Processamento de Frames
```python
if frame_count % 5 == 0:  # Processa 1 a cada 5 frames
    # Detecção facial
time.sleep(0.03)  # ~33 FPS máximo
```

| Configuração | Valor | Descrição |
|--------------|-------|-----------|
| `BUFFER_SIZE` | `1` frame | Reduz latência |
| `MAX_FPS` | `30` fps | Controle de performance |
| `DETECTION_INTERVAL` | `5` frames | Otimização de CPU |
| `FRAME_DELAY` | `0.03` segundos | Controle de velocidade |

---

## 🌐 Configurações de Rede

### CORS Settings
```python
allow_origins=["*"]           # Desenvolvimento
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

### Server Settings
```python
host="0.0.0.0"    # Aceita conexões externas
port=8000         # Porta padrão
reload=DEBUG      # Auto-reload em desenvolvimento
```

---

## 📊 Limites e Thresholds

### Validação de Dados
```python
# Pessoa
name: min_length=1, max_length=100
description: Optional

# Stream RTSP
stream_id: min_length=1, max_length=50
rtsp_url: min_length=1

# Paginação
skip: default=0
limit: default=100, max=1000
```

### Processamento
```python
# Similaridade coseno
MIN_SIMILARITY = 0.4          # Threshold de reconhecimento
MAX_DETECTION_CONFIDENCE = 1.0 # Máxima confiança

# Logs
MAX_LOGS_DISPLAY = 10         # Logs na interface
LOG_RETENTION_DAYS = 30       # Retenção de logs
```

---

## 🔐 Configurações de Segurança

### Headers HTTP
```python
"Content-Disposition": "inline; filename=image.jpg"
"Content-Type": "application/json"
"Content-Type": "multipart/x-mixed-replace; boundary=frame"
```

### Validações
- Extensões de arquivo obrigatórias
- Tamanho máximo de upload
- Sanitização de nomes de arquivo
- Timeout em conexões externas

---

## 🧪 Configurações de Desenvolvimento

### Logging
```python
level=logging.INFO
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

### Debug Mode
```python
if DEBUG:
    uvicorn.run(reload=True, log_level="debug")
else:
    uvicorn.run(reload=False, log_level="info")
```

---

## 📈 Métricas e Monitoramento

### Performance Targets
- Reconhecimento: < 100ms por face
- Upload: < 5s para 10 imagens
- RTSP: < 200ms de latência
- API: < 50ms de resposta

### Capacidade
- Faces por pessoa: Ilimitado (recomendado 5-10)
- Pessoas no sistema: Ilimitado
- Streams simultâneos: 5 (configurável)
- Embeddings em memória: ~1000 (estimado)

---

## 🔄 Configurações de Atualização

### Intervalos de Refresh
- Interface: 30 segundos (stats e logs)
- Streams: 10 segundos (status)
- Health Check: 60 segundos (interno)

### Versionamento
- Major: Mudanças incompatíveis
- Minor: Novas funcionalidades
- Patch: Correções de bugs 