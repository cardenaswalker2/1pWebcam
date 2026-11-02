import os
import cv2
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import numpy as np
from src.storage.database import DatabaseManager

logger = logging.getLogger("vision_inspection.evidence_repository")

class EvidenceRepository:
    """
    Gestiona el guardado seguro de archivos de imagen (original y con anotaciones),
    asegurando nombres únicos, carpetas jerárquicas y registro en base de datos.
    """

    def __init__(self, base_evidence_dir: str = "data/evidence", db_manager: Optional[DatabaseManager] = None):
        self.base_evidence_dir = base_evidence_dir
        self.db_manager = db_manager
        os.makedirs(self.base_evidence_dir, exist_ok=True)

    def save_capture(
        self,
        frame_original: np.ndarray,
        session_id: Optional[int] = None,
        source_info: str = "Cámara",
        frame_annotated: Optional[np.ndarray] = None,
        model_name: str = "NINGUNO",
        detections: Optional[list] = None,
        operator_notes: str = ""
    ) -> Dict[str, Any]:
        """
        Guarda la imagen original en alta resolución sin comprimir ni deformar,
        opcionalmente la imagen anotada, y registra la evidencia en la base de datos.
        """
        if frame_original is None or frame_original.size == 0:
            raise ValueError("El fotograma original es nulo o está vacío.")

        h, w = frame_original.shape[:2]
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S_%f")[:19]

        # Carpeta organizada por fecha: data/evidence/YYYY-MM-DD
        day_dir = os.path.join(self.base_evidence_dir, now.strftime("%Y-%m-%d"))
        os.makedirs(day_dir, exist_ok=True)

        original_filename = f"evidencia_{timestamp_str}_orig.png"
        original_filepath = os.path.join(day_dir, original_filename)

        # Guardado de imagen original
        success = cv2.imwrite(original_filepath, frame_original)
        if not success:
            raise IOError(f"No se pudo escribir el archivo de evidencia en {original_filepath}")

        # Guardado de imagen anotada (si existe)
        annotated_filepath = None
        if frame_annotated is not None and frame_annotated.size > 0:
            annotated_filename = f"evidencia_{timestamp_str}_annot.png"
            annotated_filepath = os.path.join(day_dir, annotated_filename)
            cv2.imwrite(annotated_filepath, frame_annotated)

        # Preparar metadatos JSON
        detection_count = len(detections) if detections else 0
        raw_json = json.dumps(detections or [], ensure_ascii=False)

        evidence_id = None
        if self.db_manager:
            evidence_id = self.db_manager.insert_evidence(
                session_id=session_id,
                original_image_path=os.path.abspath(original_filepath),
                annotated_image_path=os.path.abspath(annotated_filepath) if annotated_filepath else None,
                width=w,
                height=h,
                source_info=source_info,
                model_name=model_name,
                detection_count=detection_count,
                raw_inference_json=raw_json,
                operator_notes=operator_notes,
                review_status="PENDIENTE"
            )

        logger.info(f"Evidencia guardada exitosamente: ID={evidence_id}, ruta={original_filepath}")

        return {
            "evidence_id": evidence_id,
            "original_path": original_filepath,
            "annotated_path": annotated_filepath,
            "width": w,
            "height": h,
            "timestamp": now.isoformat(),
            "detection_count": detection_count
        }
