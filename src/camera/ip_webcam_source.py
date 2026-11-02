import time
import logging
from typing import Optional, Tuple
import cv2
import numpy as np
from src.camera.video_source import VideoSource
from src.utils.logging_config import sanitize_url_for_logging

logger = logging.getLogger("vision_inspection.ip_webcam_source")

class IPWebcamSource(VideoSource):
    """
    Fuente de captura de video para cámara de teléfono Android vía IP Webcam.
    Soporta reconexión controlada, backend FFmpeg y liberación limpia.
    """

    def __init__(self, stream_url: str, timeout: float = 3.5):
        self.stream_url = stream_url
        self.timeout = timeout
        self.cap: Optional[cv2.VideoCapture] = None
        self._is_opened = False
        self._last_width = 0
        self._last_height = 0

    def open(self) -> bool:
        self.release()
        safe_url = sanitize_url_for_logging(self.stream_url)
        logger.info(f"Intentando abrir flujo IP Webcam: {safe_url}")

        try:
            # Intento con backend FFmpeg
            self.cap = cv2.VideoCapture(self.stream_url, cv2.CAP_FFMPEG)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.stream_url)

            if self.cap.isOpened():
                # Reducir buffer interno para minimizar latencia en transmisiones en vivo
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                ret, frame = self.cap.read()
                if ret and frame is not None and frame.size > 0:
                    self._last_height, self._last_width = frame.shape[:2]
                    self._is_opened = True
                    logger.info(f"Flujo IP Webcam conectado con éxito ({self._last_width}x{self._last_height})")
                    return True
                else:
                    logger.warning("VideoCapture abierto pero no devolvió fotogramas.")
                    self.release()
                    return False
            else:
                logger.warning(f"No se pudo abrir VideoCapture para {safe_url}")
                self.release()
                return False
        except Exception as e:
            logger.error(f"Excepción al conectar con IP Webcam: {e}")
            self.release()
            return False

    def is_opened(self) -> bool:
        return self._is_opened and self.cap is not None and self.cap.isOpened()

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.is_opened():
            return False, None

        try:
            ret, frame = self.cap.read()
            if ret and frame is not None and frame.size > 0:
                self._last_height, self._last_width = frame.shape[:2]
                return True, frame
            else:
                return False, None
        except Exception as e:
            logger.error(f"Error durante la lectura del fotograma: {e}")
            return False, None

    def release(self) -> None:
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception as e:
                logger.debug(f"Excepción al liberar VideoCapture: {e}")
            self.cap = None
        self._is_opened = False
        logger.debug("Recursos de captura IP Webcam liberados.")

    def get_resolution(self) -> Tuple[int, int]:
        return (self._last_width, self._last_height)

    def get_source_name(self) -> str:
        return f"IP Webcam ({sanitize_url_for_logging(self.stream_url)})"
