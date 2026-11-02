import os
import logging
from typing import Optional
import numpy as np
from src.vision.detection_service import VisionDetector, VisionInferenceResult

logger = logging.getLogger("vision_inspection.anomaly_adapter")

class AnomalyAdapter(VisionDetector):
    """
    Adaptador preparado para modelos de detección de anomalías no supervisados (PatchCore / Anomalib).
    Por diseño ético e ingenieril: NO simula mapas de calor falsos ni inventa anomalías.
    Si no hay pesos o el framework no está instalado, reporta transparentemente que no está disponible.
    """

    def __init__(self, weights_path: str = "models/patchcore_weights.ckpt", threshold: float = 0.5):
        self.weights_path = weights_path
        self.threshold = threshold
        self._is_ready = False
        self._status_message = "Detector de anomalías no disponible (Requiere entrenamiento con láminas sanas y pesos compatibles)."

        if os.path.exists(self.weights_path):
            self._status_message = f"Pesos encontrados en {self.weights_path}, pero el runtime de Anomalib no está inicializado."

    def is_ready(self) -> bool:
        return self._is_ready

    def get_status_info(self) -> str:
        return self._status_message

    def detect(self, frame: np.ndarray) -> VisionInferenceResult:
        return VisionInferenceResult(
            model_name="PatchCore / Anomalib",
            model_version="N/A",
            is_available=False,
            status_message=self._status_message,
            has_detections=False
        )
