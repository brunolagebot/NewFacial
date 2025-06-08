from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Esquemas para Person
class PersonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class PersonCreate(PersonBase):
    pass

class PersonUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class PersonResponse(PersonBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Esquemas para detecção de faces
class BoundingBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int

class FaceDetection(BaseModel):
    bbox: BoundingBox
    confidence: float
    age: Optional[int] = None
    gender: Optional[int] = None

class FaceRecognitionResult(BaseModel):
    person_id: Optional[int] = None
    person_name: Optional[str] = None
    confidence: float
    bbox: BoundingBox

class ImageUploadResponse(BaseModel):
    success: bool
    message: str
    faces_detected: int
    faces_added: int
    detections: List[FaceDetection]

class ImageRecognitionResponse(BaseModel):
    success: bool
    message: str
    faces_detected: int
    recognitions: List[FaceRecognitionResult]

# Esquemas para RTSP
class RTSPStreamRequest(BaseModel):
    stream_id: str = Field(..., min_length=1, max_length=50)
    rtsp_url: str = Field(..., min_length=1)

class RTSPStreamInfo(BaseModel):
    stream_id: str
    rtsp_url: str
    active: bool
    fps: float
    frame_count: int
    uptime: float

class RTSPStreamResponse(BaseModel):
    success: bool
    message: str
    stream_info: Optional[RTSPStreamInfo] = None

# Esquemas para logs de detecção
class DetectionLogResponse(BaseModel):
    id: int
    person_id: Optional[int]
    person_name: Optional[str]
    confidence: float
    source: str
    source_info: Optional[str]
    detected_at: datetime
    bounding_box: Optional[dict]
    
    class Config:
        from_attributes = True

# Esquemas de resposta genérica
class GenericResponse(BaseModel):
    success: bool
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None

# Esquemas para estatísticas
class SystemStats(BaseModel):
    total_persons: int
    total_embeddings: int
    total_detections: int
    active_streams: int
    uptime: float 