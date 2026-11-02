import os
import time
import logging
from typing import Optional
import cv2
import numpy as np
from src.vision.detection_service import VisionDetector, VisionInferenceResult, DetectionRegion

logger = logging.getLogger("vision_inspection.yolo_adapter")

class YOLOAdapter(VisionDetector):
    """
    Adaptador para modelos de detección Ultralytics YOLO.
    Inspecciona si el paquete y los pesos reales existen antes de operar.
    No inventa detecciones ni emite falsos positivos si los pesos no están disponibles.
    """

    def __init__(self, weights_path: str = "models/yolov8_custom.pt", conf_thresh: float = 0.45):
        self.weights_path = weights_path
        self.conf_thresh = conf_thresh
        self._model = None
        self._is_ready = False
        self._load_status = "No inicializado"
        self._load_model()

    def _load_model(self) -> None:
        if not os.path.exists(self.weights_path):
            self._load_status = f"Pesos no encontrados en {self.weights_path}. YOLO no configurado."
            self._is_ready = False
            logger.info(self._load_status)
            return

        try:
            from ultralytics import YOLO
            self._model = YOLO(self.weights_path)
            self._is_ready = True
            self._load_status = f"Modelo YOLO cargado exitosamente desde {self.weights_path}"
            logger.info(self._load_status)
        except ImportError:
            self._load_status = "Biblioteca 'ultralytics' no instalada. YOLO no disponible."
            self._is_ready = False
            logger.warning(self._load_status)
        except Exception as e:
            self._load_status = f"Error al cargar pesos YOLO: {e}"
            self._is_ready = False
            logger.error(self._load_status)

    def is_ready(self) -> bool:
        return self._is_ready

    def get_status_info(self) -> str:
        return self._load_status

    def detect(self, frame: np.ndarray) -> VisionInferenceResult:
        if not self._is_ready or self._model is None:
            return VisionInferenceResult(
                model_name="YOLO (No configurado)",
                model_version="N/A",
                is_available=False,
                status_message=self._load_status,
                has_detections=False
            )

        start_time = time.time()
        try:
            h, w = frame.shape[:2]
            regions_dict = {}  # clave: (cls_id, round_coord) para supresión de duplicados

            # 1. Pase global optimizado
            results = self._model(frame, conf=self.conf_thresh, verbose=False)
            for r in results:
                for box in r.boxes:
                    xyxy = box.xyxy[0].cpu().numpy().astype(int)
                    conf = float(box.conf[0].cpu().numpy())
                    cls_id = int(box.cls[0].cpu().numpy())
                    label = self._model.names.get(cls_id, f"clase_{cls_id}")

                    # Agrupar por proximidad
                    box_key = (cls_id, xyxy[0] // 30, xyxy[1] // 30, xyxy[2] // 30, xyxy[3] // 30)
                    if box_key not in regions_dict or conf > regions_dict[box_key].confidence_or_score:
                        regions_dict[box_key] = DetectionRegion(
                            x1=int(xyxy[0]),
                            y1=int(xyxy[1]),
                            x2=int(xyxy[2]),
                            y2=int(xyxy[3]),
                            confidence_or_score=conf,
                            label=label,
                            is_anomaly_score=False
                        )

            # 2. Si la resolución es mayor a 800px (típico en cámara industrial de rodillo),
            # procesamos la franja central donde pasan las tejas para microporos milimétricos
            if w > 800 or h > 800:
                mid_y1 = max(0, h // 4)
                mid_y2 = min(h, 3 * h // 4)
                strip = frame[mid_y1:mid_y2, :]
                if strip.size > 0:
                    results_strip = self._model(strip, conf=self.conf_thresh, verbose=False)
                    for r in results_strip:
                        for box in r.boxes:
                            xyxy = box.xyxy[0].cpu().numpy().astype(int)
                            conf = float(box.conf[0].cpu().numpy())
                            cls_id = int(box.cls[0].cpu().numpy())
                            label = self._model.names.get(cls_id, f"clase_{cls_id}")

                            gx1 = int(xyxy[0])
                            gy1 = int(xyxy[1] + mid_y1)
                            gx2 = int(xyxy[2])
                            gy2 = int(xyxy[3] + mid_y1)

                            box_key = (cls_id, gx1 // 30, gy1 // 30, gx2 // 30, gy2 // 30)
                            if box_key not in regions_dict or conf > regions_dict[box_key].confidence_or_score:
                                regions_dict[box_key] = DetectionRegion(
                                    x1=gx1, y1=gy1, x2=gx2, y2=gy2,
                                    confidence_or_score=conf,
                                    label=label,
                                    is_anomaly_score=False
                                )

            # 3. Detector de anomalías superficiales (huecos, poros, puntos negros, manchas)
            # Filtro inteligente de reflejos: descarta brillos especulares de lámparas y rodillos
            try:
                scale = 1.0
                if max(h, w) > 960:
                    scale = 960.0 / max(h, w)
                    small = cv2.resize(frame, (int(w * scale), int(h * scale)))
                else:
                    small = frame

                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                bg = cv2.medianBlur(gray, 31)

                # A. Defectos oscuros (huecos, perforaciones, poros, manchas oscuras de grasa o polvo)
                # La zona del defecto es más oscura que la teja de fondo: (bg - gray)
                dark_diff = cv2.subtract(bg, gray)

                # B. Defectos claros pero mates (no reflejos especulares de luz):
                # Un reflejo de luz produce saturación brillante blanca (gray > 195 o píxel muy brillante)
                # y bandas alargadas horizontales en la ondulación. Descartamos reflejos de luz:
                light_diff = cv2.subtract(gray, bg)
                is_reflection = (gray > 195)
                light_diff[is_reflection] = 0

                # Combinar mapa de anomalías libre de reflejos especulares
                anomaly_map = cv2.add(dark_diff, light_diff)

                # Umbral de ruptura de uniformidad
                _, thresh = cv2.threshold(anomaly_map, 38, 255, cv2.THRESH_BINARY)
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                anomaly_candidates = []
                for c in contours:
                    area = cv2.contourArea(c)
                    if 25 <= area <= (small.shape[0] * small.shape[1] * 0.12):
                        bx, by, bw, bh = cv2.boundingRect(c)

                        # Descartar artefactos pegados al borde del fotograma (y < 4 o x < 4)
                        if by <= 2 or (by + bh) >= (small.shape[0] - 2) or bx <= 2 or (bx + bw) >= (small.shape[1] - 2):
                            continue

                        # Descartar franjas alargadas características de reflejos en las ondas de la teja
                        aspect_ratio = bw / max(1, bh)
                        if aspect_ratio > 3.5 or aspect_ratio < 0.28:
                            continue

                        # Descartar si el centro del área sigue siendo un brillo elevado (reflejo difuso)
                        roi_gray = gray[by:by+bh, bx:bx+bw]
                        if roi_gray.size > 0 and roi_gray.mean() > 205:
                            continue

                        ox1 = int(bx / scale)
                        oy1 = int(by / scale)
                        ox2 = int((bx + bw) / scale)
                        oy2 = int((by + bh) / scale)

                        # Verificar si ya está cubierto por YOLO
                        overlap_found = False
                        for ex_reg in regions_dict.values():
                            if not (ox2 < ex_reg.x1 or ox1 > ex_reg.x2 or oy2 < ex_reg.y1 or oy1 > ex_reg.y2):
                                overlap_found = True
                                break

                        if not overlap_found:
                            contrast_score = min(0.95, max(0.60, 0.55 + (area / 1500.0) * 0.2))
                            anomaly_candidates.append(
                                (area, DetectionRegion(
                                    x1=ox1,
                                    y1=oy1,
                                    x2=ox2,
                                    y2=oy2,
                                    confidence_or_score=contrast_score,
                                    label="defecto_teja",
                                    is_anomaly_score=True
                                ))
                            )

                # Ordenar por severidad (área del defecto) y limitar
                anomaly_candidates.sort(key=lambda x: x[0], reverse=True)
                for _, reg in anomaly_candidates[:8]:
                    box_key = (99, reg.x1 // 30, reg.y1 // 30, reg.x2 // 30, reg.y2 // 30)
                    regions_dict[box_key] = reg
            except Exception as e_anom:
                logger.debug(f"Error en detección de anomalías de superficie: {e_anom}")

            regions = list(regions_dict.values())
            inference_ms = (time.time() - start_time) * 1000.0

            return VisionInferenceResult(
                model_name="Ultralytics YOLO + Detector Superficie",
                model_version="v8-hibrido",
                is_available=True,
                status_message=f"{len(regions)} defecto(s) detectado(s)",
                inference_time_ms=inference_ms,
                regions=regions,
                has_detections=len(regions) > 0
            )
        except Exception as e:
            logger.error(f"Error en inferencia YOLO: {e}")
            return VisionInferenceResult(
                model_name="Ultralytics YOLO",
                model_version="v8",
                is_available=True,
                status_message=f"Error en inferencia: {e}",
                inference_time_ms=(time.time() - start_time) * 1000.0,
                has_detections=False
            )

