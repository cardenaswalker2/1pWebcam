import os
import cv2
import numpy as np
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSlider, QCheckBox, QComboBox,
    QTextEdit, QMessageBox, QFileDialog, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor

class EvidenceDetailDialog(QDialog):
    """
    Inspector Metrológico e Interactivo de Evidencias en Alta Definición.
    Permite zoom continuo (1x a 8x), paneo, conmutar vista original/anotada,
    aplicar filtros de contraste CLAHE / umbral binario, y dictaminar veredicto.
    """

    verdict_saved = Signal(int, str, str)  # (evidence_id, veredicto, notas)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inspector Metrológico de Evidencia — Análisis en Detalle HD")
        self.resize(1020, 720)
        self.setMinimumSize(850, 580)

        self.current_frame_orig: Optional[np.ndarray] = None
        self.current_frame_annot: Optional[np.ndarray] = None
        self.current_meta: Dict[str, Any] = {}
        self.zoom_level: float = 1.0

        self._setup_style()
        self._setup_ui()

    def _setup_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0d11;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QWidget {
                color: #d0d0d0;
                font-size: 12px;
            }
            QFrame#cardFrame {
                background-color: #12151b;
                border: 1px solid #232833;
                border-radius: 6px;
            }
            QPushButton {
                background-color: #1c232f;
                border: 1px solid #333f54;
                border-radius: 4px;
                padding: 6px 12px;
                color: #ffffff;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #273549;
                border-color: #007acc;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #1f242d;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #007acc;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #4da6ff;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
            QComboBox, QTextEdit {
                background-color: #161920;
                border: 1px solid #333f54;
                border-radius: 4px;
                padding: 4px 8px;
                color: #ffffff;
            }
        """)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # 1. Cabecera con datos de la evidencia
        header = QFrame()
        header.setObjectName("cardFrame")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10, 8, 10, 8)

        col_title = QVBoxLayout()
        self.lbl_title = QLabel("EVIDENCIA #-- | ANALIZADOR METROLÓGICO INDUSTRIAL")
        self.lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #4da6ff;")
        self.lbl_meta = QLabel("Fecha: -- | Fuente: -- | Resolución: --")
        self.lbl_meta.setStyleSheet("font-size: 11px; color: #7f8c9b;")
        col_title.addWidget(self.lbl_title)
        col_title.addWidget(self.lbl_meta)
        h_layout.addLayout(col_title)
        h_layout.addStretch()

        self.badge_status = QLabel("REVISIÓN PENDIENTE")
        self.badge_status.setStyleSheet("background-color: #3b2b18; color: #ffb74d; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        h_layout.addWidget(self.badge_status)
        main_layout.addWidget(header)

        # 2. Cuerpo: Visor Óptico a la izquierda + Panel de Control y Auditoría a la derecha
        body_layout = QHBoxLayout()
        body_layout.setSpacing(12)

        # Visor óptico central
        view_frame = QFrame()
        view_frame.setObjectName("cardFrame")
        v_layout = QVBoxLayout(view_frame)
        v_layout.setContentsMargins(8, 8, 8, 8)

        self.lbl_viewport = QLabel()
        self.lbl_viewport.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_viewport.setAlignment(Qt.AlignCenter)
        self.lbl_viewport.setStyleSheet("background-color: #050608; border-radius: 4px;")
        v_layout.addWidget(self.lbl_viewport, stretch=5)

        # Barra de herramientas del visor (Zoom y Filtros)
        tools_row = QHBoxLayout()
        self.chk_show_hud = QCheckBox("Mostrar Cajas HUD")
        self.chk_show_hud.setChecked(True)
        self.chk_show_hud.toggled.connect(self._render_view)
        tools_row.addWidget(self.chk_show_hud)

        self.chk_filter_clahe = QCheckBox("Filtro Contraste CLAHE")
        self.chk_filter_clahe.toggled.connect(self._render_view)
        tools_row.addWidget(self.chk_filter_clahe)

        tools_row.addSpacing(15)
        tools_row.addWidget(QLabel("Zoom HD:"))
        self.slider_zoom = QSlider(Qt.Horizontal)
        self.slider_zoom.setRange(10, 80)  # 1.0x a 8.0x
        self.slider_zoom.setValue(10)
        self.slider_zoom.valueChanged.connect(self._on_zoom_changed)
        tools_row.addWidget(self.slider_zoom)

        self.lbl_zoom_val = QLabel("1.0x")
        self.lbl_zoom_val.setStyleSheet("color: #4da6ff; font-weight: bold; min-width: 35px;")
        tools_row.addWidget(self.lbl_zoom_val)

        self.btn_reset_zoom = QPushButton("1:1")
        self.btn_reset_zoom.setToolTip("Restablecer zoom normal")
        self.btn_reset_zoom.clicked.connect(lambda: self.slider_zoom.setValue(10))
        tools_row.addWidget(self.btn_reset_zoom)

        v_layout.addLayout(tools_row)
        body_layout.addWidget(view_frame, stretch=5)

        # Panel lateral de Auditoría y Acciones
        audit_frame = QFrame()
        audit_frame.setObjectName("cardFrame")
        audit_frame.setMinimumWidth(280)
        audit_frame.setMaximumWidth(340)
        a_layout = QVBoxLayout(audit_frame)
        a_layout.setContentsMargins(12, 12, 12, 12)
        a_layout.setSpacing(10)

        lbl_a_title = QLabel("DICTAMEN Y METROLOGÍA")
        lbl_a_title.setStyleSheet("font-weight: bold; color: #58a6ff; font-size: 13px;")
        a_layout.addWidget(lbl_a_title)

        self.lbl_defect_summary = QLabel("Defectos detectados: 0\nTamaño estimado: -- mm\nCerteza IA: --%")
        self.lbl_defect_summary.setStyleSheet("background-color: #171b22; border: 1px solid #2d333b; border-radius: 4px; padding: 8px; color: #ff9999; font-weight: bold;")
        a_layout.addWidget(self.lbl_defect_summary)

        a_layout.addWidget(QLabel("<b>Veredicto del Inspector de Calidad:</b>"))
        self.combo_verdict = QComboBox()
        self.combo_verdict.addItems([
            "CONFIRMAR RECHAZO (NO CONFORME)",
            "LIBERAR POR CONCESIÓN (ACEPTADO)",
            "DESCARTAR (FALSA ALERTA / POLVO)"
        ])
        a_layout.addWidget(self.combo_verdict)

        a_layout.addWidget(QLabel("<b>Notas del Operador:</b>"))
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Comentarios del lote, turno o motivo del dictamen...")
        self.txt_notes.setMaximumHeight(85)
        a_layout.addWidget(self.txt_notes)

        self.btn_save_verdict = QPushButton("✔ Validar e Integrar a Reporte")
        self.btn_save_verdict.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px;")
        self.btn_save_verdict.clicked.connect(self._on_save_verdict)
        a_layout.addWidget(self.btn_save_verdict)

        a_layout.addSpacing(10)
        lbl_actions = QLabel("ACCIONES DE ARCHIVO")
        lbl_actions.setStyleSheet("font-weight: bold; color: #8b949e; font-size: 11px;")
        a_layout.addWidget(lbl_actions)

        self.btn_export_image = QPushButton("💾 Guardar Copia en JPG/PNG...")
        self.btn_export_image.clicked.connect(self._export_image)
        a_layout.addWidget(self.btn_export_image)

        self.btn_open_folder = QPushButton("📁 Ver Archivo en Disco")
        self.btn_open_folder.clicked.connect(self._open_in_explorer)
        a_layout.addWidget(self.btn_open_folder)

        a_layout.addStretch()
        body_layout.addWidget(audit_frame, stretch=2)
        main_layout.addLayout(body_layout)

    def load_evidence(self, frame_orig: np.ndarray, frame_annot: Optional[np.ndarray], meta: dict):
        """Carga y visualiza una evidencia completa."""
        self.current_frame_orig = frame_orig
        self.current_frame_annot = frame_annot if frame_annot is not None else frame_orig
        self.current_meta = meta
        self.zoom_level = 1.0
        self.slider_zoom.setValue(10)

        ev_id = meta.get("evidence_id", "--")
        time_str = meta.get("time_str", "--")
        source = meta.get("source_info", "En Vivo")
        h, w = frame_orig.shape[:2] if frame_orig is not None else (0, 0)

        self.lbl_title.setText(f"EVIDENCIA #{ev_id} | INSPECCIÓN METROLÓGICA DETALLADA")
        self.lbl_meta.setText(f"Hora: {time_str} | Fuente: {source} | Resolución nativa: {w}x{h} px")

        defects = meta.get("detections", [])
        num_def = len(defects)
        summary_text = f"Defectos detectados: {num_def}\n"
        if num_def > 0:
            first = defects[0]
            label = first.get("label", "defecto")
            conf = first.get("confidence", 0.0)
            summary_text += f"Defecto principal: {label.upper()}\nCerteza IA: {conf:.1%}"
        else:
            summary_text += "Superficie de teja sin no conformidades críticas."
        self.lbl_defect_summary.setText(summary_text)

        self._render_view()

    def _on_zoom_changed(self, val: int):
        self.zoom_level = val / 10.0
        self.lbl_zoom_val.setText(f"{self.zoom_level:.1f}x")
        self._render_view()

    def _render_view(self):
        if self.current_frame_orig is None:
            return

        base = self.current_frame_annot.copy() if self.chk_show_hud.isChecked() else self.current_frame_orig.copy()

        # Aplicar filtro de contraste CLAHE si está activo
        if self.chk_filter_clahe.isChecked():
            lab = cv2.cvtColor(base, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            base = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # Aplicar Zoom centrado
        h, w = base.shape[:2]
        if self.zoom_level > 1.0:
            crop_w = int(w / self.zoom_level)
            crop_h = int(h / self.zoom_level)
            x1 = max(0, (w - crop_w) // 2)
            y1 = max(0, (h - crop_h) // 2)
            base = base[y1:y1 + crop_h, x1:x1 + crop_w]

        rgb = cv2.cvtColor(base, cv2.COLOR_BGR2RGB)
        rh, rw, rch = rgb.shape
        qimg = QImage(rgb.data, rw, rh, rch * rw, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)

        scaled = pix.scaled(
            self.lbl_viewport.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.lbl_viewport.setPixmap(scaled)

    def _on_save_verdict(self):
        ev_id = self.current_meta.get("evidence_id", 0)
        verdict = self.combo_verdict.currentText()
        notes = self.txt_notes.toPlainText().strip()
        self.verdict_saved.emit(ev_id, verdict, notes)
        self.badge_status.setText("AUDITADO / VALIDADO")
        self.badge_status.setStyleSheet("background-color: #1a382b; color: #5cdb95; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        QMessageBox.information(
            self,
            "Dictamen Registrado",
            f"✅ Se ha validado la Evidencia #{ev_id}.\n\nVeredicto: {verdict}\nNotas: {notes or 'Sin observaciones'}"
        )

    def _export_image(self):
        if self.current_frame_orig is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Evidencia en Alta Definición",
            f"evidencia_{self.current_meta.get('evidence_id', 'hd')}.png",
            "Imágenes PNG (*.png);;Imágenes JPG (*.jpg)"
        )
        if path:
            img_to_save = self.current_frame_annot if self.chk_show_hud.isChecked() else self.current_frame_orig
            cv2.imwrite(path, img_to_save)
            QMessageBox.information(self, "Exportación Exitosa", f"Imagen guardada en:\n{path}")

    def _open_in_explorer(self):
        orig_path = self.current_meta.get("original_path")
        if orig_path and os.path.exists(orig_path):
            import subprocess
            subprocess.run(["explorer", "/select,", os.path.normpath(orig_path)])
        else:
            QMessageBox.information(self, "Ubicación", "El archivo de imagen se encuentra en la carpeta data/evidence.")
