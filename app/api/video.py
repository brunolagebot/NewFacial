from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import asyncio
from pathlib import Path
import json

from app.database.connection import get_db
from app.database.models import Person, FaceEmbedding, DetectionLog
from app.services.video_processing import video_service
from app.config import TEMP_DIR

router = APIRouter(prefix="/video", tags=["video processing"])

# Armazenamento temporário de jobs de processamento
processing_jobs = {}

@router.post("/process-upload")
async def process_uploaded_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    frame_interval: float = 1.0,
    max_frames: int = 300,
    generate_annotated: bool = True,
    report_format: str = "json",
    db: Session = Depends(get_db)
):
    """
    Processa arquivo de vídeo enviado para reconhecimento facial
    
    Args:
        file: Arquivo de vídeo
        frame_interval: Intervalo entre frames analisados (segundos)
        max_frames: Máximo de frames a processar
        generate_annotated: Se deve gerar vídeo anotado
        report_format: Formato do relatório (json, html, txt)
    
    Returns:
        Job ID para acompanhar o processamento
    """
    # Verificar formato do arquivo
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in video_service.supported_formats:
        raise HTTPException(
            status_code=400, 
            detail=f"Formato não suportado. Use: {', '.join(video_service.supported_formats)}"
        )
    
    # Salvar arquivo temporariamente
    job_id = str(uuid.uuid4())
    temp_filename = f"upload_{job_id}{file_ext}"
    temp_path = TEMP_DIR / temp_filename
    
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Registrar job de processamento
        processing_jobs[job_id] = {
            "status": "queued",
            "progress": 0,
            "video_path": str(temp_path),
            "original_filename": file.filename,
            "frame_interval": frame_interval,
            "max_frames": max_frames,
            "generate_annotated": generate_annotated,
            "report_format": report_format,
            "results": None,
            "annotated_video_path": None,
            "report_path": None,
            "error": None
        }
        
        # Processar em background
        background_tasks.add_task(
            _process_video_job, 
            job_id, 
            db
        )
        
        return {
            "success": True,
            "message": "Vídeo enviado para processamento",
            "job_id": job_id,
            "estimated_time_minutes": max_frames * 0.5 / 60,  # Estimativa
            "check_status_url": f"/api/video/job/{job_id}/status"
        }
    
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")

@router.post("/process-youtube")
async def process_youtube_video(
    background_tasks: BackgroundTasks,
    youtube_url: str = Form(...),
    quality: str = Form("720p"),
    frame_interval: float = Form(1.0),
    max_frames: int = Form(300),
    generate_annotated: bool = Form(True),
    report_format: str = Form("json"),
    db: Session = Depends(get_db)
):
    """
    Processa vídeo do YouTube para reconhecimento facial
    
    Args:
        youtube_url: URL do vídeo do YouTube
        quality: Qualidade do vídeo (720p, 480p, etc.)
        frame_interval: Intervalo entre frames analisados
        max_frames: Máximo de frames a processar
        generate_annotated: Se deve gerar vídeo anotado
        report_format: Formato do relatório
    """
    job_id = str(uuid.uuid4())
    
    # Registrar job
    processing_jobs[job_id] = {
        "status": "downloading",
        "progress": 0,
        "youtube_url": youtube_url,
        "quality": quality,
        "frame_interval": frame_interval,
        "max_frames": max_frames,
        "generate_annotated": generate_annotated,
        "report_format": report_format,
        "video_path": None,
        "results": None,
        "annotated_video_path": None,
        "report_path": None,
        "error": None
    }
    
    # Processar em background
    background_tasks.add_task(
        _process_youtube_job,
        job_id,
        db
    )
    
    return {
        "success": True,
        "message": "Download e processamento iniciados",
        "job_id": job_id,
        "youtube_url": youtube_url,
        "check_status_url": f"/api/video/job/{job_id}/status"
    }

