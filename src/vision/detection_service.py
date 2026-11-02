import abc
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any
import numpy as np

@dataclass
class DetectionRegion:
    """
    Representa una región sospechosa o defecto detectado en coordenadas originales.
    """
    x1: int
    y1: int
    x2: int
    y2: int
    confidence_or_score: float
    label: str = "anomalia"
    is_anomaly_score: bool = False  # Distingue confianza de clasificación vs score de anomalía
    contour: Optional[List[Tuple[int, int]]] = None

@dataclass
class VisionInferenceResult:
    """
    Resultado estructurado e inmutable de la inferencia de visión artificial.
    """
    model_name: str
    model_version: str
    is_available: bool
    status_message: str
    inference_time_ms: float = 0.0
    regions: List[DetectionRegion] = field(default_factory=list)
    has_detections: bool = False
    raw_output: Optional[Any] = None

class VisionDetector(abc.ABC):
    """
    Interfaz abstracta común para detectores (YOLO, PatchCore/Anomalib, heurísticos).
    """

    @abc.abstractmethod
    def is_ready(self) -> bool:
        """Indica si el modelo y sus pesos están cargados y listos para inferir."""
        pass

    @abc.abstractmethod
    def get_status_info(self) -> str:
        """Devuelve un mensaje legible sobre el estado actual del modelo."""
        pass

    @abc.abstractmethod
    def detect(self, frame: np.ndarray) -> VisionInferenceResult:
        """Ejecuta la inferencia sobre el fotograma y devuelve el resultado estructurado."""
        pass
