import logging
from typing import Optional, Tuple
import cv2
import numpy as np
from src.camera.video_source import VideoSource

logger = logging.getLogger("vision_inspection.usb_camera_source")

class USBCameraSource(VideoSource):
    """
    Fuente de captura directa para cámaras web USB o cámaras del dispositivo (DirectShow / V4L2).
    Permite seleccionar cualquier dispositivo por índice (0, 1, 2...) y conectarse de inmediato.
    """

    def __init__(self, camera_index: int = 0, width: int = 1280, height: int = 720):
        self.camera_index = camera_index
        self.preferred_width = width
        self.preferred_height = height
        self.cap: Optional[cv2.VideoCapture] = None
        self._is_opened = False
        self._last_width = 0
        self._last_height = 0

    def open(self) -> bool:
        self.release()
        logger.info(f"Intentando abrir cámara USB/Dispositivo (Índice {self.camera_index})...")

        try:
            # En Windows cv2.CAP_DSHOW suele ser el más confiable y rápido para cámaras USB
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_index)

            if self.cap.isOpened():
                # Intentar configurar resolución preferida si el sensor lo admite
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.preferred_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.preferred_height)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                ret, frame = self.cap.read()
                if ret and frame is not None and frame.size > 0:
                    self._last_height, self._last_width = frame.shape[:2]
                    self._is_opened = True
                    logger.info(f"Cámara USB #{self.camera_index} conectada con éxito ({self._last_width}x{self._last_height})")
                    return True
                else:
                    logger.warning(f"Cámara USB #{self.camera_index} abierta pero no entregó fotogramas.")
                    self.release()
                    return False
            else:
                logger.warning(f"No se pudo abrir el dispositivo de video #{self.camera_index}")
                self.release()
                return False
        except Exception as e:
            logger.error(f"Excepción al abrir cámara USB #{self.camera_index}: {e}")
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
            return False, None
        except Exception as e:
            logger.error(f"Error leyendo de cámara USB #{self.camera_index}: {e}")
            return False, None

    def release(self) -> None:
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception as e:
                logger.debug(f"Excepción al liberar VideoCapture USB: {e}")
            self.cap = None
        self._is_opened = False
        logger.debug(f"Cámara USB #{self.camera_index} liberada.")

    def get_resolution(self) -> Tuple[int, int]:
        return (self._last_width, self._last_height)

    def get_source_name(self) -> str:
        return f"Cámara USB #{self.camera_index} ({self._last_width}x{self._last_height})"
