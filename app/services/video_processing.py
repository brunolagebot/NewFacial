import cv2
import numpy as np
import logging
import os
import tempfile
import asyncio
from typing import List, Dict, Optional, Tuple, Generator
from pathlib import Path
import json
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VideoProcessingService:
    """
    Serviço para processamento de vídeos com reconhecimento facial
    Suporta:
    - URLs do YouTube
    - Arquivos de vídeo local
    - Extração de frames
    - Reconhecimento facial em batch
    - Geração de relatórios com timestamps
    - Criação de vídeos anotados
    """
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "newfacial_videos"
        self.temp_dir.mkdir(exist_ok=True)
        self.supported_formats = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v'}
    
    def download_youtube_video(self, url: str, quality: str = "720p") -> str:
        """
        Baixa vídeo do YouTube e retorna caminho do arquivo
        
        Args:
            url: URL do vídeo do YouTube
            quality: Qualidade desejada (720p, 480p, etc.)
        
        Returns:
            Caminho do arquivo baixado
        """
        try:
            import yt_dlp
        except ImportError:
            raise ImportError("yt-dlp não instalado. Execute: pip install yt-dlp")
        
        # Configurações do yt-dlp
        output_path = self.temp_dir / f"youtube_video_{int(time.time())}.%(ext)s"
        
        ydl_opts = {
            'format': f'best[height<={quality[:-1]}]',  # Remove 'p' de '720p'
            'outtmpl': str(output_path),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extrair informações do vídeo
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                
                logger.info(f"Baixando: {video_title} ({duration}s)")
                
                # Baixar vídeo
                ydl.download([url])
                
                # Encontrar arquivo baixado
                for file_path in self.temp_dir.glob(f"youtube_video_{int(time.time())}*"):
                    if file_path.suffix in self.supported_formats:
                        return str(file_path)
                
                raise Exception("Arquivo de vídeo não encontrado após download")
                
        except Exception as e:
            logger.error(f"Erro ao baixar vídeo do YouTube: {e}")
            raise Exception(f"Falha no download: {str(e)}")
    
    def extract_frames(self, video_path: str, interval_seconds: float = 1.0, 
                      max_frames: int = 300) -> List[Tuple[np.ndarray, float]]:
        """
        Extrai frames do vídeo em intervalos regulares
        
        Args:
            video_path: Caminho do arquivo de vídeo
            interval_seconds: Intervalo entre frames em segundos
            max_frames: Máximo de frames a extrair
        
        Returns:
            Lista de tuplas (frame, timestamp_seconds)
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise Exception("Não foi possível abrir o vídeo")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"Vídeo: {duration:.1f}s, {fps:.1f} FPS, {total_frames} frames")
        
        frames = []
        frame_interval = int(fps * interval_seconds)
        
        frame_count = 0
        while cap.isOpened() and len(frames) < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Extrair frame a cada intervalo
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                frames.append((frame.copy(), timestamp))
                logger.debug(f"Frame extraído: {timestamp:.1f}s")
            
            frame_count += 1
        
        cap.release()
        logger.info(f"Extraídos {len(frames)} frames do vídeo")
        
        return frames
    
    def process_video_faces(self, video_path: str, known_persons: List[Dict] = None,
                           frame_interval: float = 1.0, max_frames: int = 300) -> Dict:
        """
        Processa vídeo completo para reconhecimento facial
        
        Args:
            video_path: Caminho do vídeo
            known_persons: Lista de pessoas conhecidas com embeddings
            frame_interval: Intervalo entre frames analisados
            max_frames: Máximo de frames a processar
        
        Returns:
            Resultado completo do processamento
        """
        from app.services.face_recognition import face_service
        
        start_time = time.time()
        
        # Extrair frames
        frames = self.extract_frames(video_path, frame_interval, max_frames)
        
        results = {
            "video_path": video_path,
            "processing_info": {
                "total_frames_analyzed": len(frames),
                "frame_interval_seconds": frame_interval,
                "processing_start": datetime.now().isoformat(),
                "processing_duration": 0
            },
            "detections_by_frame": [],
            "person_timeline": {},
            "statistics": {
                "total_faces_detected": 0,
                "unique_persons_found": set(),
                "faces_per_second": {},
                "recognition_accuracy": 0.0
            },
            "errors": []
        }
        
        logger.info(f"Iniciando processamento de {len(frames)} frames")
        
        # Processar cada frame
        for i, (frame, timestamp) in enumerate(frames):
            try:
                # Detectar faces no frame
                face_detections = face_service.detect_faces(frame)
                
                frame_result = {
                    "frame_index": i,
                    "timestamp": timestamp,
                    "timestamp_formatted": str(timedelta(seconds=int(timestamp))),
                    "faces": [],
                    "recognized_persons": []
                }
                
                # Processar cada face detectada
                for face in face_detections:
                    face_info = {
                        "bbox": face["bbox"],
                        "confidence": face["confidence"],
                        "recognition": None
                    }
                    
                    # Tentar reconhecimento se há pessoas conhecidas
                    if known_persons:
                        best_match = None
                        best_confidence = 0.0
                        
                        for person in known_persons:
                            try:
                                similarity = face_service.compare_embeddings(
                                    face["embedding"], 
                                    person["embedding"]
                                )
                                
                                if similarity > best_confidence and similarity >= 0.4:
                                    best_confidence = similarity
                                    best_match = person
                            except Exception as e:
                                logger.warning(f"Erro ao comparar embedding: {e}")
                        
                        if best_match:
                            face_info["recognition"] = {
                                "person_id": best_match["id"],
                                "person_name": best_match["name"],
                                "confidence": best_confidence
                            }
                            
                            # Adicionar à timeline da pessoa
                            person_id = best_match["id"]
                            if person_id not in results["person_timeline"]:
                                results["person_timeline"][person_id] = {
                                    "name": best_match["name"],
                                    "appearances": [],
                                    "total_time": 0,
                                    "average_confidence": 0.0
                                }
                            
                            results["person_timeline"][person_id]["appearances"].append({
                                "timestamp": timestamp,
                                "confidence": best_confidence,
                                "frame_index": i
                            })
                            
                            results["statistics"]["unique_persons_found"].add(person_id)
                            frame_result["recognized_persons"].append(best_match["name"])
                    
                    frame_result["faces"].append(face_info)
                    results["statistics"]["total_faces_detected"] += 1
                
                # Contar faces por segundo
                second = int(timestamp)
                if second not in results["statistics"]["faces_per_second"]:
                    results["statistics"]["faces_per_second"][second] = 0
                results["statistics"]["faces_per_second"][second] += len(face_detections)
                
                results["detections_by_frame"].append(frame_result)
                
                # Log de progresso
                if i % 10 == 0:
                    progress = (i + 1) / len(frames) * 100
                    logger.info(f"Processamento: {progress:.1f}% ({i+1}/{len(frames)})")
                
            except Exception as e:
                error_msg = f"Erro no frame {i} (timestamp: {timestamp:.1f}s): {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Calcular estatísticas finais
        processing_time = time.time() - start_time
        results["processing_info"]["processing_duration"] = processing_time
        results["processing_info"]["processing_end"] = datetime.now().isoformat()
        
        # Converter set para lista para JSON
        results["statistics"]["unique_persons_found"] = list(results["statistics"]["unique_persons_found"])
        
        # Calcular estatísticas de timeline
        for person_id, timeline in results["person_timeline"].items():
            appearances = timeline["appearances"]
            if appearances:
                # Tempo total de aparição (aproximado)
                timeline["total_time"] = len(appearances) * frame_interval
                
                # Confiança média
                total_confidence = sum(app["confidence"] for app in appearances)
                timeline["average_confidence"] = total_confidence / len(appearances)
        
        logger.info(f"Processamento concluído em {processing_time:.1f}s")
        logger.info(f"Total de faces: {results['statistics']['total_faces_detected']}")
        logger.info(f"Pessoas únicas: {len(results['statistics']['unique_persons_found'])}")
        
        return results
    
    def create_annotated_video(self, video_path: str, detection_results: Dict, 
                              output_path: str = None) -> str:
        """
        Cria vídeo anotado com as detecções de faces
        
        Args:
            video_path: Vídeo original
            detection_results: Resultados do processamento
            output_path: Caminho de saída (opcional)
        
        Returns:
            Caminho do vídeo anotado
        """
        if output_path is None:
            output_path = str(self.temp_dir / f"annotated_{int(time.time())}.mp4")
        
        cap = cv2.VideoCapture(video_path)
        
        # Propriedades do vídeo original
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Codec e writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Criar mapa de detecções por timestamp
        detections_map = {}
        for frame_data in detection_results["detections_by_frame"]:
            timestamp = frame_data["timestamp"]
            detections_map[timestamp] = frame_data["faces"]
        
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Calcular timestamp do frame atual
            current_timestamp = frame_count / fps
            
            # Encontrar detecções mais próximas
            closest_timestamp = None
            min_diff = float('inf')
            
            for timestamp in detections_map.keys():
                diff = abs(timestamp - current_timestamp)
                if diff < min_diff:
                    min_diff = diff
                    closest_timestamp = timestamp
            
            # Anotar frame se há detecções próximas (dentro de 1 segundo)
            if closest_timestamp and min_diff <= 1.0:
                faces = detections_map[closest_timestamp]
                frame = self._draw_face_annotations(frame, faces)
            
            out.write(frame)
            frame_count += 1
            
            # Log de progresso
            if frame_count % 100 == 0:
                logger.debug(f"Anotando frame {frame_count}")
        
        cap.release()
        out.release()
        
        logger.info(f"Vídeo anotado criado: {output_path}")
        return output_path
    
    def _draw_face_annotations(self, frame: np.ndarray, faces: List[Dict]) -> np.ndarray:
        """Desenha anotações de faces no frame"""
        annotated_frame = frame.copy()
        
        for face in faces:
            bbox = face["bbox"]
            confidence = face["confidence"]
            recognition = face.get("recognition")
            
            # Cor baseada no reconhecimento
            color = (0, 255, 0) if recognition else (255, 0, 0)  # Verde se reconhecido, azul se não
            
            # Desenhar retângulo
            cv2.rectangle(annotated_frame, 
                         (bbox[0], bbox[1]), 
                         (bbox[2], bbox[3]), 
                         color, 2)
            
            # Texto da anotação
            if recognition:
                text = f"{recognition['person_name']} ({recognition['confidence']:.2f})"
            else:
                text = f"Desconhecido ({confidence:.2f})"
            
            # Fundo do texto
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(annotated_frame,
                         (bbox[0], bbox[1] - text_size[1] - 10),
                         (bbox[0] + text_size[0] + 5, bbox[1]),
                         color, -1)
            
            # Texto
            cv2.putText(annotated_frame, text,
                       (bbox[0] + 2, bbox[1] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return annotated_frame
    
    def generate_report(self, detection_results: Dict, format: str = "json") -> str:
        """
        Gera relatório do processamento
        
        Args:
            detection_results: Resultados do processamento
            format: Formato do relatório (json, html, txt)
        
        Returns:
            Caminho do arquivo de relatório
        """
        timestamp = int(time.time())
        
        if format == "json":
            report_path = self.temp_dir / f"report_{timestamp}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(detection_results, f, indent=2, ensure_ascii=False, default=str)
        
        elif format == "html":
            report_path = self.temp_dir / f"report_{timestamp}.html"
            html_content = self._generate_html_report(detection_results)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        elif format == "txt":
            report_path = self.temp_dir / f"report_{timestamp}.txt"
            txt_content = self._generate_text_report(detection_results)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(txt_content)
        
        else:
            raise ValueError("Formato não suportado. Use: json, html, txt")
        
        return str(report_path)
    
    def _generate_html_report(self, results: Dict) -> str:
        """Gera relatório em HTML"""
        stats = results["statistics"]
        timeline = results["person_timeline"]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>NewFacial - Relatório de Vídeo</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #007bff; color: white; padding: 20px; border-radius: 5px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 20px 0; }}
                .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }}
                .timeline {{ margin: 20px 0; }}
                .person {{ background: #e9ecef; margin: 10px 0; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎬 Relatório de Reconhecimento Facial em Vídeo</h1>
                <p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>{stats['total_faces_detected']}</h3>
                    <p>Faces Detectadas</p>
                </div>
                <div class="stat-card">
                    <h3>{len(stats['unique_persons_found'])}</h3>
                    <p>Pessoas Únicas</p>
                </div>
                <div class="stat-card">
                    <h3>{results['processing_info']['total_frames_analyzed']}</h3>
                    <p>Frames Analisados</p>
                </div>
            </div>
            
            <div class="timeline">
                <h2>Timeline de Pessoas</h2>
        """
        
        for person_id, data in timeline.items():
            html += f"""
                <div class="person">
                    <h3>{data['name']}</h3>
                    <p><strong>Tempo total:</strong> {data['total_time']:.1f}s</p>
                    <p><strong>Aparições:</strong> {len(data['appearances'])}</p>
                    <p><strong>Confiança média:</strong> {data['average_confidence']:.2f}</p>
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_text_report(self, results: Dict) -> str:
        """Gera relatório em texto"""
        stats = results["statistics"]
        timeline = results["person_timeline"]
        
        report = f"""
=== NEWFACIAL - RELATÓRIO DE RECONHECIMENTO FACIAL ===
Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

ESTATÍSTICAS GERAIS:
- Faces detectadas: {stats['total_faces_detected']}
- Pessoas únicas: {len(stats['unique_persons_found'])}
- Frames analisados: {results['processing_info']['total_frames_analyzed']}
- Tempo de processamento: {results['processing_info']['processing_duration']:.1f}s

TIMELINE DE PESSOAS:
        """
        
        for person_id, data in timeline.items():
            report += f"""
{data['name']}:
  - Tempo total: {data['total_time']:.1f}s
  - Aparições: {len(data['appearances'])}
  - Confiança média: {data['average_confidence']:.2f}
            """
        
        return report
    
    def cleanup_temp_files(self, older_than_hours: int = 24):
        """Remove arquivos temporários antigos"""
        cutoff_time = time.time() - (older_than_hours * 3600)
        
        removed_count = 0
        for file_path in self.temp_dir.glob("*"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Erro ao remover {file_path}: {e}")
        
        logger.info(f"Removidos {removed_count} arquivos temporários")

# Instância global do serviço
video_service = VideoProcessingService() 