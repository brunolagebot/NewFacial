# Documentação das Rotas - NewFacial API

Documentação completa das rotas REST da API do sistema NewFacial.

## 🏠 Base URL
```
http://localhost:8000
```

---

## 📊 Rotas Principais

### Home e Saúde
| Método | Endpoint | Descrição | Resposta |
|--------|----------|-----------|----------|
| `GET` | `/` | Página inicial da aplicação | HTML |
| `GET` | `/api/health` | Verificação de saúde da API | JSON |
| `GET` | `/api/stats` | Estatísticas do sistema | JSON |
| `GET` | `/api/logs` | Logs de detecções | JSON |

---

## 👥 Gerenciamento de Pessoas

### Base: `/api/persons`

| Método | Endpoint | Descrição | Parâmetros | Resposta |
|--------|----------|-----------|------------|----------|
| `POST` | `/api/persons/` | Criar nova pessoa | Body: PersonCreate | PersonResponse |
| `GET` | `/api/persons/` | Listar pessoas | Query: skip, limit | Array[PersonResponse] |
| `GET` | `/api/persons/{person_id}` | Obter pessoa específica | Path: person_id | PersonResponse |
| `PUT` | `/api/persons/{person_id}` | Atualizar pessoa | Path: person_id, Body: PersonUpdate | PersonResponse |
| `DELETE` | `/api/persons/{person_id}` | Remover pessoa | Path: person_id | GenericResponse |

### Upload de Imagens
| Método | Endpoint | Descrição | Parâmetros | Resposta |
|--------|----------|-----------|------------|----------|
| `POST` | `/api/persons/{person_id}/upload-images` | Upload múltiplas imagens | Path: person_id, Files: images | ImageUploadResponse |
| `GET` | `/api/persons/{person_id}/embeddings` | Listar embeddings da pessoa | Path: person_id | JSON |

---

## 🔍 Reconhecimento Facial

### Base: `/api/recognition`

| Método | Endpoint | Descrição | Parâmetros | Resposta |
|--------|----------|-----------|------------|----------|
| `POST` | `/api/recognition/recognize-image` | Reconhecer faces em imagem | File: image | ImageRecognitionResponse |
| `POST` | `/api/recognition/recognize-image-annotated` | Imagem com anotações de faces | File: image | Image/JPEG |

---

## 🎥 Streams RTSP

### Base: `/api/rtsp`

| Método | Endpoint | Descrição | Parâmetros | Resposta |
|--------|----------|-----------|------------|----------|
| `POST` | `/api/rtsp/streams` | Adicionar stream RTSP | Body: RTSPStreamRequest | RTSPStreamResponse |
| `GET` | `/api/rtsp/streams` | Listar streams ativos | - | Array[RTSPStreamInfo] |
| `GET` | `/api/rtsp/streams/{stream_id}` | Info do stream | Path: stream_id | RTSPStreamInfo |
| `DELETE` | `/api/rtsp/streams/{stream_id}` | Remover stream | Path: stream_id | GenericResponse |
| `GET` | `/api/rtsp/streams/{stream_id}/frame` | Último frame do stream | Path: stream_id | Image/JPEG |
| `GET` | `/api/rtsp/streams/{stream_id}/mjpeg` | Stream MJPEG | Path: stream_id | Video/MJPEG |
| `POST` | `/api/rtsp/streams/{stream_id}/test-connection` | Testar conexão RTSP | Path: stream_id, Body: rtsp_url | JSON |

---

## 📝 Modelos de Dados

### PersonCreate
```json
{
  "name": "string",
  "description": "string (opcional)"
}
```

### PersonUpdate
```json
{
  "name": "string (opcional)",
  "description": "string (opcional)",
  "is_active": "boolean (opcional)"
}
```

### PersonResponse
```json
{
  "id": "integer",
  "name": "string",
  "description": "string",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### RTSPStreamRequest
```json
{
  "stream_id": "string",
  "rtsp_url": "string"
}
```

### ImageRecognitionResponse
```json
{
  "success": "boolean",
  "message": "string",
  "faces_detected": "integer",
  "recognitions": [
    {
      "person_id": "integer",
      "person_name": "string",
      "confidence": "float",
      "bbox": {
        "x1": "integer",
        "y1": "integer",
        "x2": "integer",
        "y2": "integer"
      }
    }
  ]
}
```

### SystemStats
```json
{
  "total_persons": "integer",
  "total_embeddings": "integer",
  "total_detections": "integer",
  "active_streams": "integer",
  "uptime": "float"
}
```

---

## 🔧 Códigos de Status HTTP

| Código | Descrição | Quando Ocorre |
|--------|-----------|---------------|
| `200` | Sucesso | Operação realizada com sucesso |
| `201` | Criado | Recurso criado com sucesso |
| `400` | Bad Request | Dados inválidos ou faltando |
| `404` | Not Found | Recurso não encontrado |
| `422` | Validation Error | Erro de validação Pydantic |
| `500` | Internal Error | Erro interno do servidor |

---

## 📋 Exemplos de Uso

### Criar Pessoa
```bash
curl -X POST "http://localhost:8000/api/persons/" \
     -H "Content-Type: application/json" \
     -d '{"name": "João Silva", "description": "Funcionário TI"}'
```

### Upload de Imagens
```bash
curl -X POST "http://localhost:8000/api/persons/1/upload-images" \
     -F "files=@foto1.jpg" \
     -F "files=@foto2.jpg"
```

### Reconhecimento Facial
```bash
curl -X POST "http://localhost:8000/api/recognition/recognize-image" \
     -F "file=@imagem_teste.jpg"
```

### Adicionar Stream RTSP
```bash
curl -X POST "http://localhost:8000/api/rtsp/streams" \
     -H "Content-Type: application/json" \
     -d '{"stream_id": "camera1", "rtsp_url": "rtsp://192.168.1.100:554/stream"}'
```

### Obter Estatísticas
```bash
curl -X GET "http://localhost:8000/api/stats"
```

---

## 🔍 Query Parameters

### Paginação
- `skip`: Número de registros para pular (default: 0)
- `limit`: Número máximo de registros (default: 100)

### Filtros
- `person_id`: Filtrar logs por pessoa específica

---

## 🎯 Content Types Suportados

### Upload de Imagens
- `image/jpeg`
- `image/png`
- `image/bmp`
- `image/tiff`
- `image/webp`

### Responses
- `application/json` (APIs REST)
- `text/html` (Interface web)
- `image/jpeg` (Frames e imagens anotadas)
- `multipart/x-mixed-replace` (MJPEG streams)

---

## 📚 Documentação Interativa

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json 