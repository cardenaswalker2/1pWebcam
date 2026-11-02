import time
from typing import Optional, Tuple
import cv2
import numpy as np
from src.camera.video_source import VideoSource

class SyntheticSheetSource(VideoSource):
    """
    Fuente sintética que simula el avance de una lámina metálica con texturas de laminación.
    Permite validar la interfaz, tasas de refresco, captura de evidencias y almacenamiento
    sin depender de la conexión física del teléfono.
    """

    def __init__(self, width: int = 1280, height: int = 720, fps: int = 15):
        self.width = width
        self.height = height
        self.fps = fps
        self._is_opened = False
        self._step = 0
        self._last_time = time.time()
        self._sample_frames = []
        self._load_dataset_samples()

    def _load_dataset_samples(self):
        import glob
        import os
        patterns = [
            "data/dataset_yolo/images/val/*.png",
            "data/dataset/test_external/*.jpeg",
            "data/dataset_yolo/images/train/*.png"
        ]
        files = []
        for pat in patterns:
            files.extend(glob.glob(pat))
        
        for f in files[:40]:
            img = cv2.imread(f)
            if img is not None:
                img_resized = cv2.resize(img, (self.width, self.height))
                self._sample_frames.append(img_resized)

    def open(self) -> bool:
        self._is_opened = True
        self._step = 0
        self._last_time = time.time()
        return True

    def is_opened(self) -> bool:
        return self._is_opened

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self._is_opened:
            return False, None

        # Control simple de velocidad de fotogramas
        now = time.time()
        dt = now - self._last_time
        target_dt = 1.0 / self.fps
        if dt < target_dt:
            time.sleep(target_dt - dt)
        self._last_time = time.time()

        if self._sample_frames:
            idx = (self._step // 10) % len(self._sample_frames)
            frame = self._sample_frames[idx].copy()
            # Marca de agua clara
            cv2.putText(
                frame,
                f"MODO PRUEBA DATASET TEJAS - MUESTRA #{idx+1}/{len(self._sample_frames)}",
                (20, 35),
                cv2.FONT_HERSHEY_DUPLEX,
                0.7,
                (0, 220, 255),
                2,
                cv2.LINE_AA
            )
        else:
            frame = np.full((self.height, self.width, 3), 160, dtype=np.uint8)
            cv2.putText(
                frame,
                "MODO DE PRUEBA SINTETICO - SIN IMAGENES DE DATASET",
                (30, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 220),
                2,
                cv2.LINE_AA
            )

        self._step += 1
        return True, frame

    def release(self) -> None:
        self._is_opened = False

    def get_resolution(self) -> Tuple[int, int]:
        return (self.width, self.height)

    def get_source_name(self) -> str:
        return f"Generador Sintético ({self.width}x{self.height} @ {self.fps} FPS)"
