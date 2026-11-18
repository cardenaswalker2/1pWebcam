"""
Simulador de Inferencia de Visión Artificial para Láminas Poliméricas Translúcidas.
Módulo de diagnóstico y análisis de refracción óptica.
"""

import time
import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class AnomalyDetection:
    label: str
    confidence: float
    box: Tuple[int, int, int, int]  # x1, y1, x2, y2
    anomaly_score: float
    wavelength_dispersion: float

class TransparentInferenceEngine:
    def __init__(self):
        self.simulation_mode = True
        self.alert_triggered = False
        self.trigger_timestamp = 0.0
        self.frame_count = 0

    def trigger_optical_alert(self):
        self.alert_triggered = True
        self.trigger_timestamp = time.time()

    def reset_alert(self):
        self.alert_triggered = False

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, dict]:
        """
        Procesa el frame en vivo. Si alert_triggered es True, genera la visualización
        con HUD de telemetría de distorsión óptica, gradiente espectral y advertencia de refracción.
        """
        h, w = frame.shape[:2]
        annotated = frame.copy()
        self.frame_count += 1

        stats = {
            "fps": 30.0,
            "inference_time_ms": 32.4,
            "refraction_index": 1.492, # Índice de refracción típico de policarbonato/acrílico
            "snr_db": 14.2,
            "status": "NORMAL",
            "alert_active": self.alert_triggered
        }

        if not self.alert_triggered:
            # Estado normal de visualización con HUD sutil de telemetría translúcida
            # Dibujar retícula sutil de calibración
            self._draw_normal_hud(annotated, w, h)
            return annotated, stats

        # SI SE DISPARÓ LA ALERTA (Ctrl+X o X):
        elapsed = time.time() - self.trigger_timestamp
        # Efecto de pulso / parpadeo de advertencia
        pulse = int(128 + 127 * np.sin(elapsed * 5.0))
        
        # 1. Overlay tintado ámbar/rojo de fallo espectral
        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 30, 90), -1)
        cv2.addWeighted(overlay, 0.25, annotated, 0.75, 0, annotated)

        # 2. Dibujar zonas de falso positivo / aberración cromática simulada
        cx, cy = w // 2, h // 2
        # Zona 1: Centro de refracción crítica
        box_w, box_h = int(w * 0.45), int(h * 0.4)
        x1, y1 = cx - box_w // 2, cy - box_h // 2
        x2, y2 = cx + box_w // 2, cy + box_h // 2

        # Bounding box parpadeante
        border_color = (0, pulse, 255) # BGR: naranja a amarillo intenso
        cv2.rectangle(annotated, (x1, y1), (x2, y2), border_color, 2)

        # Esquinas tipo visor táctico industrial
        line_len = 25
        # Top-left
        cv2.line(annotated, (x1, y1), (x1 + line_len, y1), border_color, 4)
        cv2.line(annotated, (x1, y1), (x1, y1 + line_len), border_color, 4)
        # Top-right
        cv2.line(annotated, (x2, y1), (x2 - line_len, y1), border_color, 4)
        cv2.line(annotated, (x2, y1), (x2, y1 + line_len), border_color, 4)
        # Bottom-left
        cv2.line(annotated, (x1, y2), (x1 + line_len, y2), border_color, 4)
        cv2.line(annotated, (x1, y2), (x1, y2 - line_len), border_color, 4)
        # Bottom-right
        cv2.line(annotated, (x2, y2), (x2 - line_len, y2), border_color, 4)
        cv2.line(annotated, (x2, y2), (x2, y2 - line_len), border_color, 4)

        # Etiquetas técnicas sobre el cuadro
        cv2.putText(annotated, "ERR: CAUSTICA OPTICA & TRANSMITANCIA REFRACTIVA", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, border_color, 2, cv2.LINE_AA)
        cv2.putText(annotated, f"CONFIDENCIA MODELO: 11.4% [UMBRAL MINIMO: 85.0%]", (x1, y2 + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 180, 255), 1, cv2.LINE_AA)
        cv2.putText(annotated, "STATUS: GRADIENTE ESPECTRAL FUERA DE CONVERGENCIA", (x1, y2 + 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 100, 255), 1, cv2.LINE_AA)

        # 3. Banner superior translúcido de advertencia crítica
        banner_h = 70
        banner_bg = annotated[0:banner_h, 0:w].copy()
        cv2.rectangle(banner_bg, (0, 0), (w, banner_h), (10, 10, 30), -1)
        cv2.addWeighted(banner_bg, 0.85, annotated[0:banner_h, 0:w], 0.15, 0, annotated[0:banner_h, 0:w])
        
        cv2.line(annotated, (0, banner_h), (w, banner_h), (0, 0, 255), 2)
        cv2.putText(annotated, "[!] ALERTA CRITICA DE MOTOR DE INFERENCIA DEEP LEARNING", (20, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 140, 255), 2, cv2.LINE_AA)
        cv2.putText(annotated, "INCOMPATIBILIDAD DE MATERIAL: POLICARBONATO / POLIMERO TRANSLUCIDO NO ENTRENADO", (20, 52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (220, 220, 220), 1, cv2.LINE_AA)

        # 4. Banner inferior con telemetría de requisitos de entrenamiento
        footer_y = h - 60
        footer_bg = annotated[footer_y:h, 0:w].copy()
        cv2.rectangle(footer_bg, (0, 0), (w, 60), (15, 15, 20), -1)
        cv2.addWeighted(footer_bg, 0.85, annotated[footer_y:h, 0:w], 0.15, 0, annotated[footer_y:h, 0:w])
        cv2.line(annotated, (0, footer_y), (w, footer_y), (0, 165, 255), 1)

        cv2.putText(annotated, "REQUERIMIENTO: Adquisicion dataset polarizado + calibracion causticas (Est. 90-120 dias)", (20, footer_y + 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 220, 255), 1, cv2.LINE_AA)
        cv2.putText(annotated, "Presione [Ctrl+X] para re-inspeccionar / ver reporte detallado", (20, footer_y + 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1, cv2.LINE_AA)

        stats["status"] = "ERROR_REFRACTION_UNCONVERGED"
        stats["inference_time_ms"] = 142.8
        stats["confidence"] = 0.114
        return annotated, stats

    def _draw_normal_hud(self, img: np.ndarray, w: int, h: int):
        """Dibuja un HUD industrial elegante para dar aspecto 100% profesional de monitoreo"""
        # Esquinas del viewport
        c_color = (0, 200, 100) # Verde cian
        # Mira central
        cx, cy = w // 2, h // 2
        cv2.line(img, (cx - 20, cy), (cx + 20, cy), c_color, 1)
        cv2.line(img, (cx, cy - 20), (cx, cy + 20), c_color, 1)
        cv2.circle(img, (cx, cy), 10, c_color, 1)

        # Telemetría superior izquierda
        cv2.putText(img, "SENSOR: IP-CAM HD OPTICAL STREAM [ACTIVE]", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 255, 150), 1, cv2.LINE_AA)
        cv2.putText(img, "MODO: ANALISIS TRANSLUCIDO / TRANSMITANCIA ESPECTRAL", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

        # Región de interés ROI estimada
        rx1, ry1 = int(w * 0.15), int(h * 0.15)
        rx2, ry2 = int(w * 0.85), int(h * 0.85)
        cv2.rectangle(img, (rx1, ry1), (rx2, ry2), (60, 60, 80), 1)
        cv2.putText(img, "ROI: POLIMERO_SURFACE_MONITOR", (rx1 + 5, ry1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (120, 140, 160), 1, cv2.LINE_AA)
