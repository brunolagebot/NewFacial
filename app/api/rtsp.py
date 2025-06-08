from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import asyncio

from app.database.connection import get_db
from app.database.models import DetectionLog, Person
from app.models.schemas import RTSPStreamRequest, RTSPStreamResponse, RTSPStreamInfo, GenericResponse
from app.services.rtsp_service import rtsp_processor
from app.services.face_recognition import face_service

router = APIRouter(prefix="/rtsp", tags=["rtsp"])

async def detection_callback(stream_id: str, frame, detections, db: Session = None):
    """Callback chamado quando faces são detectadas em stream RTSP"""
    if not detections:
        return
    
    # Esta função seria chamada em contexto assíncrono
    # Por isso, seria necessário criar uma nova sessão de banco aqui
    # Para simplicidade, vamos pular o log automático por agora
    pass

@router.post("/streams", response_model=RTSPStreamResponse)
def add_rtsp_stream(stream_request: RTSPStreamRequest, db: Session = Depends(get_db)):
    """Adiciona um novo stream RTSP para monitoramento"""
    success = rtsp_processor.add_stream(
        stream_request.stream_id,
        stream_request.rtsp_url,
        callback=detection_callback
    )
    
    if success:
        stream_info_dict = rtsp_processor.get_stream_info(stream_request.stream_id)
        stream_info = RTSPStreamInfo(**stream_info_dict) if stream_info_dict else None
        
        return RTSPStreamResponse(
            success=True,
            message=f"Stream {stream_request.stream_id} adicionado com sucesso",
            stream_info=stream_info
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Falha ao adicionar stream. Verifique se o stream_id já existe ou se atingiu o limite máximo."
        )

@router.delete("/streams/{stream_id}", response_model=GenericResponse)
def remove_rtsp_stream(stream_id: str):
    """Remove um stream RTSP do monitoramento"""
    success = rtsp_processor.remove_stream(stream_id)
    
    if success:
        return GenericResponse(
            success=True,
            message=f"Stream {stream_id} removido com sucesso"
        )
    else:
        raise HTTPException(
            status_code=404,
            detail="Stream não encontrado"
        )

@router.get("/streams", response_model=List[RTSPStreamInfo])
def list_rtsp_streams():
    """Lista todos os streams RTSP ativos"""
    streams = rtsp_processor.list_streams()
    return [RTSPStreamInfo(**stream) for stream in streams]

@router.get("/streams/{stream_id}", response_model=RTSPStreamInfo)
def get_rtsp_stream_info(stream_id: str):
    """Obtém informações sobre um stream específico"""
    stream_info = rtsp_processor.get_stream_info(stream_id)
    
    if stream_info:
        return RTSPStreamInfo(**stream_info)
    else:
        raise HTTPException(
            status_code=404,
            detail="Stream não encontrado"
        )

@router.get("/streams/{stream_id}/frame")
def get_latest_frame(stream_id: str):
    """Obtém o último frame processado de um stream"""
    frame_bytes = rtsp_processor.get_latest_frame(stream_id)
    
    if frame_bytes:
        def generate():
            yield frame_bytes
        
        return StreamingResponse(
            generate(),
            media_type="image/jpeg",
            headers={"Content-Disposition": f"inline; filename={stream_id}_latest.jpg"}
        )
    else:
        raise HTTPException(
            status_code=404,
            detail="Stream não encontrado ou sem frames disponíveis"
        )

@router.get("/streams/{stream_id}/mjpeg")
def get_mjpeg_stream(stream_id: str):
    """Retorna stream MJPEG do processamento em tempo real"""
    def generate_mjpeg():
        while True:
            frame_bytes = rtsp_processor.get_latest_frame(stream_id)
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # Se não há frame, aguardar um pouco
                import time
                time.sleep(0.1)
    
    stream_info = rtsp_processor.get_stream_info(stream_id)
    if not stream_info:
        raise HTTPException(status_code=404, detail="Stream não encontrado")
    
    return StreamingResponse(
        generate_mjpeg(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.post("/streams/{stream_id}/test-connection")
def test_rtsp_connection(stream_id: str, rtsp_url: str):
    """Testa conexão com uma URL RTSP sem adicionar ao monitoramento"""
    import cv2
    
    try:
        cap = cv2.VideoCapture(rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not cap.isOpened():
            return {
                "success": False,
                "message": "Não foi possível conectar ao stream RTSP",
                "rtsp_url": rtsp_url
            }
        
        # Tentar ler um frame
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            height, width = frame.shape[:2]
            return {
                "success": True,
                "message": "Conexão RTSP bem-sucedida",
                "rtsp_url": rtsp_url,
                "resolution": f"{width}x{height}"
            }
        else:
            return {
                "success": False,
                "message": "Conectado ao stream mas não foi possível ler frames",
                "rtsp_url": rtsp_url
            }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao testar conexão: {str(e)}",
            "rtsp_url": rtsp_url
        } 