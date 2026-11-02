import pytest
import numpy as np
from src.vision.yolo_adapter import YOLOAdapter
from src.vision.anomaly_adapter import AnomalyAdapter
from src.vision.image_processor import ImageProcessor
from src.vision.detection_service import VisionInferenceResult, DetectionRegion

def test_yolo_adapter_missing_weights():
    adapter = YOLOAdapter(weights_path="non_existent_weights.pt")
    assert not adapter.is_ready()
    assert "no encontrados" in adapter.get_status_info().lower() or "no configurado" in adapter.get_status_info().lower()

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    res = adapter.detect(dummy_frame)
    assert not res.is_available
    assert not res.has_detections
    assert len(res.regions) == 0

def test_anomaly_adapter_status():
    adapter = AnomalyAdapter(weights_path="non_existent_patchcore.ckpt")
    assert not adapter.is_ready()
    assert "no disponible" in adapter.get_status_info().lower()

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    res = adapter.detect(dummy_frame)
    assert not res.is_available
    assert not res.has_detections

def test_image_processor_annotation():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    region = DetectionRegion(x1=50, y1=50, x2=150, y2=150, confidence_or_score=0.85, label="abolladura")
    result = VisionInferenceResult(
        model_name="YOLO_TEST",
        model_version="1.0",
        is_available=True,
        status_message="OK",
        regions=[region],
        has_detections=True
    )
    annotated = ImageProcessor.annotate_frame(frame, result)
    # Comprobar que no es idéntico a la imagen negra vacía
    assert np.any(annotated > 0)
    # Comprobar que el fotograma original no fue alterado
    assert np.all(frame == 0)

def test_image_processor_patches_extraction():
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    patches = ImageProcessor.extract_patches(frame, patch_size=(640, 640), overlap=64)
    assert len(patches) > 0
    patch, bbox = patches[0]
    assert patch.shape == (640, 640, 3)
    x1, y1, x2, y2 = bbox
    assert x2 - x1 == 640
    assert y2 - y1 == 640
