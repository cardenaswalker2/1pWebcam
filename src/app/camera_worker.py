import time
import logging
from typing import Optional
import numpy as np
from PySide6.QtCore import QThread, Signal
from src.camera.video_source import VideoSource
from src.vision.detection_service import VisionDetector, VisionInferenceResult

logger = logging.getLogger("vision_inspection.camera_worker")

class CameraWorker(QThread):
    """
    Hilo de adquisición y procesamiento desacoplado de la interfaz gráfica.
    Previene el congelamiento de la GUI de PySide6, descarta fotogramas viejos
    si la inferencia es lenta y calcula métricas reales de rendimiento (FPS, latencia).
    """

    # Señales hacia la GUI
    frame_ready = Signal(np.ndarray, np.ndarray, object)  # (original, anotado, VisionInferenceResult)
    connection_status_changed = Signal(bool, str)          # (conectado, mensaje)
    metrics_updated = Signal(float, float, float, int, int) # (capture_fps, process_fps, latency_ms, w, h)
    error_occurred = Signal(str, str)                      # (error_code, descripcion)

    def __init__(
        self,
        video_source: VideoSource,
        detector: Optional[VisionDetector] = None,
        mm_per_pixel: float = 0.25
    ):
        super().__init__()
        self.video_source = video_source
        self.detector = detector
        self.mm_per_pixel = mm_per_pixel
        self._running = False
        self._paused = False

    def run(self) -> None:
        self._running = True
        logger.info(f"Iniciando captura en hilo de trabajo: {self.video_source.get_source_name()}")

        if not self.video_source.open():
            self._running = False
            self.connection_status_changed.emit(False, "Fallo al conectar con la fuente de video.")
            self.error_occurred.emit("OPEN_FAILED", "No se pudo abrir el flujo de video.")
            return

        self.connection_status_changed.emit(True, f"Conectado: {self.video_source.get_source_name()}")

        frame_count = 0
        fps_timer = time.time()
        capture_fps = 0.0
        process_fps = 0.0

        consecutive_read_failures = 0
        max_read_failures = 10

        while self._running:
            if self._paused:
                time.sleep(0.05)
                continue

            t_capture_start = time.time()
            ret, frame = self.video_source.read()

            if not ret or frame is None or frame.size == 0:
                consecutive_read_failures += 1
                logger.warning(f"Fallo consecutivo de lectura #{consecutive_read_failures}")
                if consecutive_read_failures >= max_read_failures:
                    logger.error("Se excedió el límite de fallos de lectura. Flujo interrumpido.")
                    self.connection_status_changed.emit(False, "Flujo de video interrumpido o desconectado.")
                    self.error_occurred.emit("STREAM_LOST", "Se perdió la señal de video desde la cámara.")
                    break
                time.sleep(0.1)
                continue

            consecutive_read_failures = 0
            frame_count += 1

            # Medición de FPS de captura
            dt_fps = time.time() - fps_timer
            if dt_fps >= 1.0:
                capture_fps = frame_count / dt_fps
                process_fps = capture_fps  # Si no hay retardo
                frame_count = 0
                fps_timer = time.time()

            h, w = frame.shape[:2]

            # Inferencia de detección (si hay un detector configurado)
            t_infer_start = time.time()
            inference_result = None
            frame_annotated = frame.copy()

            if self.detector is not None:
                try:
                    inference_result = self.detector.detect(frame)
                    if inference_result.has_detections:
                        from src.vision.image_processor import ImageProcessor
                        frame_annotated = ImageProcessor.annotate_frame(
                            frame, inference_result, mm_per_pixel=self.mm_per_pixel
                        )
                except Exception as e:
                    logger.error(f"Error procesando fotograma con detector: {e}")

            latency_ms = (time.time() - t_capture_start) * 1000.0

            # Emitir a la interfaz
            self.frame_ready.emit(frame, frame_annotated, inference_result)
            self.metrics_updated.emit(capture_fps, process_fps, latency_ms, w, h)

        self.video_source.release()
        self.connection_status_changed.emit(False, "Captura detenida.")
        logger.info("Hilo de captura finalizado limpiamente.")

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def stop(self) -> None:
        self._running = False
        self.wait(2000)
