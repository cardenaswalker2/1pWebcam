import os
import pytest
import sqlite3
from src.storage.database import DatabaseManager

def test_database_initialization(tmp_path):
    db_file = str(tmp_path / "test_inspection.db")
    db = DatabaseManager(db_file)
    assert os.path.exists(db_file)

    # Verificar que las tablas fueron creadas
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert "inspection_sessions" in tables
    assert "evidences" in tables
    assert "audit_logs" in tables

def test_session_lifecycle(tmp_path):
    db_file = str(tmp_path / "test_inspection.db")
    db = DatabaseManager(db_file)

    session_id = db.create_session("Sesion_Prueba", "IP_Webcam", "http://192.168.1.100:8080/video")
    assert session_id > 0

    db.close_session(session_id, frames_received=150, notes="Prueba finalizada con éxito")

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT frames_received, end_time FROM inspection_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()

    assert row[0] == 150
    assert row[1] is not None

def test_evidence_persistence_and_review(tmp_path):
    db_file = str(tmp_path / "test_inspection.db")
    db = DatabaseManager(db_file)

    ev_id = db.insert_evidence(
        session_id=1,
        original_image_path="/path/to/img.png",
        width=1920,
        height=1080,
        source_info="IP Webcam",
        model_name="YOLO"
    )
    assert ev_id > 0

    # Consultar evidencias
    evidences = db.get_evidences()
    assert len(evidences) == 1
    assert evidences[0]["review_status"] == "PENDIENTE"

    # Actualizar decisión de revisión
    db.update_evidence_review(ev_id, "NO PASA", "Defecto visible en borde superior")
    updated = db.get_evidences()
    assert updated[0]["review_status"] == "NO PASA"
    assert updated[0]["operator_notes"] == "Defecto visible en borde superior"
    assert updated[0]["reviewed_at"] is not None
