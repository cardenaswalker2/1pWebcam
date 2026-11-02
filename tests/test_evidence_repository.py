import os
import cv2
import numpy as np
import pytest
from src.storage.evidence_repository import EvidenceRepository
from src.storage.database import DatabaseManager

def test_evidence_repository_save(tmp_path):
    db_file = str(tmp_path / "test_db.db")
    evidence_dir = str(tmp_path / "evidences")

    db = DatabaseManager(db_file)
    repo = EvidenceRepository(evidence_dir, db)

    # Crear fotograma sintético
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:] = (100, 150, 200)

    result = repo.save_capture(
        frame_original=frame,
        session_id=None,
        source_info="Prueba unitaria"
    )

    assert result["evidence_id"] is not None
    assert os.path.exists(result["original_path"])
    assert result["width"] == 640
    assert result["height"] == 480

    # Comprobar que el archivo guardado tiene las dimensiones correctas
    loaded = cv2.imread(result["original_path"])
    assert loaded.shape == (480, 640, 3)

def test_evidence_repository_empty_frame_raises(tmp_path):
    repo = EvidenceRepository(str(tmp_path / "evidences"))
    with pytest.raises(ValueError):
        repo.save_capture(np.array([]))
