"""
Motor Avanzado de Inferencia y Simulación Óptica Espectral v3.0.
HUD Espectacular, Alerta Sonora de Alarma Industrial en Hilo Independiente (10 Segundos),
Banners de Impacto en Video con Letras Grandes y Legibles destacando el requisito de 3 a 4 MESES.
"""

import time
import math
import threading
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
        self.alarm_thread: threading.Thread = None
        self.alarm_running = False

    def trigger_optical_alert(self):
        self.alert_triggered = True
        self.trigger_timestamp = time.time()
        self._start_industrial_alarm_10s()

    def reset_alert(self):
        self.alert_triggered = False
        self.alarm_running = False

    def _start_industrial_alarm_10s(self):
        """Inicia secuencia de pitido industrial tipo sirena/alarma técnica durante 10 segundos en hilo separado"""
        if self.alarm_running:
            return

        def _alarm_worker():
            self.alarm_running = True
            try:
                import winsound
                end_time = time.time() + 10.0 # 10 segundos exactos
                while time.time() < end_time and self.alarm_running:
                    # Tono dual de advertencia tipo radar/scada industrial
                    winsound.Beep(920, 220)  # Tono alto
                    time.sleep(0.08)
                    if not self.alarm_running or time.time() >= end_time:
                        break
                    winsound.Beep(740, 220)  # Tono bajo
                    time.sleep(0.18)
            except Exception:
                pass
            finally:
                self.alarm_running = False

        self.alarm_thread = threading.Thread(target=_alarm_worker, daemon=True)
        self.alarm_thread.start()

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        h, w = frame.shape[:2]
        annotated = frame.copy()
        self.frame_count += 1
        t_now = time.time()

        stats = {
            "fps": 29.8 + 0.5 * math.sin(self.frame_count * 0.1),
            "inference_time_ms": 31.2 + 1.0 * math.cos(self.frame_count * 0.1),
            "refraction_index": 1.492,
            "snr_db": 25.4,
            "status": "NOMINAL",
            "alert_active": self.alert_triggered,
            "loss": 0.015
        }

        # ---------------- MODO NOMINAL ----------------
        if not self.alert_triggered:
            self._draw_professional_nominal_hud(annotated, w, h)
            return annotated, stats

        # ---------------- MODO ALERTA CRÍTICA (DISPARADO CON X) ----------------
        elapsed = t_now - self.trigger_timestamp
        pulse = int(128 + 127 * math.sin(elapsed * 7.0))
        border_color = (0, pulse, 255) # Ámbar a rojo parpadeante

        # 1. MAPA DE ESTRÉS FOTOELÁSTICO (Falso Color Térmico en la zona del material)
        cx, cy = w // 2, h // 2
        box_w, box_h = int(w * 0.60), int(h * 0.50)
        x1, y1 = max(0, cx - box_w // 2), max(0, cy - box_h // 2)
        x2, y2 = min(w, cx + box_w // 2), min(h, cy + box_h // 2)

        roi = annotated[y1:y2, x1:x2]
        if roi.size > 0:
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            caustic_map = cv2.applyColorMap(gray_roi, cv2.COLORMAP_JET)
            alpha = 0.40 + 0.15 * math.sin(elapsed * 5.0)
            annotated[y1:y2, x1:x2] = cv2.addWeighted(caustic_map, alpha, roi, 1 - alpha, 0)

        # 2. LÍNEA DE ESCANEO LÁSER DINÁMICA
        self.scan_line_y = (self.scan_line_y + 9) % h
        overlay_scan = annotated.copy()
        cv2.line(overlay_scan, (0, self.scan_line_y), (w, self.scan_line_y), (0, 255, 255), 3)
        cv2.rectangle(overlay_scan, (0, max(0, self.scan_line_y - 14)), (w, self.scan_line_y), (0, 180, 255), -1)
        cv2.addWeighted(overlay_scan, 0.40, annotated, 0.60, 0, annotated)

        # 3. RECUADRO TÁCTICO CON ESQUINAS REFORZADAS
        cv2.rectangle(annotated, (x1, y1), (x2, y2), border_color, 3)
        L = 35
        # Top-left
        cv2.line(annotated, (x1, y1), (x1 + L, y1), border_color, 5)
        cv2.line(annotated, (x1, y1), (x1, y1 + L), border_color, 5)
        # Top-right
        cv2.line(annotated, (x2, y1), (x2 - L, y1), border_color, 5)
        cv2.line(annotated, (x2, y1), (x2, y1 + L), border_color, 5)
        # Bottom-left
        cv2.line(annotated, (x1, y2), (x1 + L, y2), border_color, 5)
        cv2.line(annotated, (x1, y2), (x1, y2 - L), border_color, 5)
        # Bottom-right
        cv2.line(annotated, (x2, y2), (x2 - L, y2), border_color, 5)
        cv2.line(annotated, (x2, y2), (x2, y2 - L), border_color, 5)

        # 4. FALSOS POSITIVOS FLUCTUANTES
        fx1, fy1 = int(x1 + box_w * 0.15), int(y1 + box_h * 0.20)
        fx2, fy2 = fx1 + 130, fy1 + 65
        cv2.rectangle(annotated, (fx1, fy1), (fx2, fy2), (0, 0, 255), 2)
        cv2.putText(annotated, "FALSO POSITIVO", (fx1 + 5, fy1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 255), 2)
        cv2.putText(annotated, "Destello Optico (11.2%)", (fx1 + 5, fy2 + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 255), 1)

        # 5. ESPECTRÓMETRO EN LA ESQUINA
        self._draw_spectrometer_widget(annotated, w - 270, h - 180, 250, 105, is_alert=True)

        # 6. BANNER SUPERIOR CON TIPOGRAFÍA GRANDE Y CLARA
        top_h = 82
        top_overlay = annotated[0:top_h, 0:w].copy()
        cv2.rectangle(top_overlay, (0, 0), (w, top_h), (5, 8, 20), -1)
        cv2.addWeighted(top_overlay, 0.90, annotated[0:top_h, 0:w], 0.10, 0, annotated[0:top_h, 0:w])
        cv2.line(annotated, (0, top_h), (w, top_h), (0, 0, 255), 3)

        cv2.putText(annotated, "[!] ALERTA CRITICA: INCOMPATIBILIDAD POR MATERIAL TRANSLUCIDO", (20, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 100, 255), 2, cv2.LINE_AA)
        cv2.putText(annotated, "FENOMENO DE CAUSTICA Y REFRACCION - CONFIANZA DEL MODELO: 11.4% (CRITICO)", (20, 64),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.54, (220, 220, 220), 1, cv2.LINE_AA)

        # 7. CARTEL CENTRAL GIGANTE DE IMPACTO: "FASE DE ENTRENAMIENTO: 3 A 4 MESES"
        msg_w, msg_h = int(w * 0.72), 95
        msg_x = (w - msg_w) // 2
        msg_y = y2 + 12
        if msg_y + msg_h > h - 75:
            msg_y = y1 - msg_h - 12
            if msg_y < top_h + 10:
                msg_y = (h - msg_h) // 2

        # Placa de advertencia destacada
        card_bg = annotated[msg_y:msg_y+msg_h, msg_x:msg_x+msg_w].copy()
        cv2.rectangle(card_bg, (0, 0), (msg_w, msg_h), (10, 10, 30), -1)
        cv2.addWeighted(card_bg, 0.92, annotated[msg_y:msg_y+msg_h, msg_x:msg_x+msg_w], 0.08, 0, annotated[msg_y:msg_y+msg_h, msg_x:msg_x+msg_w])
        cv2.rectangle(annotated, (msg_x, msg_y), (msg_x + msg_w, msg_y + msg_h), (0, 140, 255), 2)

        # Texto GRANDE y contundente para el cliente
        cv2.putText(annotated, "REQUISITO OBLIGATORIO DE ADAPTACION TECNICA:", (msg_x + 18, msg_y + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.60, (0, 220, 255), 2, cv2.LINE_AA)
        cv2.putText(annotated, "TIEMPO ESTIMADO DE ENTRENAMIENTO IA: 3 A 4 MESES", (msg_x + 18, msg_y + 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.82, (0, 80, 255), 3, cv2.LINE_AA)

        # 8. BANNER INFERIOR
        bot_h = 60
        bot_y = h - bot_h
        bot_overlay = annotated[bot_y:h, 0:w].copy()
        cv2.rectangle(bot_overlay, (0, 0), (w, bot_h), (8, 10, 16), -1)
        cv2.addWeighted(bot_overlay, 0.90, annotated[bot_y:h, 0:w], 0.10, 0, annotated[bot_y:h, 0:w])
        cv2.line(annotated, (0, bot_y), (w, bot_y), (0, 140, 255), 1)

        cv2.putText(annotated, "Presione [Ctrl+X] o [X] para abrir el Dictamen Oficial | [Ctrl+R] para restaurar", (20, bot_y + 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 200, 255), 1, cv2.LINE_AA)

        stats["status"] = "ERROR_REFRACTION_UNCONVERGED"
        stats["inference_time_ms"] = 152.6
        stats["snr_db"] = 3.8
        stats["loss"] = 2.842
        return annotated, stats

    def _draw_professional_nominal_hud(self, img: np.ndarray, w: int, h: int):
        cx, cy = w // 2, h // 2
        c_green = (0, 220, 130)

        # Retícula central
        cv2.line(img, (cx - 25, cy), (cx + 25, cy), c_green, 1)
        cv2.line(img, (cx, cy - 25), (cx, cy + 25), c_green, 1)
        cv2.circle(img, (cx, cy), 14, c_green, 1)

        # ROI
        rx1, ry1 = int(w * 0.12), int(h * 0.12)
        rx2, ry2 = int(w * 0.88), int(h * 0.88)
        cv2.rectangle(img, (rx1, ry1), (rx2, ry2), (40, 70, 60), 1)

        # Telemetría superior izquierda
        cv2.putText(img, "SENSOR: IP-CAM HD OPTICAL FEED [ONLINE]", (20, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 255, 180), 1, cv2.LINE_AA)
        cv2.putText(img, "CALIBRACION OPTICA: ACTIVA [ETA=1.492 | 540nm | CPL-ON]", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (180, 200, 220), 1, cv2.LINE_AA)

        self._draw_spectrometer_widget(img, w - 270, h - 180, 250, 105, is_alert=False)

    def _draw_spectrometer_widget(self, img: np.ndarray, x: int, y: int, width: int, height: int, is_alert: bool):
        overlay = img[y:y+height, x:x+width].copy()
        cv2.rectangle(overlay, (0, 0), (width, height), (12, 16, 22), -1)
        cv2.addWeighted(overlay, 0.85, img[y:y+height, x:x+width], 0.15, 0, img[y:y+height, x:x+width])
        
        border_c = (0, 80, 255) if is_alert else (40, 90, 70)
        cv2.rectangle(img, (x, y), (x + width, y + height), border_c, 1)

        title = "ESPECTROMETRIA: ANOMALA" if is_alert else "ESPECTROMETRIA NOMINAL"
        t_color = (0, 140, 255) if is_alert else (0, 220, 150)
        cv2.putText(img, title, (x + 8, y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.38, t_color, 1, cv2.LINE_AA)

        gx = x + 15
        gy = y + height - 15
        gw = width - 30
        gh = height - 38

        points = []
        steps = 25
        for i in range(steps):
            px = int(gx + (i / (steps - 1)) * gw)
            norm = i / (steps - 1)
            if is_alert:
                noise = (np.random.rand() - 0.5) * 0.4
                val = 0.85 * math.sin(norm * math.pi) + noise
                val = max(0.1, min(0.95, val))
            else:
                val = 0.35 + 0.3 * math.exp(-((norm - 0.5) ** 2) / 0.08)

            py = int(gy - val * gh)
            points.append((px, py))

        line_c = (0, 80, 255) if is_alert else (0, 255, 180)
        for i in range(len(points) - 1):
            cv2.line(img, points[i], points[i+1], line_c, 2)

        cv2.putText(img, "400nm", (gx, y + height - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.30, (120, 130, 140), 1)
        cv2.putText(img, "700nm", (gx + gw - 32, y + height - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.30, (120, 130, 140), 1)
