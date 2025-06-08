from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import json

Base = declarative_base()

class Person(Base):
    __tablename__ = "persons"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, nullable=False, index=True)
    embedding = Column(LargeBinary, nullable=False)  # Embedding vetorial serializado
    image_path = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def set_embedding(self, embedding_array):
        """Serializa o array numpy para armazenar no banco"""
        import numpy as np
        self.embedding = embedding_array.tobytes()
    
    def get_embedding(self):
        """Deserializa o embedding do banco para array numpy"""
        import numpy as np
        return np.frombuffer(self.embedding, dtype=np.float32)

class DetectionLog(Base):
    __tablename__ = "detection_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, nullable=True, index=True)  # None se pessoa não identificada
    confidence = Column(Float, nullable=False)
    source = Column(String, nullable=False)  # 'upload', 'rtsp', etc.
    source_info = Column(String, nullable=True)  # URL RTSP ou nome do arquivo
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    bounding_box = Column(String, nullable=True)  # JSON com coordenadas da face
    
    def set_bounding_box(self, x, y, w, h):
        """Define as coordenadas da bounding box"""
        self.bounding_box = json.dumps({"x": x, "y": y, "w": w, "h": h})
    
    def get_bounding_box(self):
        """Retorna as coordenadas da bounding box"""
        if self.bounding_box:
            return json.loads(self.bounding_box)
        return None 