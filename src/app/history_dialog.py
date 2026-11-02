import os
import cv2
import json
import numpy as np
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QTextEdit, QMessageBox, QSplitter, QSlider, QCheckBox, QFrame,
    QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QFont
from src.storage.database import DatabaseManager

class EvidenceHistoryDialog(QDialog):
    """
    Consola de Auditoría y Control de Calidad de Evidencias Históricas.
    Diseño profesional oscuro, visor interactivo con zoom digital (1x a 5x),
    filtro de realce CLAHE, alternancia entre foto original / anotada con cajas,
    abridor nativo en el visor de Windows e integración con la Terminal de Calidad.
    """

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Historial de Evidencias e Inspección de Calidad — Auditoría ISO 9001")
        self.resize(1180, 780)
        self.setMinimumSize(980, 620)
        self.current_evidence: Optional[Dict[str, Any]] = None
        self.evidences_cache: List[Dict[str, Any]] = []

        # Estado de la imagen en inspección
        self._loaded_raw_img: Optional[np.ndarray] = None
        self._loaded_annot_img: Optional[np.ndarray] = None
        self.zoom_factor: float = 1.0

        self._setup_style()
        self._setup_ui()
        self._load_evidences()

    def _setup_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0e1116;
                color: #e6edf3;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #c9d1d9;
                font-size: 13px;
            }
            QTableWidget {
                background-color: #161b22;
                border: 1px solid #30363d;
                color: #f0f6fc;
                gridline-color: #21262d;
                selection-background-color: #1f6feb;
                selection-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #21262d;
                color: #58a6ff;
                padding: 6px;
                border: 1px solid #30363d;
                font-weight: bold;
                font-size: 12px;
            }
            QComboBox, QTextEdit {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 5px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #21262d;
                border: 1px solid #363b42;
                border-radius: 4px;
                padding: 6px 12px;
                color: #e6edf3;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #58a6ff;
            }
            QSlider::groove:horizontal {
                height: 5px;
                background: #21262d;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #1f6feb;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #58a6ff;
                width: 14px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 7px;
            }
        """)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # 1. Barra superior de filtros y acciones
        filter_frame = QFrame()
        filter_frame.setStyleSheet("background-color: #161b22; border-radius: 6px; padding: 4px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(10, 4, 10, 4)

        lbl_f = QLabel("Filtrar por estado:")
        lbl_f.setStyleSheet("font-weight: bold; color: #58a6ff;")
        filter_layout.addWidget(lbl_f)

        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["TODOS", "PENDIENTE", "PASA", "NO PASA", "FALSA ALERTA"])
        self.combo_filter.currentTextChanged.connect(self._load_evidences)
        filter_layout.addWidget(self.combo_filter)

        self.btn_refresh = QPushButton("🔄 Actualizar Bitácora")
        self.btn_refresh.clicked.connect(self._load_evidences)
        filter_layout.addWidget(self.btn_refresh)

        filter_layout.addStretch()

        self.lbl_record_count = QLabel("Mostrando 0 evidencias")
        self.lbl_record_count.setStyleSheet("color: #8b949e; font-size: 12px;")
        filter_layout.addWidget(self.lbl_record_count)

        main_layout.addWidget(filter_frame)

        # 2. Splitter central: Tabla a la izquierda, visor y formulario a la derecha
        splitter = QSplitter(Qt.Horizontal)

        # A. TABLA DE EVIDENCIAS
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Fecha / Hora", "Resolución", "Modelo IA", "Defectos", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().resizeSection(0, 50)
        self.table.horizontalHeader().resizeSection(1, 140)
        self.table.horizontalHeader().resizeSection(2, 95)
        self.table.horizontalHeader().resizeSection(3, 100)
        self.table.horizontalHeader().resizeSection(4, 75)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        left_layout.addWidget(self.table)

        splitter.addWidget(left_widget)

        # B. PANEL DE VISUALIZACIÓN DETALLADA Y AUDITORÍA
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # Contenedor del visor óptico
        viewer_box = QFrame()
        viewer_box.setStyleSheet("background-color: #05070a; border: 1px solid #30363d; border-radius: 6px;")
        vb_layout = QVBoxLayout(viewer_box)
        vb_layout.setContentsMargins(6, 6, 6, 6)

        self.lbl_image_preview = QLabel("Seleccione una evidencia de la tabla para inspeccionar")
        self.lbl_image_preview.setAlignment(Qt.AlignCenter)
        self.lbl_image_preview.setStyleSheet("color: #484f58; font-weight: bold;")
        self.lbl_image_preview.setMinimumSize(460, 360)
        vb_layout.addWidget(self.lbl_image_preview)

        # Barra de herramientas del visor (Zoom, Alternar anotación, Abrir imagen original)
        tool_layout = QHBoxLayout()
        self.chk_annotated = QCheckBox("Mostrar Cajas IA")
        self.chk_annotated.setChecked(True)
        self.chk_annotated.toggled.connect(self._render_preview)
        tool_layout.addWidget(self.chk_annotated)

        self.chk_clahe = QCheckBox("Realce de Fisuras")
        self.chk_clahe.toggled.connect(self._render_preview)
        tool_layout.addWidget(self.chk_clahe)

        tool_layout.addStretch()

        tool_layout.addWidget(QLabel("Zoom:"))
        self.slider_zoom = QSlider(Qt.Horizontal)
        self.slider_zoom.setRange(10, 50)  # 1.0x a 5.0x
        self.slider_zoom.setValue(10)
        self.slider_zoom.setFixedWidth(100)
        self.slider_zoom.valueChanged.connect(self._on_zoom_changed)
        tool_layout.addWidget(self.slider_zoom)
        self.lbl_zoom_txt = QLabel("1.0x")
        self.lbl_zoom_txt.setFixedWidth(35)
        tool_layout.addWidget(self.lbl_zoom_txt)

        self.btn_open_external = QPushButton("🔍 Abrir en Pantalla Completa")
        self.btn_open_external.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold;")
        self.btn_open_external.clicked.connect(self._open_in_system_viewer)
        tool_layout.addWidget(self.btn_open_external)

        vb_layout.addLayout(tool_layout)
        right_layout.addWidget(viewer_box, stretch=3)

        # Panel de Auditoría y Dictamen Humano
        audit_box = QFrame()
        audit_box.setStyleSheet("background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 8px;")
        ab_layout = QVBoxLayout(audit_box)
        ab_layout.setSpacing(6)

        header_audit = QHBoxLayout()
        self.lbl_evidence_meta = QLabel("Evidencia: Ninguna seleccionada")
        self.lbl_evidence_meta.setStyleSheet("font-weight: bold; color: #ff7b72;")
        header_audit.addWidget(self.lbl_evidence_meta)

        header_audit.addStretch()

        header_audit.addWidget(QLabel("Dictamen:"))
        self.combo_decision = QComboBox()
        self.combo_decision.addItems(["PENDIENTE", "PASA", "NO PASA", "FALSA ALERTA"])
        header_audit.addWidget(self.combo_decision)
        ab_layout.addLayout(header_audit)

        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Notas técnicas del auditor o inspector de turno...")
        self.txt_notes.setMaximumHeight(50)
        ab_layout.addWidget(self.txt_notes)

        # Botones de acción inferior
        action_row = QHBoxLayout()
        self.btn_save_review = QPushButton("✔ Guardar Dictamen")
        self.btn_save_review.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 7px;")
        self.btn_save_review.clicked.connect(self._save_review)
        action_row.addWidget(self.btn_save_review)

        self.btn_open_report = QPushButton("📄 Ficha Forense / Informe")
        self.btn_open_report.setStyleSheet("background-color: #8957e5; color: white; font-weight: bold; padding: 7px;")
        self.btn_open_report.clicked.connect(self._open_detailed_report)
        action_row.addWidget(self.btn_open_report)

        self.btn_open_folder = QPushButton("📁 Abrir en Carpeta")
        self.btn_open_folder.clicked.connect(self._open_file_location)
        action_row.addWidget(self.btn_open_folder)

        ab_layout.addLayout(action_row)
        right_layout.addWidget(audit_box, stretch=1)

        splitter.addWidget(right_widget)
        splitter.setSizes([520, 620])
        main_layout.addWidget(splitter)

    def _load_evidences(self):
        status_filter = self.combo_filter.currentText()
        evidences = self.db_manager.get_evidences(limit=250, review_status=status_filter)
        self.evidences_cache = evidences
        self.lbl_record_count.setText(f"Mostrando {len(evidences)} evidencias")

        self.table.setRowCount(len(evidences))
        for row, ev in enumerate(evidences):
            self.table.setItem(row, 0, QTableWidgetItem(str(ev["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(str(ev["timestamp"][:19]).replace("T", " ")))
            self.table.setItem(row, 2, QTableWidgetItem(f"{ev['width']}x{ev['height']}"))
            self.table.setItem(row, 3, QTableWidgetItem(str(ev["model_name"])))
            
            # Formato de defectos con color
            def_item = QTableWidgetItem(str(ev["detection_count"]))
            if ev["detection_count"] > 0:
                def_item.setForeground(Qt.red)
            self.table.setItem(row, 4, def_item)

            st_item = QTableWidgetItem(str(ev["review_status"]))
            if ev["review_status"] == "PASA":
                st_item.setForeground(Qt.green)
            elif ev["review_status"] == "NO PASA":
                st_item.setForeground(Qt.red)
            self.table.setItem(row, 5, st_item)

    def _on_row_selected(self):
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if row < len(self.evidences_cache):
            self.current_evidence = self.evidences_cache[row]
            self._display_selected_evidence()

    def _display_selected_evidence(self):
        if not self.current_evidence:
            return

        ev_id = self.current_evidence["id"]
        def_count = self.current_evidence["detection_count"]
        status = self.current_evidence.get("review_status", "PENDIENTE")
        res = f"{self.current_evidence['width']}x{self.current_evidence['height']}"

        self.lbl_evidence_meta.setText(f"Evidencia #{ev_id} | {def_count} Defecto(s) | Res: {res}")

        # Cargar imágenes originales y anotadas en memoria
        orig_path = self.current_evidence.get("original_image_path")
        annot_path = self.current_evidence.get("annotated_image_path")

        self._loaded_raw_img = cv2.imread(orig_path) if orig_path and os.path.exists(orig_path) else None
        self._loaded_annot_img = cv2.imread(annot_path) if annot_path and os.path.exists(annot_path) else None

        # Reset de zoom al cambiar de imagen
        self.slider_zoom.setValue(10)
        self.zoom_factor = 1.0
        self.lbl_zoom_txt.setText("1.0x")

        self._render_preview()

        # Cargar datos al formulario
        idx = self.combo_decision.findText(status)
        if idx >= 0:
            self.combo_decision.setCurrentIndex(idx)
        self.txt_notes.setText(self.current_evidence.get("operator_notes") or "")

    def _on_zoom_changed(self, val: int):
        self.zoom_factor = val / 10.0
        self.lbl_zoom_txt.setText(f"{self.zoom_factor:.1f}x")
        self._render_preview()

    def _render_preview(self):
        # Elegir si mostramos con cajas de IA o foto limpia
        if self.chk_annotated.isChecked() and self._loaded_annot_img is not None:
            img = self._loaded_annot_img.copy()
        elif self._loaded_raw_img is not None:
            img = self._loaded_raw_img.copy()
        else:
            self.lbl_image_preview.setText("Archivo de imagen no encontrado en disco.")
            return

        # Filtro de realce de fisuras
        if self.chk_clahe.isChecked():
            try:
                lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                cl = clahe.apply(l)
                img = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)
            except Exception:
                pass

        # Aplicar recorte de Zoom
        if self.zoom_factor > 1.0:
            h, w = img.shape[:2]
            nw = int(w / self.zoom_factor)
            nh = int(h / self.zoom_factor)
            sx = (w - nw) // 2
            sy = (h - nh) // 2
            img = img[sy:sy+nh, sx:sx+nw]

        # Convertir a QPixmap y escalar
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        rh, rw, rc = rgb.shape
        qimg = QImage(rgb.data, rw, rh, rc * rw, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        scaled = pixmap.scaled(
            self.lbl_image_preview.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.lbl_image_preview.setPixmap(scaled)

    def _open_in_system_viewer(self):
        """Abre la imagen en máxima resolución en el visor nativo de Windows (Fotos / Paint)."""
        if not self.current_evidence:
            QMessageBox.warning(self, "Aviso", "Seleccione primero una evidencia de la tabla.")
            return

        img_path = self.current_evidence.get("annotated_image_path") if self.chk_annotated.isChecked() else self.current_evidence.get("original_image_path")
        if not img_path or not os.path.exists(img_path):
            img_path = self.current_evidence.get("original_image_path")

        if img_path and os.path.exists(img_path):
            try:
                os.startfile(os.path.abspath(img_path))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el visor: {e}")
        else:
            QMessageBox.warning(self, "Error", "El archivo de imagen no se encuentra en disco.")

    def _open_file_location(self):
        if not self.current_evidence:
            return
        img_path = self.current_evidence.get("original_image_path")
        if img_path and os.path.exists(img_path):
            folder = os.path.dirname(os.path.abspath(img_path))
            try:
                os.startfile(folder)
            except Exception:
                pass

    def _save_review(self):
        if not self.current_evidence:
            QMessageBox.warning(self, "Aviso", "Seleccione primero una evidencia de la lista.")
            return

        evidence_id = self.current_evidence["id"]
        status = self.combo_decision.currentText()
        notes = self.txt_notes.toPlainText().strip()

        try:
            self.db_manager.update_evidence_review(evidence_id, status, notes)
            QMessageBox.information(self, "Éxito", f"Decisión #{status} registrada para la evidencia #{evidence_id}.")
            self._load_evidences()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la revisión: {e}")

    def _open_detailed_report(self):
        if not self.current_evidence:
            QMessageBox.warning(self, "Aviso", "Seleccione primero una evidencia de la lista.")
            return

        img_path = self.current_evidence.get("original_image_path")
        if not img_path or not os.path.exists(img_path):
            img_path = self.current_evidence.get("annotated_image_path")

        if not img_path or not os.path.exists(img_path):
            QMessageBox.warning(self, "Aviso", "El archivo de imagen no existe en el almacenamiento.")
            return

        from src.app.image_report_dialog import ImageInspectionReportDialog
        # Usar el detector si está disponible en el padre
        detector = getattr(self.parent(), "detector", None)
        mm_px = getattr(self.parent(), "settings", None)
        mm_val = getattr(mm_px.vision, "mm_per_pixel", 0.25) if mm_px else 0.25

        dlg = ImageInspectionReportDialog(
            detector=detector,
            mm_per_pixel=mm_val,
            initial_image_path=img_path,
            parent=self
        )
        dlg.exec()
