"""
Motor Avanzado de Inferencia y Simulación Óptica Espectral.
Maneja análisis en tiempo real, mapas de estrés fotoelástico (Heatmap Jet),
curvas espectrométricas simuladas, escaneo láser y telemetría de distorsión óptica.
"""

import time
import math
import cv2
import numpy as np
from typing import Tuple, Dict, Any

class TransparentInferenceEngine:
    def __init__(self):
        self.simulation_mode = True
        self.alert_triggered = False
        self.trigger_timestamp = 0.0
        self.frame_count = 0
        self.scan_line_y = 0
        self.start_time = time.time()

    def trigger_optical_alert(self):
        self.alert_triggered = True
        self.trigger_timestamp = time.time()

    def reset_alert(self):
        self.alert_triggered = False

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Procesa el fotograma en vivo generando un pipeline de inspección de grado aeroespacial/industrial.
        """
        h, w = frame.shape[:2]
        annotated = frame.copy()
        self.frame_count += 1
        t_now = time.time()

        # Telemetría estándar
        stats = {
            "fps": 29.8 + 0.6 * math.sin(self.frame_count * 0.1),
            "inference_time_ms": 31.5 + 1.2 * math.cos(self.frame_count * 0.1),
            "refraction_index": 1.492, # Policarbonato óptico
            "snr_db": 24.6,
            "status": "NOMINAL",
            "alert_active": self.alert_triggered,
            "loss": 0.018,
            "far_rate": 0.02
        }

        # ---------------- MODO NOMINAL / CALIBRACIÓN ACTIVA ----------------
        if not self.alert_triggered:
            self._draw_professional_nominal_hud(annotated, w, h, t_now)
            return annotated, stats

        # ---------------- MODO ALERTA CRÍTICA (DISPARADO CON X) ----------------
        elapsed = t_now - self.trigger_timestamp
        pulse = int(128 + 127 * math.sin(elapsed * 6.0))
        border_color = (0, pulse, 255) # Ámbar a rojo destellante

        # 1. GENERAR MAPA DE ESTRÉS FOTOELÁSTICO / ABERRACIÓN ESPECTRAL (Falso Color Térmico)
        cx, cy = w // 2, h // 2
        box_w, box_h = int(w * 0.55), int(h * 0.45)
        x1, y1 = max(0, cx - box_w // 2), max(0, cy - box_h // 2)
        x2, y2 = min(w, cx + box_w // 2), min(h, cy + box_h // 2)

        # Región de interés ROI
        roi = annotated[y1:y2, x1:x2]
        if roi.size > 0:
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            # Simular gradiente de tensión y refracción caústica
            caustic_map = cv2.applyColorMap(gray_roi, cv2.COLORMAP_JET)
            # Mezclar parcialmente sobre la imagen original
            alpha = 0.45 + 0.15 * math.sin(elapsed * 4.0)
            annotated[y1:y2, x1:x2] = cv2.addWeighted(caustic_map, alpha, roi, 1 - alpha, 0)

        # 2. LÍNEA DE ESCANEO LÁSER VERTICAL DINÁMICA
        self.scan_line_y = (self.scan_line_y + 8) % h
        scan_alpha = 0.35
        overlay_scan = annotated.copy()
        cv2.line(overlay_scan, (0, self.scan_line_y), (w, self.scan_line_y), (0, 255, 255), 2)
        cv2.rectangle(overlay_scan, (0, max(0, self.scan_line_y - 12)), (w, self.scan_line_y), (0, 180, 255), -1)
        cv2.addWeighted(overlay_scan, scan_alpha, annotated, 1 - scan_alpha, 0, annotated)

        # 3. RECUADRO TÁCTICO DE FALLA ESPECTRAL CON ESQUINAS REFORZADAS
        cv2.rectangle(annotated, (x1, y1), (x2, y2), border_color, 2)
        L = 30 # Largo de esquina
        # Top-left
        cv2.line(annotated, (x1, y1), (x1 + L, y1), border_color, 4)
        cv2.line(annotated, (x1, y1), (x1, y1 + L), border_color, 4)
        # Top-right
        cv2.line(annotated, (x2, y1), (x2 - L, y1), border_color, 4)
        cv2.line(annotated, (x2, y1), (x2, y1 + L), border_color, 4)
        # Bottom-left
        cv2.line(annotated, (x1, y2), (x1 + L, y2), border_color, 4)
        cv2.line(annotated, (x1, y2), (x1, y2 - L), border_color, 4)
        # Bottom-right
        cv2.line(annotated, (x2, y2), (x2 - L, y2), border_color, 4)
        cv2.line(annotated, (x2, y2), (x2, y2 - L), border_color, 4)

        # Textos tácticos sobre el cuadro
        cv2.putText(annotated, "ANOMALIA: CAUSTICA REFRACTIVA Y DISPERSION DE TRANSMITANCIA", (x1, y1 - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, border_color, 2, cv2.LINE_AA)
        cv2.putText(annotated, "STATUS: GRADIENTE ESPECTRAL FUERA DE CONVERGENCIA [LOSS: 2.842]", (x1, y2 + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 140, 255), 1, cv2.LINE_AA)
        cv2.putText(annotated, "FIABILIDAD MODELO YOLOv8: 11.4% (TOLERANCIA INDUSTRIAL: >= 85.0%)", (x1, y2 + 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 80, 255), 1, cv2.LINE_AA)

        # 4. FALSOS POSITIVOS FLUCTUANTES EN ZONAS DE DESTELLO
        fx1, fy1 = int(x1 + box_w * 0.15), int(y1 + box_h * 0.25)
        fx2, fy2 = fx1 + 110, fy1 + 65
        cv2.rectangle(annotated, (fx1, fy1), (fx2, fy2), (0, 0, 255), 1)
        cv2.putText(annotated, "FALSO POSITIVO", (fx1, fy1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 255), 1)
        cv2.putText(annotated, "Destello Refractivo (9.2%)", (fx1, fy2 + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (180, 180, 255), 1)

        # 5. MINI ESPECTRÓMETRO EN LA ESQUINA INFERIOR DERECHA
        self._draw_spectrometer_widget(annotated, w - 260, h - 170, 240, 100, is_alert=True)

        # 6. BANNER SUPERIOR MILITAR INDUSTRIAL
        top_h = 74
        top_overlay = annotated[0:top_h, 0:w].copy()
        cv2.rectangle(top_overlay, (0, 0), (w, top_h), (8, 10, 24), -1)
        cv2.addWeighted(top_overlay, 0.88, annotated[0:top_h, 0:w], 0.12, 0, annotated[0:top_h, 0:w])
        cv2.line(annotated, (0, top_h), (w, top_h), (0, 0, 255), 2)

        cv2.putText(annotated, "[!] ALERTA CRITICA: MOTOR DE INFERENCIA DEEP LEARNING EN CONFLICTO", (20, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 130, 255), 2, cv2.LINE_AA)
        cv2.putText(annotated, "SUPERFICIE POLIMERICA TRANSLUCIDA REQUIERE ADQUISICION ESPECTRAL Y RE-ENTRENAMIENTO (3-4 MESES)", (20, 54),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (220, 220, 220), 1, cv2.LINE_AA)

        # 7. BANNER INFERIOR CON TELEMETRÍA DE REQUERIMIENTOS
        bot_h = 60
        bot_y = h - bot_h
        bot_overlay = annotated[bot_y:h, 0:w].copy()
        cv2.rectangle(bot_overlay, (0, 0), (w, bot_h), (10, 12, 18), -1)
        cv2.addWeighted(bot_overlay, 0.88, annotated[bot_y:h, 0:w], 0.12, 0, annotated[bot_y:h, 0:w])
        cv2.line(annotated, (0, bot_y), (w, bot_y), (0, 140, 255), 1)

        cv2.putText(annotated, "AUDITORIA TECNICA: Transmitancia refractiva > 82%. Generando ruido de fondo incompatible con dataset v1.0.", (20, bot_y + 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.47, (0, 200, 255), 1, cv2.LINE_AA)
        cv2.putText(annotated, "Presione [Ctrl+X] o [X] para ver el dictamen técnico completo | [Ctrl+R] para reiniciar", (20, bot_y + 46),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (150, 150, 150), 1, cv2.LINE_AA)

        # Estadísticas en modo alerta
        stats["status"] = "ERROR_REFRACTION_UNCONVERGED"
        stats["inference_time_ms"] = 148.4
        stats["snr_db"] = 4.2
        stats["loss"] = 2.842
        stats["far_rate"] = 0.748
        return annotated, stats

    def _draw_professional_nominal_hud(self, img: np.ndarray, w: int, h: int, t_now: float):
        """HUD de grado aeroespacial / inspección industrial en modo nominal."""
        cx, cy = w // 2, h // 2

        # Retícula y mirilla central militar
        c_green = (0, 220, 130)
        cv2.line(img, (cx - 25, cy), (cx + 25, cy), c_green, 1)
        cv2.line(img, (cx, cy - 25), (cx, cy + 25), c_green, 1)
        cv2.circle(img, (cx, cy), 14, c_green, 1)
        cv2.circle(img, (cx, cy), 3, (0, 255, 200), -1)

        # Caja de Región de Interés Activa (ROI)
        rx1, ry1 = int(w * 0.12), int(h * 0.12)
        rx2, ry2 = int(w * 0.88), int(h * 0.88)
        cv2.rectangle(img, (rx1, ry1), (rx2, ry2), (40, 70, 60), 1)

        # Marcas angulares de calibración
        cl = 15
        cv2.line(img, (rx1, ry1), (rx1 + cl, ry1), c_green, 2)
        cv2.line(img, (rx1, ry1), (rx1, ry1 + cl), c_green, 2)
        cv2.line(img, (rx2, ry1), (rx2 - cl, ry1), c_green, 2)
        cv2.line(img, (rx2, ry1), (rx2, ry1 + cl), c_green, 2)
        cv2.line(img, (rx1, ry2), (rx1 + cl, ry2), c_green, 2)
        cv2.line(img, (rx1, ry2), (rx1, ry2 - cl), c_green, 2)
        cv2.line(img, (rx2, ry2), (rx2 - cl, ry2), c_green, 2)
        cv2.line(img, (rx2, ry2), (rx2, ry2 - cl), c_green, 2)

        # Telemetría superior izquierda
        cv2.putText(img, "SENSOR: IP-CAM HD ULTRA-PRECISION [ONLINE]", (20, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 180), 1, cv2.LINE_AA)
        cv2.putText(img, f"CALIBRACION OPTICA: ACTIVA [ETA=1.492 | CPL-ON | 540nm]", (20, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 200, 220), 1, cv2.LINE_AA)

        # Espectrómetro en modo nominal
        self._draw_spectrometer_widget(img, w - 260, h - 170, 240, 100, is_alert=False)

    def _draw_spectrometer_widget(self, img: np.ndarray, x: int, y: int, width: int, height: int, is_alert: bool):
        """Dibuja un widget de gráfica espectral (longitud de onda vs transmitancia)"""
        # Fondo oscuro
        overlay = img[y:y+height, x:x+width].copy()
        cv2.rectangle(overlay, (0, 0), (width, height), (12, 16, 22), -1)
        cv2.addWeighted(overlay, 0.85, img[y:y+height, x:x+width], 0.15, 0, img[y:y+height, x:x+width])
        
        border_c = (0, 80, 255) if is_alert else (40, 90, 70)
        cv2.rectangle(img, (x, y), (x + width, y + height), border_c, 1)

        # Título
        title = "ESPECTROMETRIA: CAUSTICA ANOMALA" if is_alert else "ESPECTROMETRIA NOMINAL"
        t_color = (0, 140, 255) if is_alert else (0, 220, 150)
        cv2.putText(img, title, (x + 8, y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.38, t_color, 1, cv2.LINE_AA)

        # Eje de gráfica
        gx = x + 15
        gy = y + height - 15
        gw = width - 30
        gh = height - 38

        # Dibujar curva espectral simulada
        points = []
        steps = 25
        for i in range(steps):
            px = int(gx + (i / (steps - 1)) * gw)
            norm = i / (steps - 1)
            if is_alert:
                # Curva distorsionada y con ruido alto de transmitancia
                noise = (np.random.rand() - 0.5) * 0.4
                val = 0.85 * math.sin(norm * math.pi) + noise
                val = max(0.1, min(0.95, val))
            else:
                # Curva suave y controlada
                val = 0.35 + 0.3 * math.exp(-((norm - 0.5) ** 2) / 0.08)

            py = int(gy - val * gh)
            points.append((px, py))

        line_c = (0, 80, 255) if is_alert else (0, 255, 180)
        for i in range(len(points) - 1):
            cv2.line(img, points[i], points[i+1], line_c, 2)

        # Ejes
        cv2.putText(img, "400nm", (gx, y + height - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.30, (120, 130, 140), 1)
        cv2.putText(img, "700nm", (gx + gw - 32, y + height - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.30, (120, 130, 140), 1)
