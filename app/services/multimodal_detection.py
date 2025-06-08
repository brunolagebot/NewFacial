import cv2
import numpy as np
import logging
import os
from typing import List, Dict, Optional, Tuple
from PIL import Image
import requests
import json
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

class MultiModalDetectionService:
    """
    Serviço avançado de detecção que combina:
    - Faces (InsightFace)
    - Objetos e animais (YOLOv8)
    - Análise contextual (LLM)
    """
    
    def __init__(self):
        self.yolo_model = None
        self.llm_available = False
        self.initialize_models()
    
    def initialize_models(self):
        """Inicializa modelos de detecção"""
        try:
            # Tentar importar YOLOv8
            from ultralytics import YOLO
            self.yolo_model = YOLO('yolov8n.pt')  # Modelo nano (rápido)
            logger.info("YOLOv8 inicializado com sucesso")
        except ImportError:
            logger.warning("YOLOv8 não disponível. Instale: pip install ultralytics")
        except Exception as e:
            logger.error(f"Erro ao inicializar YOLO: {e}")
        
        # Verificar disponibilidade de LLM
        self.check_llm_availability()
    
    def check_llm_availability(self):
        """Verifica se LLM está disponível (OpenAI, Ollama, etc.)"""
        try:
            import openai
            # Verificar se há API key configurada
            if hasattr(openai, 'api_key') or 'OPENAI_API_KEY' in os.environ:
                self.llm_available = True
                logger.info("OpenAI API disponível")
        except ImportError:
            logger.info("OpenAI não instalado")
        
        # Verificar Ollama local
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                self.llm_available = True
                logger.info("Ollama local disponível")
        except:
            pass
    
    def detect_objects_yolo(self, image: np.ndarray) -> List[Dict]:
        """Detecta objetos usando YOLOv8"""
        if not self.yolo_model:
            return []
        
        try:
            results = self.yolo_model(image, verbose=False)
            detections = []
            
            for r in results:
                for box in r.boxes:
                    if box.conf > 0.5:  # Threshold de confiança
                        detection = {
                            'type': 'object',
                            'class': r.names[int(box.cls)],
                            'confidence': float(box.conf),
                            'bbox': box.xyxy[0].tolist(),  # [x1, y1, x2, y2]
                            'category': self._get_category(r.names[int(box.cls)])
                        }
                        detections.append(detection)
            
            return detections
        except Exception as e:
            logger.error(f"Erro na detecção YOLO: {e}")
            return []
    
    def _get_category(self, class_name: str) -> str:
        """Categoriza objetos detectados"""
        animals = ['cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 
                  'zebra', 'giraffe', 'bird', 'person']
        vehicles = ['car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 
                   'boat', 'bicycle']
        objects = ['bottle', 'chair', 'couch', 'table', 'laptop', 'tv', 
                  'cell phone', 'book', 'clock', 'scissors']
        
        if class_name in animals:
            return 'animal' if class_name != 'person' else 'person'
        elif class_name in vehicles:
            return 'vehicle'
        else:
            return 'object'
    
    def analyze_with_llm(self, image_path: str, detections: List[Dict]) -> Dict:
        """Analisa cena usando LLM"""
        if not self.llm_available:
            return {"analysis": "LLM não disponível"}
        
        try:
            # Preparar contexto das detecções
            detection_summary = self._prepare_detection_summary(detections)
            
            # Tentar diferentes providers de LLM
            analysis = self._try_llm_analysis(image_path, detection_summary)
            return analysis
            
        except Exception as e:
            logger.error(f"Erro na análise LLM: {e}")
            return {"analysis": f"Erro na análise: {str(e)}"}
    
    def _prepare_detection_summary(self, detections: List[Dict]) -> str:
        """Prepara resumo das detecções para o LLM"""
        if not detections:
            return "Nenhuma detecção encontrada"
        
        summary = "Detecções na imagem:\n"
        
        # Agrupar por categoria
        categories = {}
        for det in detections:
            cat = det.get('category', 'unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(det)
        
        for category, items in categories.items():
            summary += f"\n{category.upper()}S ({len(items)}):\n"
            for item in items:
                conf = item.get('confidence', 0) * 100
                summary += f"- {item.get('class', 'unknown')} (confiança: {conf:.1f}%)\n"
        
        return summary
    
    def _try_llm_analysis(self, image_path: str, detection_summary: str) -> Dict:
        """Tenta análise com diferentes providers de LLM"""
        
        # Prompt para análise
        prompt = f"""
        Analise esta imagem com base nas seguintes detecções automáticas:
        
        {detection_summary}
        
        Forneça uma análise estruturada incluindo:
        1. Descrição geral da cena
        2. Principais elementos identificados
        3. Possíveis atividades ou contexto
        4. Interações entre elementos
        5. Observações interessantes
        
        Responda em formato JSON com as chaves: scene_description, main_elements, activities, interactions, observations
        """
        
        # Tentar Ollama primeiro (local)
        try:
            return self._analyze_with_ollama(prompt, image_path)
        except:
            pass
        
        # Tentar OpenAI
        try:
            return self._analyze_with_openai(prompt, image_path)
        except:
            pass
        
        return {"analysis": "Nenhum LLM disponível para análise"}
    
    def _analyze_with_ollama(self, prompt: str, image_path: str = None) -> Dict:
        """Análise usando Ollama local"""
        url = "http://localhost:11434/api/generate"
        
        payload = {
            "model": "llava",  # ou outro modelo multimodal
            "prompt": prompt,
            "stream": False
        }
        
        # Se imagem fornecida, converter para base64
        if image_path:
            with open(image_path, "rb") as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode()
                payload["images"] = [img_b64]
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return {"analysis": result.get("response", "Sem resposta")}
        else:
            raise Exception(f"Ollama error: {response.status_code}")
    
    def _analyze_with_openai(self, prompt: str, image_path: str = None) -> Dict:
        """Análise usando OpenAI GPT-4V"""
        import openai
        
        messages = [{"role": "user", "content": prompt}]
        
        # Se imagem fornecida, adicionar ao prompt
        if image_path:
            with open(image_path, "rb") as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode()
                messages[0]["content"] = [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                    }
                ]
        
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=messages,
            max_tokens=500
        )
        
        return {"analysis": response.choices[0].message.content}
    
    def comprehensive_detection(self, image_path: str) -> Dict:
        """Detecção completa: faces + objetos + análise LLM"""
        try:
            # Carregar imagem
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Não foi possível carregar a imagem")
            
            results = {
                "image_path": image_path,
                "faces": [],
                "objects": [],
                "analysis": {},
                "summary": {}
            }
            
            # 1. Detectar objetos com YOLO
            object_detections = self.detect_objects_yolo(image)
            results["objects"] = object_detections
            
            # 2. Detectar faces (usar serviço existente)
            try:
                from app.services.face_recognition import face_service
                face_detections = face_service.detect_faces(image)
                results["faces"] = face_detections
            except Exception as e:
                logger.error(f"Erro na detecção de faces: {e}")
            
            # 3. Análise com LLM
            all_detections = object_detections + [
                {"type": "face", "class": "person_face", "confidence": d["confidence"]}
                for d in results["faces"]
            ]
            
            llm_analysis = self.analyze_with_llm(image_path, all_detections)
            results["analysis"] = llm_analysis
            
            # 4. Resumo estatístico
            results["summary"] = self._generate_summary(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Erro na detecção completa: {e}")
            return {"error": str(e)}
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Gera resumo estatístico das detecções"""
        summary = {
            "total_faces": len(results.get("faces", [])),
            "total_objects": len(results.get("objects", [])),
            "categories": {},
            "confidence_avg": 0.0
        }
        
        # Contar por categoria
        for obj in results.get("objects", []):
            category = obj.get("category", "unknown")
            summary["categories"][category] = summary["categories"].get(category, 0) + 1
        
        # Calcular confiança média
        all_detections = results.get("objects", []) + results.get("faces", [])
        if all_detections:
            total_conf = sum(d.get("confidence", 0) for d in all_detections)
            summary["confidence_avg"] = total_conf / len(all_detections)
        
        return summary
    
    def draw_all_detections(self, image: np.ndarray, results: Dict) -> np.ndarray:
        """Desenha todas as detecções na imagem"""
        annotated_image = image.copy()
        
        # Cores para diferentes tipos
        colors = {
            'face': (0, 255, 0),      # Verde
            'person': (255, 0, 0),    # Azul
            'animal': (0, 255, 255),  # Amarelo
            'vehicle': (255, 0, 255), # Magenta
            'object': (0, 165, 255)   # Laranja
        }
        
        # Desenhar objetos
        for obj in results.get("objects", []):
            bbox = obj["bbox"]
            category = obj.get("category", "object")
            color = colors.get(category, (128, 128, 128))
            
            # Retângulo
            cv2.rectangle(annotated_image, 
                         (int(bbox[0]), int(bbox[1])), 
                         (int(bbox[2]), int(bbox[3])), 
                         color, 2)
            
            # Label
            label = f"{obj['class']} ({obj['confidence']:.2f})"
            cv2.putText(annotated_image, label, 
                       (int(bbox[0]), int(bbox[1] - 10)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Desenhar faces
        for face in results.get("faces", []):
            bbox = face["bbox"]
            color = colors["face"]
            
            cv2.rectangle(annotated_image,
                         (bbox[0], bbox[1]),
                         (bbox[2], bbox[3]),
                         color, 2)
            
            label = f"Face ({face['confidence']:.2f})"
            cv2.putText(annotated_image, label,
                       (bbox[0], bbox[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return annotated_image

# Instância global do serviço
multimodal_service = MultiModalDetectionService() 