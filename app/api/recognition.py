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
from app.database.models import Person, FaceEmbedding, DetectionLog
from app.models.schemas import ImageRecognitionResponse, BoundingBox, FaceRecognitionResult
from app.services.face_recognition import face_service
from app.config import TEMP_DIR, ALLOWED_EXTENSIONS

router = APIRouter(prefix="/recognition", tags=["recognition"])

@router.post("/recognize-image", response_model=ImageRecognitionResponse)
async def recognize_faces_in_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Reconhece faces em uma imagem enviada"""
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
        
        # Detectar faces na imagem
        face_detections = face_service.extract_face_embedding(str(temp_path))
        
        if not face_detections:
            return ImageRecognitionResponse(
                success=True,
                message="Nenhuma face detectada na imagem",
                faces_detected=0,
                recognitions=[]
            )
        
        # Obter todos os embeddings conhecidos do banco
        known_embeddings = []
        embeddings_query = db.query(FaceEmbedding, Person).join(
            Person, FaceEmbedding.person_id == Person.id
        ).filter(Person.is_active == True).all()
        
        for embedding_record, person in embeddings_query:
            embedding_array = embedding_record.get_embedding()
            known_embeddings.append((person.id, person.name, embedding_array))
        
        recognitions = []
        
        # Processar cada face detectada
        for detection in face_detections:
            bbox = detection['bbox']
            bbox_obj = BoundingBox(
                x1=int(bbox[0]),
                y1=int(bbox[1]),
                x2=int(bbox[2]),
                y2=int(bbox[3])
            )
            
            # Tentar identificar a face
            if known_embeddings:
                # Comparar com embeddings conhecidos
                best_match = None
                best_confidence = 0.0
                
                for person_id, person_name, known_embedding in known_embeddings:
                    confidence = face_service.compare_embeddings(
                        detection['embedding'], 
                        known_embedding
                    )
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = (person_id, person_name)
                
                # Se encontrou match válido
                if best_match and best_confidence >= 0.4:  # Threshold de reconhecimento
                    person_id, person_name = best_match
                    
                    # Registrar log de detecção
                    detection_log = DetectionLog(
                        person_id=person_id,
                        confidence=best_confidence,
                        source='upload',
                        source_info=file.filename
                    )
                    detection_log.set_bounding_box(bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1])
                    db.add(detection_log)
                    
                    recognitions.append(FaceRecognitionResult(
                        person_id=person_id,
                        person_name=person_name,
                        confidence=best_confidence,
                        bbox=bbox_obj
                    ))
                else:
                    # Face não reconhecida
                    detection_log = DetectionLog(
                        person_id=None,
                        confidence=detection['confidence'],
                        source='upload',
                        source_info=file.filename
                    )
                    detection_log.set_bounding_box(bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1])
                    db.add(detection_log)
                    
                    recognitions.append(FaceRecognitionResult(
                        person_id=None,
                        person_name="Desconhecido",
                        confidence=detection['confidence'],
                        bbox=bbox_obj
                    ))
            else:
                # Não há pessoas cadastradas
                recognitions.append(FaceRecognitionResult(
                    person_id=None,
                    person_name="Desconhecido",
                    confidence=detection['confidence'],
                    bbox=bbox_obj
                ))
        
        db.commit()
        
        return ImageRecognitionResponse(
            success=True,
            message=f"Processamento concluído. {len(face_detections)} faces detectadas.",
            faces_detected=len(face_detections),
            recognitions=recognitions
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar imagem: {str(e)}")
    
    finally:
        # Remover arquivo temporário
        if temp_path.exists():
            temp_path.unlink()

@router.post("/recognize-image-annotated")
async def recognize_and_annotate_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Reconhece faces e retorna imagem anotada com detecções"""
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
        
        # Carregar imagem
        image = face_service.preprocess_image(str(temp_path))
        
        # Detectar faces
        face_detections = face_service.extract_face_embedding(str(temp_path))
        
        if face_detections:
            # Obter embeddings conhecidos
            known_embeddings = []
            embeddings_query = db.query(FaceEmbedding, Person).join(
                Person, FaceEmbedding.person_id == Person.id
            ).filter(Person.is_active == True).all()
            
            for embedding_record, person in embeddings_query:
                embedding_array = embedding_record.get_embedding()
                known_embeddings.append((person.id, person.name, embedding_array))
            
            # Anotar imagem com reconhecimentos
            annotated_image = image.copy()
            
            for detection in face_detections:
                bbox = detection['bbox']
                
                # Identificar pessoa se possível
                person_name = "Desconhecido"
                recognition_confidence = 0.0
                
                if known_embeddings:
                    best_match = None
                    best_confidence = 0.0
                    
                    for person_id, name, known_embedding in known_embeddings:
                        confidence = face_service.compare_embeddings(
                            detection['embedding'], 
                            known_embedding
                        )
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = name
                    
                    if best_match and best_confidence >= 0.4:
                        person_name = best_match
                        recognition_confidence = best_confidence
                
                # Desenhar retângulo e texto
                color = (0, 255, 0) if person_name != "Desconhecido" else (0, 0, 255)
                cv2.rectangle(annotated_image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                
                # Texto com nome e confiança
                text = f"{person_name}"
                if recognition_confidence > 0:
                    text += f" ({recognition_confidence:.2f})"
                
                # Calcular posição do texto
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                text_y = bbox[1] - 10 if bbox[1] - 10 > 10 else bbox[1] + text_size[1] + 10
                
                # Desenhar fundo do texto
                cv2.rectangle(annotated_image, 
                            (bbox[0], text_y - text_size[1] - 5),
                            (bbox[0] + text_size[0] + 5, text_y + 5),
                            color, -1)
                
                # Desenhar texto
                cv2.putText(annotated_image, text, (bbox[0] + 2, text_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        else:
            annotated_image = image
        
        # Converter para bytes
        _, img_encoded = cv2.imencode('.jpg', annotated_image)
        img_bytes = BytesIO(img_encoded.tobytes())
        
        return StreamingResponse(
            img_bytes,
            media_type="image/jpeg",
            headers={"Content-Disposition": "inline; filename=annotated_image.jpg"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar imagem: {str(e)}")
    
    finally:
        # Remover arquivo temporário
        if temp_path.exists():
            temp_path.unlink() 