from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
import time
import atexit

from app.config import APP_NAME, APP_VERSION, DEBUG
from app.database.connection import init_database, get_db
from app.database.models import Person, FaceEmbedding, DetectionLog
from app.api import persons, recognition, rtsp, multimodal
from app.services.rtsp_service import rtsp_processor
from app.models.schemas import SystemStats

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Sistema moderno de reconhecimento facial usando InsightFace (ArcFace)",
    debug=DEBUG
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configurar templates
templates = Jinja2Templates(directory="app/templates")

# Incluir routers das APIs
app.include_router(persons.router, prefix="/api")
app.include_router(recognition.router, prefix="/api")
app.include_router(rtsp.router, prefix="/api")
app.include_router(multimodal.router, prefix="/api")

# Variável para controlar tempo de início
start_time = time.time()

@app.on_event("startup")
async def startup_event():
    """Eventos executados na inicialização da aplicação"""
    logger.info("Iniciando NewFacial...")
    
    # Inicializar banco de dados
    try:
        init_database()
        logger.info("Banco de dados inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        raise
    
    # Inicializar serviços
    try:
        logger.info("Serviços inicializados com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar serviços: {e}")
        raise
    
    logger.info("NewFacial iniciado com sucesso!")

@app.on_event("shutdown")
async def shutdown_event():
    """Eventos executados no encerramento da aplicação"""
    logger.info("Encerrando NewFacial...")
    
    # Parar todos os streams RTSP
    rtsp_processor.shutdown()
    
    logger.info("NewFacial encerrado com sucesso")

# Registrar função de cleanup no exit
atexit.register(lambda: rtsp_processor.shutdown())

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página inicial da aplicação"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
async def health_check():
    """Endpoint de verificação de saúde da aplicação"""
    return {
        "status": "healthy",
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "timestamp": time.time()
    }

@app.get("/api/stats", response_model=SystemStats)
async def get_system_stats(db: Session = Depends(get_db)):
    """Retorna estatísticas do sistema"""
    # Contar registros no banco
    total_persons = db.query(Person).filter(Person.is_active == True).count()
    total_embeddings = db.query(FaceEmbedding).count()
    total_detections = db.query(DetectionLog).count()
    
    # Contar streams ativos
    active_streams = len(rtsp_processor.active_streams)
    
    # Calcular uptime
    uptime = time.time() - start_time
    
    return SystemStats(
        total_persons=total_persons,
        total_embeddings=total_embeddings,
        total_detections=total_detections,
        active_streams=active_streams,
        uptime=uptime
    )

@app.get("/api/logs")
async def get_detection_logs(
    skip: int = 0,
    limit: int = 100,
    person_id: int = None,
    db: Session = Depends(get_db)
):
    """Retorna logs de detecção"""
    query = db.query(DetectionLog, Person).outerjoin(
        Person, DetectionLog.person_id == Person.id
    ).order_by(DetectionLog.detected_at.desc())
    
    if person_id:
        query = query.filter(DetectionLog.person_id == person_id)
    
    logs = query.offset(skip).limit(limit).all()
    
    result = []
    for log, person in logs:
        log_data = {
            "id": log.id,
            "person_id": log.person_id,
            "person_name": person.name if person else "Desconhecido",
            "confidence": log.confidence,
            "source": log.source,
            "source_info": log.source_info,
            "detected_at": log.detected_at,
            "bounding_box": log.get_bounding_box()
        }
        result.append(log_data)
    
    return {
        "logs": result,
        "total": db.query(DetectionLog).count()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG,
        log_level="info"
    ) 