import cv2
import asyncio
import threading
import time
import logging
from typing import Dict, Optional, Callable
from app.services.face_recognition import face_service
from app.config import RTSP_TIMEOUT, MAX_CONCURRENT_STREAMS

logger = logging.getLogger(__name__)

class RTSPStreamProcessor:
    def __init__(self):
        self.active_streams: Dict[str, dict] = {}
        self.max_streams = MAX_CONCURRENT_STREAMS
        
    def add_stream(self, stream_id: str, rtsp_url: str, callback: Optional[Callable] = None) -> bool:
        """Adiciona um novo stream RTSP para processamento"""
        if len(self.active_streams) >= self.max_streams:
            logger.warning(f"Máximo de {self.max_streams} streams simultâneos atingido")
            return False
        
        if stream_id in self.active_streams:
            logger.warning(f"Stream {stream_id} já existe")
            return False
        
        try:
            cap = cv2.VideoCapture(rtsp_url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduzir buffer para menor latência
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            if not cap.isOpened():
                logger.error(f"Não foi possível conectar ao stream RTSP: {rtsp_url}")
                return False
            
            stream_info = {
                'rtsp_url': rtsp_url,
                'capture': cap,
                'active': True,
                'thread': None,
                'callback': callback,
                'last_frame': None,
                'fps': 0,
                'frame_count': 0,
                'start_time': time.time()
            }
            
            # Iniciar thread de processamento
            thread = threading.Thread(
                target=self._process_stream,
                args=(stream_id, stream_info),
                daemon=True
            )
            stream_info['thread'] = thread
            thread.start()
            
            self.active_streams[stream_id] = stream_info
            logger.info(f"Stream {stream_id} adicionado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar stream {stream_id}: {e}")
            return False
    
    def remove_stream(self, stream_id: str) -> bool:
        """Remove um stream RTSP do processamento"""
        if stream_id not in self.active_streams:
            return False
        
        try:
            stream_info = self.active_streams[stream_id]
            stream_info['active'] = False
            
            # Aguardar thread terminar
            if stream_info['thread']:
                stream_info['thread'].join(timeout=5)
            
            # Fechar captura
            if stream_info['capture']:
                stream_info['capture'].release()
            
            del self.active_streams[stream_id]
            logger.info(f"Stream {stream_id} removido com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover stream {stream_id}: {e}")
            return False
    
    def get_stream_info(self, stream_id: str) -> Optional[dict]:
        """Retorna informações sobre um stream"""
        if stream_id in self.active_streams:
            info = self.active_streams[stream_id]
            return {
                'stream_id': stream_id,
                'rtsp_url': info['rtsp_url'],
                'active': info['active'],
                'fps': info['fps'],
                'frame_count': info['frame_count'],
                'uptime': time.time() - info['start_time']
            }
        return None
    
    def list_streams(self) -> list:
        """Lista todos os streams ativos"""
        return [self.get_stream_info(stream_id) for stream_id in self.active_streams.keys()]
    
    def get_latest_frame(self, stream_id: str) -> Optional[bytes]:
        """Retorna o último frame processado de um stream"""
        if stream_id in self.active_streams:
            frame = self.active_streams[stream_id]['last_frame']
            if frame is not None:
                _, buffer = cv2.imencode('.jpg', frame)
                return buffer.tobytes()
        return None
    
    def _process_stream(self, stream_id: str, stream_info: dict):
        """Processa frames de um stream RTSP em loop"""
        cap = stream_info['capture']
        callback = stream_info['callback']
        frame_count = 0
        start_time = time.time()
        
        logger.info(f"Iniciando processamento do stream {stream_id}")
        
        try:
            while stream_info['active']:
                ret, frame = cap.read()
                
                if not ret:
                    logger.warning(f"Falha ao ler frame do stream {stream_id}")
                    time.sleep(0.1)
                    continue
                
                frame_count += 1
                current_time = time.time()
                
                # Calcular FPS
                if frame_count % 30 == 0:  # Atualizar FPS a cada 30 frames
                    elapsed = current_time - start_time
                    stream_info['fps'] = frame_count / elapsed if elapsed > 0 else 0
                
                stream_info['frame_count'] = frame_count
                
                # Processar detecção de faces a cada 5 frames (otimização)
                if frame_count % 5 == 0:
                    try:
                        detections = face_service.detect_faces(frame)
                        
                        if detections:
                            # Desenhar detecções no frame
                            frame_with_detections = face_service.draw_face_detection(frame, detections)
                            stream_info['last_frame'] = frame_with_detections
                            
                            # Chamar callback se fornecido
                            if callback:
                                asyncio.run_coroutine_threadsafe(
                                    callback(stream_id, frame, detections),
                                    asyncio.get_event_loop()
                                )
                        else:
                            stream_info['last_frame'] = frame
                            
                    except Exception as e:
                        logger.error(f"Erro ao processar frame do stream {stream_id}: {e}")
                        stream_info['last_frame'] = frame
                else:
                    stream_info['last_frame'] = frame
                
                # Pequena pausa para não sobrecarregar CPU
                time.sleep(0.03)  # ~33 FPS máximo
                
        except Exception as e:
            logger.error(f"Erro crítico no processamento do stream {stream_id}: {e}")
        finally:
            logger.info(f"Processamento do stream {stream_id} finalizado")
    
    def shutdown(self):
        """Para todos os streams e limpa recursos"""
        logger.info("Parando todos os streams RTSP...")
        stream_ids = list(self.active_streams.keys())
        for stream_id in stream_ids:
            self.remove_stream(stream_id)

# Instância global do processador RTSP
rtsp_processor = RTSPStreamProcessor() 