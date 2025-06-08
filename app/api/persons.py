from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from pathlib import Path

from app.database.connection import get_db
from app.database.models import Person, FaceEmbedding
from app.models.schemas import PersonCreate, PersonUpdate, PersonResponse, ImageUploadResponse, GenericResponse
from app.services.face_recognition import face_service
from app.config import UPLOADS_DIR, ALLOWED_EXTENSIONS

router = APIRouter(prefix="/persons", tags=["persons"])

@router.post("/", response_model=PersonResponse)
def create_person(person: PersonCreate, db: Session = Depends(get_db)):
    """Cria uma nova pessoa no banco de dados"""
    # Verificar se já existe pessoa com mesmo nome
    existing_person = db.query(Person).filter(Person.name == person.name).first()
    if existing_person:
        raise HTTPException(status_code=400, detail="Pessoa com este nome já existe")
    
    db_person = Person(**person.dict())
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    
    return db_person

@router.get("/", response_model=List[PersonResponse])
def list_persons(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista todas as pessoas cadastradas"""
    persons = db.query(Person).filter(Person.is_active == True).offset(skip).limit(limit).all()
    return persons

@router.get("/{person_id}", response_model=PersonResponse)
def get_person(person_id: int, db: Session = Depends(get_db)):
    """Obtém uma pessoa específica por ID"""
    person = db.query(Person).filter(Person.id == person_id, Person.is_active == True).first()
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return person

@router.put("/{person_id}", response_model=PersonResponse)
def update_person(person_id: int, person_update: PersonUpdate, db: Session = Depends(get_db)):
    """Atualiza dados de uma pessoa"""
    person = db.query(Person).filter(Person.id == person_id, Person.is_active == True).first()
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    
    # Verificar se novo nome já existe (se fornecido)
    if person_update.name and person_update.name != person.name:
        existing_person = db.query(Person).filter(Person.name == person_update.name).first()
        if existing_person:
            raise HTTPException(status_code=400, detail="Nome já existe")
    
    # Atualizar campos fornecidos
    update_data = person_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(person, field, value)
    
    db.commit()
    db.refresh(person)
    return person

@router.delete("/{person_id}", response_model=GenericResponse)
def delete_person(person_id: int, db: Session = Depends(get_db)):
    """Remove uma pessoa (soft delete)"""
    person = db.query(Person).filter(Person.id == person_id, Person.is_active == True).first()
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    
    person.is_active = False
    db.commit()
    
    return GenericResponse(success=True, message="Pessoa removida com sucesso")

@router.post("/{person_id}/upload-images", response_model=ImageUploadResponse)
async def upload_person_images(
    person_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Faz upload de imagens para treinar reconhecimento de uma pessoa"""
    # Verificar se pessoa existe
    person = db.query(Person).filter(Person.id == person_id, Person.is_active == True).first()
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    
    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
    
    faces_detected = 0
    faces_added = 0
    detections = []
    
    # Criar diretório para a pessoa
    person_dir = UPLOADS_DIR / str(person_id)
    person_dir.mkdir(exist_ok=True)
    
    for file in files:
        # Verificar extensão do arquivo
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            continue
        
        # Salvar arquivo temporariamente
        temp_filename = f"{uuid.uuid4()}{file_ext}"
        temp_path = person_dir / temp_filename
        
        try:
            content = await file.read()
            with open(temp_path, "wb") as f:
                f.write(content)
            
            # Extrair embeddings das faces
            face_detections = face_service.extract_face_embedding(str(temp_path))
            
            for detection in face_detections:
                faces_detected += 1
                
                # Salvar embedding no banco de dados
                embedding_record = FaceEmbedding(
                    person_id=person_id,
                    image_path=str(temp_path),
                    confidence=detection['confidence']
                )
                embedding_record.set_embedding(detection['embedding'])
                
                db.add(embedding_record)
                faces_added += 1
                
                # Adicionar à lista de detecções
                bbox = detection['bbox']
                detections.append({
                    "bbox": {
                        "x1": int(bbox[0]),
                        "y1": int(bbox[1]),
                        "x2": int(bbox[2]),
                        "y2": int(bbox[3])
                    },
                    "confidence": detection['confidence'],
                    "age": detection.get('age'),
                    "gender": detection.get('gender')
                })
        
        except Exception as e:
            # Se houver erro, remover arquivo temporário
            if temp_path.exists():
                temp_path.unlink()
            continue
    
    db.commit()
    
    return ImageUploadResponse(
        success=True,
        message=f"Processamento concluído. {faces_added} faces adicionadas de {faces_detected} detectadas.",
        faces_detected=faces_detected,
        faces_added=faces_added,
        detections=detections
    )

@router.get("/{person_id}/embeddings")
def get_person_embeddings(person_id: int, db: Session = Depends(get_db)):
    """Lista todos os embeddings de uma pessoa"""
    person = db.query(Person).filter(Person.id == person_id, Person.is_active == True).first()
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    
    embeddings = db.query(FaceEmbedding).filter(FaceEmbedding.person_id == person_id).all()
    
    return {
        "person_id": person_id,
        "person_name": person.name,
        "total_embeddings": len(embeddings),
        "embeddings": [
            {
                "id": emb.id,
                "image_path": emb.image_path,
                "confidence": emb.confidence,
                "created_at": emb.created_at
            }
            for emb in embeddings
        ]
    } 