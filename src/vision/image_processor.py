from typing import Optional, List, Tuple
import cv2
import numpy as np
from src.vision.detection_service import VisionInferenceResult, DetectionRegion

class ImageProcessor:
    """
    Procesador de imágenes para preparación de visualización, dibujo de contornos
    y transformaciones para análisis por parches sin alterar el fotograma original.
    """

    @staticmethod
    def annotate_frame(
        frame: np.ndarray,
        result: VisionInferenceResult,
        mm_per_pixel: float = 0.25
    ) -> np.ndarray:
        """
        Dibuja los contornos o recuadros de detección con estilo HUD industrial
        y metrología milimétrica estimada sobre una COPIA del fotograma original.
        """
        if frame is None or frame.size == 0:
            return frame

        annotated = frame.copy()

        if not result.has_detections or not result.regions:
            return annotated

        for region in result.regions:
            # Color rojo brillante para No Conformidad (defecto de teja)
            is_high_conf = region.confidence_or_score >= 0.5
            box_color = (36, 36, 235) if is_high_conf else (0, 140, 255) # BGR (Rojo / Naranja)

            x1, y1, x2, y2 = region.x1, region.y1, region.x2, region.y2
            
            # Cálculo de metrología milimétrica
            w_px = max(1, x2 - x1)
            h_px = max(1, y2 - y1)
            w_mm = w_px * mm_per_pixel
            h_mm = h_px * mm_per_pixel
            
            # 1. Bounding box con fondo translúcido sutil
            sub_overlay = annotated[y1:y2, x1:x2]
            if sub_overlay.size > 0:
                color_rect = np.full_like(sub_overlay, (0, 0, 180) if is_high_conf else (0, 100, 200))
                cv2.addWeighted(sub_overlay, 0.85, color_rect, 0.15, 0, sub_overlay)
                annotated[y1:y2, x1:x2] = sub_overlay

            # Contorno de caja
            cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, 2)

            # Esquinas HUD reforzadas estilo visión artificial industrial
            line_len = max(8, min(24, int(min(x2 - x1, y2 - y1) * 0.25)))
            thick = 3
            # Superior Izquierda
            cv2.line(annotated, (x1, y1), (x1 + line_len, y1), (0, 255, 255), thick)
            cv2.line(annotated, (x1, y1), (x1, y1 + line_len), (0, 255, 255), thick)
            # Superior Derecha
            cv2.line(annotated, (x2, y1), (x2 - line_len, y1), (0, 255, 255), thick)
            cv2.line(annotated, (x2, y1), (x2, y1 + line_len), (0, 255, 255), thick)
            # Inferior Izquierda
            cv2.line(annotated, (x1, y2), (x1 + line_len, y2), (0, 255, 255), thick)
            cv2.line(annotated, (x1, y2), (x1, y2 - line_len), (0, 255, 255), thick)
            # Inferior Derecha
            cv2.line(annotated, (x2, y2), (x2 - line_len, y2), (0, 255, 255), thick)
            cv2.line(annotated, (x2, y2), (x2, y2 - line_len), (0, 255, 255), thick)

            # 2. Etiqueta destacada con metrología milimétrica
            label_text = f"NO CONFORME [{region.label.upper()}]: {region.confidence_or_score:.0%} ({w_mm:.1f}x{h_mm:.1f} mm)"
            if region.is_anomaly_score:
                label_text = f"ANOMALIA TEJA: {region.confidence_or_score:.0%} ({w_mm:.1f}x{h_mm:.1f} mm)"

            (tw, th), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_DUPLEX, 0.45, 1)
            label_y = max(th + 6, y1 - 6)
            
            # Badge background
            cv2.rectangle(
                annotated,
                (x1, label_y - th - 5),
                (x1 + tw + 10, label_y + baseline - 2),
                (20, 20, 20),
                -1
            )
            cv2.rectangle(
                annotated,
                (x1, label_y - th - 5),
                (x1 + tw + 10, label_y + baseline - 2),
                box_color,
                1
            )

            # Texto
            cv2.putText(
                annotated,
                label_text,
                (x1 + 5, label_y - 2),
                cv2.FONT_HERSHEY_DUPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

        # Banner superior en caso de No Conformidad
        if len(result.regions) > 0:
            h_img, w_img = annotated.shape[:2]
            banner_text = f"ALERTA: {len(result.regions)} DEFECTO(S) DETECTADO(S) EN TEJA"
            cv2.rectangle(annotated, (0, 0), (w_img, 36), (15, 15, 160), -1)
            cv2.putText(annotated, banner_text, (20, 25), cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

        return annotated

    @staticmethod
    def extract_patches(
        frame: np.ndarray,
        patch_size: Tuple[int, int] = (640, 640),
        overlap: int = 64
    ) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Prepara el fotograma para inspección de alta resolución por parches (tiling),
        fundamental para estudiar defectos pequeños de 1 mm sin reducir la imagen global.
        Retorna lista de (recorte, (x1, y1, x2, y2)).
        """
        h, w = frame.shape[:2]
        pw, ph = patch_size
        step_x = max(1, pw - overlap)
        step_y = max(1, ph - overlap)

        patches = []
        for y in range(0, h, step_y):
            for x in range(0, w, step_x):
                x2 = min(x + pw, w)
                y2 = min(y + ph, h)
                x1 = max(0, x2 - pw)
                y1 = max(0, y2 - ph)
                patch = frame[y1:y2, x1:x2].copy()
                patches.append((patch, (x1, y1, x2, y2)))
        return patches
