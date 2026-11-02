import os
import sqlite3
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("vision_inspection.database")

class DatabaseManager:
    """
    Gestor de base de datos SQLite para persistencia de sesiones de inspección,
    evidencias de capturas, revisiones de operadores y registros de auditoría.
    """

    def __init__(self, db_path: str = "data/inspection.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Crea el esquema inicial si no existe."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Tabla de sesiones de trabajo/inspección
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS inspection_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_name TEXT NOT NULL,
                        source_type TEXT NOT NULL,
                        source_url TEXT,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        frames_received INTEGER DEFAULT 0,
                        notes TEXT
                    );
                """)

                # Tabla de evidencias fotográficas capturadas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS evidences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        timestamp TEXT NOT NULL,
                        original_image_path TEXT NOT NULL,
                        annotated_image_path TEXT,
                        width INTEGER NOT NULL,
                        height INTEGER NOT NULL,
                        source_info TEXT,
                        model_name TEXT,
                        detection_count INTEGER DEFAULT 0,
                        raw_inference_json TEXT,
                        review_status TEXT DEFAULT 'PENDIENTE',
                        operator_notes TEXT,
                        reviewed_at TEXT,
                        FOREIGN KEY (session_id) REFERENCES inspection_sessions(id)
                    );
                """)

                # Tabla de eventos y errores de diagnóstico
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        message TEXT NOT NULL,
                        details TEXT
                    );
                """)

                conn.commit()
                logger.info(f"Base de datos SQLite inicializada correctamente en {self.db_path}")
        except Exception as e:
            logger.error(f"Error al inicializar la base de datos: {e}")
            raise

    def create_session(self, session_name: str, source_type: str, source_url: str = "") -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO inspection_sessions (session_name, source_type, source_url, start_time)
                VALUES (?, ?, ?, ?)
                """,
                (session_name, source_type, source_url, datetime.now().isoformat())
            )
            conn.commit()
            return cursor.lastrowid

    def close_session(self, session_id: int, frames_received: int = 0, notes: str = "") -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE inspection_sessions
                SET end_time = ?, frames_received = ?, notes = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), frames_received, notes, session_id)
            )
            conn.commit()

    def insert_evidence(
        self,
        session_id: Optional[int],
        original_image_path: str,
        width: int,
        height: int,
        source_info: str,
        annotated_image_path: Optional[str] = None,
        model_name: Optional[str] = "NINGUNO",
        detection_count: int = 0,
        raw_inference_json: str = "{}",
        operator_notes: str = "",
        review_status: str = "PENDIENTE"
    ) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO evidences (
                    session_id, timestamp, original_image_path, annotated_image_path,
                    width, height, source_info, model_name, detection_count,
                    raw_inference_json, review_status, operator_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    datetime.now().isoformat(),
                    original_image_path,
                    annotated_image_path,
                    width,
                    height,
                    source_info,
                    model_name,
                    detection_count,
                    raw_inference_json,
                    review_status,
                    operator_notes
                )
            )
            conn.commit()
            return cursor.lastrowid

    def update_evidence_review(self, evidence_id: int, review_status: str, operator_notes: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE evidences
                SET review_status = ?, operator_notes = ?, reviewed_at = ?
                WHERE id = ?
                """,
                (review_status, operator_notes, datetime.now().isoformat(), evidence_id)
            )
            conn.commit()

    def get_evidences(self, limit: int = 100, review_status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if review_status and review_status != "TODOS":
                cursor.execute(
                    "SELECT * FROM evidences WHERE review_status = ? ORDER BY id DESC LIMIT ?",
                    (review_status, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM evidences ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def log_event(self, event_type: str, message: str, details: str = "") -> None:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO audit_logs (timestamp, event_type, message, details)
                    VALUES (?, ?, ?, ?)
                    """,
                    (datetime.now().isoformat(), event_type, message, details)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Fallo al registrar evento en audit_logs: {e}")