@router.get("/job/{job_id}/status")
def get_job_status(job_id: str):
    """Verifica status de um job de processamento"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job = processing_jobs[job_id]
    
    response = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"]
    }
    
    if job["status"] == "completed":
        response.update({
            "results": job["results"],
            "download_urls": {
                "report": f"/api/video/job/{job_id}/download/report",
                "annotated_video": f"/api/video/job/{job_id}/download/video" if job["annotated_video_path"] else None
            }
        })
    elif job["status"] == "failed":
        response["error"] = job["error"]
    
    return response

@router.get("/job/{job_id}/download/report")
def download_report(job_id: str):
    """Baixa relatório do processamento"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job = processing_jobs[job_id]
    
    if job["status"] != "completed" or not job["report_path"]:
        raise HTTPException(status_code=400, detail="Relatório não disponível")
    
    report_path = Path(job["report_path"])
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo de relatório não encontrado")
    
    return FileResponse(
        path=str(report_path),
        filename=f"facial_recognition_report_{job_id}.{job['report_format']}",
        media_type="application/octet-stream"
    )

@router.get("/job/{job_id}/download/video")
def download_annotated_video(job_id: str):
    """Baixa vídeo anotado"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job = processing_jobs[job_id]
    
    if job["status"] != "completed" or not job["annotated_video_path"]:
        raise HTTPException(status_code=400, detail="Vídeo anotado não disponível")
    
    video_path = Path(job["annotated_video_path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo de vídeo não encontrado")
    
    return FileResponse(
        path=str(video_path),
        filename=f"annotated_video_{job_id}.mp4",
        media_type="video/mp4"
    )

@router.get("/jobs")
def list_jobs(limit: int = 20):
    """Lista jobs de processamento"""
    jobs_list = []
    
    for job_id, job in list(processing_jobs.items())[-limit:]:
        job_summary = {
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "created_at": job.get("created_at", "Unknown")
        }
        
        if "original_filename" in job:
            job_summary["source"] = f"Upload: {job['original_filename']}"
        elif "youtube_url" in job:
            job_summary["source"] = f"YouTube: {job['youtube_url']}"
        
        if job["status"] == "completed" and job["results"]:
            stats = job["results"]["statistics"]
            job_summary["summary"] = {
                "faces_detected": stats["total_faces_detected"],
                "unique_persons": len(stats["unique_persons_found"])
            }
        
        jobs_list.append(job_summary)
    
    return {
        "jobs": jobs_list,
        "total_active_jobs": len(processing_jobs)
    }

@router.delete("/job/{job_id}")
def cancel_job(job_id: str):
    """Cancela e remove um job de processamento"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job = processing_jobs[job_id]
    
    # Marcar como cancelado se ainda está processando
    if job["status"] in ["queued", "processing", "downloading"]:
        job["status"] = "cancelled"
    
    # Remover arquivos temporários
    if job.get("video_path"):
        try:
            Path(job["video_path"]).unlink()
        except:
            pass
    
    if job.get("annotated_video_path"):
        try:
            Path(job["annotated_video_path"]).unlink()
        except:
            pass
    
    if job.get("report_path"):
        try:
            Path(job["report_path"]).unlink()
        except:
            pass
    
    # Remover job da lista
    del processing_jobs[job_id]
    
    return {"success": True, "message": "Job cancelado e removido"}

@router.post("/cleanup")
def cleanup_old_jobs(older_than_hours: int = 24):
    """Remove jobs antigos e arquivos temporários"""
    import time
    
    cutoff_time = time.time() - (older_than_hours * 3600)
    removed_jobs = []
    
    for job_id, job in list(processing_jobs.items()):
        # Se não tem timestamp, considerar antigo
        job_time = job.get("created_at", 0)
        if isinstance(job_time, str):
            continue  # Pular se é string (mais recente)
        
        if job_time < cutoff_time:
            # Remover arquivos
            for path_key in ["video_path", "annotated_video_path", "report_path"]:
                if job.get(path_key):
                    try:
                        Path(job[path_key]).unlink()
                    except:
                        pass
            
            del processing_jobs[job_id]
            removed_jobs.append(job_id)
    
    # Cleanup geral de arquivos temporários
    video_service.cleanup_temp_files(older_than_hours)
    
    return {
        "success": True,
        "message": f"Removidos {len(removed_jobs)} jobs antigos",
        "removed_jobs": removed_jobs
    }

