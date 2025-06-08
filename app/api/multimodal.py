from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import uuid
import cv2
import numpy as np
from pathlib import Path
from io import BytesIO

from app.database.connection import get_db
from app.database.models import DetectionLog, Person
from app.services.multimodal_detection import multimodal_service
from app.config import TEMP_DIR, ALLOWED_EXTENSIONS

router = APIRouter(prefix="/multimodal", tags=["multimodal detection"])

@router.post("/detect-comprehensive")
async def comprehensive_detection(
    file: UploadFile = File(...),
    include_llm_analysis: bool = True,
    db: Session = Depends(get_db)
):
    """
    Detecção completa: faces + objetos + animais + análise LLM
    
    Retorna:
    - Faces detectadas (InsightFace)
    - Objetos e animais (YOLOv8)  
    - Análise contextual (LLM)
    - Estatísticas resumidas
    """
    # Verificar extensão do arquivo
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Formato de arquivo não suportado")
    
    # Salvar arquivo temporariamente
    temp_filename = f"{uuid.uuid4()}{file_ext}"
    temp_path = TEMP_DIR / temp_filename
    
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Realizar detecção completa
        if include_llm_analysis:
            results = multimodal_service.comprehensive_detection(str(temp_path))
        else:
            # Apenas detecção visual, sem LLM
            image = cv2.imread(str(temp_path))
            results = {
                "image_path": str(temp_path),
                "faces": [],
                "objects": [],
                "analysis": {"analysis": "Análise LLM desabilitada"},
                "summary": {}
            }
            
            # Detectar objetos
            object_detections = multimodal_service.detect_objects_yolo(image)
            results["objects"] = object_detections
            
            # Detectar faces
            try:
                from app.services.face_recognition import face_service
                face_detections = face_service.detect_faces(image)
                results["faces"] = face_detections
            except Exception as e:
                results["faces"] = []
            
            # Gerar resumo
            results["summary"] = multimodal_service._generate_summary(results)
        
        # Log das detecções (opcional)
        try:
            for obj in results.get("objects", []):
                detection_log = DetectionLog(
                    person_id=None,
                    confidence=obj["confidence"],
                    source='multimodal_upload',
                    source_info=f"{obj['class']} - {file.filename}"
                )
                bbox = obj["bbox"]
                detection_log.set_bounding_box(
                    int(bbox[0]), int(bbox[1]), 
                    int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])
                )
                db.add(detection_log)
            
            db.commit()
        except Exception as e:
            # Log error but don't fail the request
            pass
        
        # Remover path temporário da resposta
        results.pop("image_path", None)
        
        return {
            "success": True,
            "message": f"Detecção completa realizada. {len(results.get('objects', []))} objetos e {len(results.get('faces', []))} faces detectadas.",
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")
    
    finally:
        # Remover arquivo temporário
        if temp_path.exists():
            temp_path.unlink()

@router.post("/detect-objects-only")
async def detect_objects_only(
    file: UploadFile = File(...),
    confidence_threshold: float = 0.5
):
    """
    Detecção apenas de objetos e animais (sem faces nem LLM)
    Mais rápido para quando só precisa de detecção de objetos
    """
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Formato de arquivo não suportado")
    
    temp_filename = f"{uuid.uuid4()}{file_ext}"
    temp_path = TEMP_DIR / temp_filename
    
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Carregar imagem
        image = cv2.imread(str(temp_path))
        if image is None:
            raise HTTPException(status_code=400, detail="Não foi possível processar a imagem")
        
        # Detectar apenas objetos
        detections = multimodal_service.detect_objects_yolo(image)
        
        # Filtrar por threshold
        filtered_detections = [
            d for d in detections 
            if d["confidence"] >= confidence_threshold
        ]
        
        # Estatísticas
        categories = {}
        for det in filtered_detections:
            cat = det.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "success": True,
            "message": f"{len(filtered_detections)} objetos detectados",
            "objects": filtered_detections,
            "statistics": {
                "total_objects": len(filtered_detections),
                "categories": categories,
                "confidence_threshold": confidence_threshold
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na detecção: {str(e)}")
    
    finally:
        if temp_path.exists():
            temp_path.unlink()

@router.post("/analyze-scene-with-llm")
async def analyze_scene_with_llm(
    file: UploadFile = File(...),
    custom_prompt: str = None
):
    """
    Análise de cena focada no LLM
    Permite prompt customizado para análises específicas
    """
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Formato de arquivo não suportado")
    
    # Verificar se LLM está disponível
    if not multimodal_service.llm_available:
        raise HTTPException(
            status_code=503, 
            detail="LLM não disponível. Configure OpenAI API ou instale Ollama"
        )
    
    temp_filename = f"{uuid.uuid4()}{file_ext}"
    temp_path = TEMP_DIR / temp_filename
    
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Se tem prompt customizado, usar diretamente
        if custom_prompt:
            try:
                analysis = multimodal_service._try_llm_analysis(str(temp_path), custom_prompt)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro na análise LLM: {str(e)}")
        else:
            # Análise padrão com detecções
            image = cv2.imread(str(temp_path))
            detections = multimodal_service.detect_objects_yolo(image)
            analysis = multimodal_service.analyze_with_llm(str(temp_path), detections)
        
        return {
            "success": True,
            "message": "Análise LLM concluída",
            "analysis": analysis,
            "custom_prompt_used": custom_prompt is not None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")
    
    finally:
        if temp_path.exists():
            temp_path.unlink()

@router.post("/detect-and-annotate")
async def detect_and_annotate(
    file: UploadFile = File(...),
    include_faces: bool = True,
    include_objects: bool = True
):
    """
    Detecta elementos e retorna imagem anotada com todas as detecções
    """
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Formato de arquivo não suportado")
    
    temp_filename = f"{uuid.uuid4()}{file_ext}"
    temp_path = TEMP_DIR / temp_filename
    
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Carregar imagem
        image = cv2.imread(str(temp_path))
        if image is None:
            raise HTTPException(status_code=400, detail="Não foi possível processar a imagem")
        
        results = {"faces": [], "objects": []}
        
        # Detectar conforme solicitado
        if include_objects:
            results["objects"] = multimodal_service.detect_objects_yolo(image)
        
        if include_faces:
            try:
                from app.services.face_recognition import face_service
                results["faces"] = face_service.detect_faces(image)
            except Exception as e:
                results["faces"] = []
        
        # Anotar imagem
        annotated_image = multimodal_service.draw_all_detections(image, results)
        
        # Converter para bytes
        _, img_encoded = cv2.imencode('.jpg', annotated_image)
        img_bytes = BytesIO(img_encoded.tobytes())
        
        return StreamingResponse(
            img_bytes,
            media_type="image/jpeg",
            headers={"Content-Disposition": "inline; filename=annotated_multimodal.jpg"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")
    
    finally:
        if temp_path.exists():
            temp_path.unlink()

@router.get("/supported-classes")
def get_supported_classes():
    """
    Retorna as classes de objetos que podem ser detectadas
    """
    # Classes do YOLOv8 COCO dataset
    yolo_classes = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
        'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
        'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
        'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
        'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
        'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
        'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
        'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
        'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
        'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'scissors', 'teddy bear', 'hair drier',
        'toothbrush'
    ]
    
    categories = {
        'animals': ['bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe'],
        'vehicles': ['bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat'],
        'people': ['person'],
        'objects': [c for c in yolo_classes if c not in ['person', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat']]
    }
    
    return {
        "yolo_available": multimodal_service.yolo_model is not None,
        "llm_available": multimodal_service.llm_available,
        "total_classes": len(yolo_classes),
        "classes_by_category": categories,
        "all_classes": sorted(yolo_classes)
    }

@router.get("/service-status")
def get_service_status():
    """
    Status dos serviços de detecção disponíveis
    """
    return {
        "yolo_model_loaded": multimodal_service.yolo_model is not None,
        "llm_available": multimodal_service.llm_available,
        "face_detection_available": True,  # InsightFace sempre disponível
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": 10,
        "services": {
            "object_detection": "YOLOv8" if multimodal_service.yolo_model else "Não disponível",
            "face_detection": "InsightFace ArcFace",
            "llm_analysis": "OpenAI/Ollama" if multimodal_service.llm_available else "Não disponível"
        }
    } 