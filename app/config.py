import os
from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
TEMP_DIR = BASE_DIR / "temp"
MODELS_DIR = BASE_DIR / "models"

# Configurações do banco de dados
DATABASE_URL = "sqlite:///./face_recognition.db"

# Configurações da aplicação
APP_NAME = "NewFacial - Sistema de Reconhecimento Facial"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Configurações do InsightFace
INSIGHTFACE_MODEL = "buffalo_l"  # Modelo ArcFace
FACE_DETECTION_THRESHOLD = 0.6
FACE_RECOGNITION_THRESHOLD = 0.4

# Configurações de upload
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

# Configurações RTSP
RTSP_TIMEOUT = 30
MAX_CONCURRENT_STREAMS = 5

# Criar diretórios se não existirem
UPLOADS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True) 