@router.get("/supported-formats")
def get_supported_formats():
    """Retorna formatos de vídeo suportados e limitações"""
    return {
        "video_formats": list(video_service.supported_formats),
        "youtube_supported": True,
        "max_file_size_mb": 100,  # Limite exemplo
        "max_duration_minutes": 30,  # Limite exemplo
        "recommended_settings": {
            "frame_interval": 1.0,
            "max_frames": 300,
            "quality": "720p"
        },
        "processing_capabilities": {
            "face_detection": True,
            "face_recognition": True,
            "video_annotation": True,
            "timeline_analysis": True,
            "report_generation": ["json", "html", "txt"]
        }
    }

# Funções auxiliares para processamento em background

async def _process_video_job(job_id: str, db: Session):
    """Processa job de vídeo local"""
    job = processing_jobs[job_id]
    
    try:
        job["status"] = "processing"
        job["progress"] = 10
        job["created_at"] = time.time()
        
        # Obter pessoas conhecidas do banco
        known_persons = []
        embeddings_query = db.query(FaceEmbedding, Person).join(
            Person, FaceEmbedding.person_id == Person.id
        ).filter(Person.is_active == True).all()
        
        for embedding_record, person in embeddings_query:
            known_persons.append({
                "id": person.id,
                "name": person.name,
                "embedding": embedding_record.get_embedding()
            })
        
        job["progress"] = 20
        
        # Processar vídeo
        results = video_service.process_video_faces(
            job["video_path"],
            known_persons,
            job["frame_interval"],
            job["max_frames"]
        )
        
        job["results"] = results
        job["progress"] = 70
        
        # Gerar relatório
        report_path = video_service.generate_report(results, job["report_format"])
        job["report_path"] = report_path
        job["progress"] = 80
        
        # Gerar vídeo anotado se solicitado
        if job["generate_annotated"]:
            annotated_path = video_service.create_annotated_video(
                job["video_path"], 
                results
            )
            job["annotated_video_path"] = annotated_path
        
        job["progress"] = 100
        job["status"] = "completed"
        
        # Salvar logs no banco (opcional)
        _save_detection_logs(results, db, f"upload_{job_id}")
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        logger.error(f"Erro no processamento do job {job_id}: {e}")

async def _process_youtube_job(job_id: str, db: Session):
    """Processa job de vídeo do YouTube"""
    job = processing_jobs[job_id]
    
    try:
        job["created_at"] = time.time()
        
        # Baixar vídeo
        job["status"] = "downloading"
        job["progress"] = 5
        
        video_path = video_service.download_youtube_video(
            job["youtube_url"],
            job["quality"]
        )
        
        job["video_path"] = video_path
        job["progress"] = 30
        
        # Continuar com processamento normal
        await _process_video_job(job_id, db)
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        logger.error(f"Erro no job YouTube {job_id}: {e}")

def _save_detection_logs(results: dict, db: Session, source: str):
    """Salva logs de detecção no banco de dados"""
    try:
        for frame_data in results["detections_by_frame"]:
            for face in frame_data["faces"]:
                recognition = face.get("recognition")
                
                detection_log = DetectionLog(
                    person_id=recognition["person_id"] if recognition else None,
                    confidence=recognition["confidence"] if recognition else face["confidence"],
                    source='video_processing',
                    source_info=f"{source} - timestamp: {frame_data['timestamp']:.1f}s"
                )
                
                bbox = face["bbox"]
                detection_log.set_bounding_box(
                    bbox[0], bbox[1], 
                    bbox[2] - bbox[0], bbox[3] - bbox[1]
                )
                
                db.add(detection_log)
        
        db.commit()
    except Exception as e:
        logger.warning(f"Erro ao salvar logs de detecção: {e}")

import time
import logging
logger = logging.getLogger(__name__) 