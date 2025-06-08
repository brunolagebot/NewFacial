import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from typing import List, Tuple, Optional
import logging
from PIL import Image
from app.config import INSIGHTFACE_MODEL, FACE_DETECTION_THRESHOLD, FACE_RECOGNITION_THRESHOLD

logger = logging.getLogger(__name__)

class FaceRecognitionService:
    def __init__(self):
        self.app = None
        self.initialize_model()
    
    def initialize_model(self):
        """Inicializa o modelo InsightFace"""
        try:
            self.app = FaceAnalysis(name=INSIGHTFACE_MODEL)
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            logger.info(f"Modelo {INSIGHTFACE_MODEL} inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar modelo InsightFace: {e}")
            raise
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocessa imagem para análise"""
        try:
            # Tenta carregar com OpenCV primeiro
            img = cv2.imread(image_path)
            if img is None:
                # Se falhar, tenta com PIL
                pil_img = Image.open(image_path)
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            return img
        except Exception as e:
            logger.error(f"Erro ao preprocessar imagem {image_path}: {e}")
            raise
    
    def detect_faces(self, image: np.ndarray) -> List[dict]:
        """Detecta faces na imagem e extrai embeddings"""
        try:
            faces = self.app.get(image)
            results = []
            
            for face in faces:
                if face.det_score >= FACE_DETECTION_THRESHOLD:
                    bbox = face.bbox.astype(int)
                    result = {
                        'bbox': bbox,  # [x1, y1, x2, y2]
                        'confidence': float(face.det_score),
                        'embedding': face.embedding,
                        'landmark': face.landmark,
                        'age': getattr(face, 'age', None),
                        'gender': getattr(face, 'gender', None)
                    }
                    results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Erro na detecção de faces: {e}")
            return []
    
    def extract_face_embedding(self, image_path: str) -> List[dict]:
        """Extrai embeddings de todas as faces detectadas na imagem"""
        img = self.preprocess_image(image_path)
        return self.detect_faces(img)
    
    def compare_embeddings(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compara dois embeddings e retorna a similaridade (cosine similarity)"""
        try:
            # Normalizar embeddings
            embedding1 = embedding1 / np.linalg.norm(embedding1)
            embedding2 = embedding2 / np.linalg.norm(embedding2)
            
            # Calcular similaridade coseno
            similarity = np.dot(embedding1, embedding2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Erro ao comparar embeddings: {e}")
            return 0.0
    
    def identify_face(self, unknown_embedding: np.ndarray, known_embeddings: List[Tuple[int, np.ndarray]]) -> Optional[Tuple[int, float]]:
        """
        Identifica uma face comparando com embeddings conhecidos
        
        Args:
            unknown_embedding: Embedding da face desconhecida
            known_embeddings: Lista de tuplas (person_id, embedding)
        
        Returns:
            Tupla (person_id, confidence) se encontrado, None caso contrário
        """
        best_match = None
        best_confidence = 0.0
        
        for person_id, known_embedding in known_embeddings:
            confidence = self.compare_embeddings(unknown_embedding, known_embedding)
            
            if confidence > best_confidence and confidence >= FACE_RECOGNITION_THRESHOLD:
                best_confidence = confidence
                best_match = person_id
        
        if best_match is not None:
            return (best_match, best_confidence)
        
        return None
    
    def draw_face_detection(self, image: np.ndarray, detections: List[dict]) -> np.ndarray:
        """Desenha retângulos ao redor das faces detectadas"""
        img_copy = image.copy()
        
        for detection in detections:
            bbox = detection['bbox']
            confidence = detection['confidence']
            
            # Desenhar retângulo
            cv2.rectangle(img_copy, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
            
            # Adicionar texto com confiança
            text = f"{confidence:.2f}"
            cv2.putText(img_copy, text, (bbox[0], bbox[1] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return img_copy

# Instância global do serviço
face_service = FaceRecognitionService() 