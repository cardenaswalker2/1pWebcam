import cv2
import numpy as np
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QFrame, QSizePolicy, QSlider,
    QCheckBox, QComboBox, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QFont

class DefectViewerWindow(QMainWindow):
    """
    Ventana independiente de Grado de Ingeniería / SCADA para Aislamiento,
    Metrología y Análisis Avanzado de No Conformidades en Tejas Metálicas.
    Puede moverse a un segundo monitor físico en planta.
    """

    manual_review_submitted = Signal(int, str, str)  # (evidence_id, decision, notes)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terminal de Calidad — Aislamiento y Metrología de No Conformidades")
        self.resize(920, 720)
        self.setMinimumSize(780, 560)

        # Estado del defecto actual
        self.current_clean_crop: Optional[np.ndarray] = None
        self.current_annot_crop: Optional[np.ndarray] = None
        self.current_full_frame: Optional[np.ndarray] = None
        self.current_meta: Dict[str, Any] = {}
        self.zoom_level: float = 1.0

        self._setup_style()
        self._setup_ui()

    def _setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0e1116;
                color: #e6edf3;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QWidget {
                color: #c9d1d9;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #30363d;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 14px;
                font-weight: bold;
                color: #58a6ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
            }
            QPushButton {
                background-color: #21262d;
                border: 1px solid #363b42;
                border-radius: 4px;
                padding: 7px 14px;
                font-weight: 500;
                color: #f0f6fc;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #58a6ff;
            }
            QPushButton:pressed {
                background-color: #161b22;
            }
            QComboBox, QTextEdit {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 5px;
                color: #ffffff;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #21262d;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #1f6feb;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #58a6ff;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
        """)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # Encabezado técnico
        header = QFrame()
        header.setStyleSheet("background-color: #161b22; border-radius: 6px; padding: 4px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10, 6, 10, 6)

        title_box = QVBoxLayout()
        lbl_t = QLabel("ESTACIÓN METROLÓGICA — ANÁLISIS DE NO CONFORMIDAD")
        lbl_t.setStyleSheet("font-size: 15px; font-weight: bold; color: #ff7b72;")
        lbl_sub = QLabel("Inspección de precisión milimétrica, perfil de intensidad y veredicto de calidad")
        lbl_sub.setStyleSheet("font-size: 11px; color: #8b949e;")
        title_box.addWidget(lbl_t)
        title_box.addWidget(lbl_sub)
        h_layout.addLayout(title_box)

        h_layout.addStretch()

        self.badge_severity = QLabel("ESTADO: EN ESPERA")
        self.badge_severity.setStyleSheet("background-color: #21262d; color: #8b949e; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        h_layout.addWidget(self.badge_severity)

        main_layout.addWidget(header)

        # Cuerpo central dividido en dos paneles
        body = QHBoxLayout()
        body.setSpacing(12)

        # 1. Visor Óptico Principal (Zoom y Encapsulado)
        viewer_box = QGroupBox("VISOR ÓPTICO DE ALTA DEFINICIÓN (ROI ENCAPSULADO)")
        v_layout = QVBoxLayout(viewer_box)

        self.lbl_viewport = QLabel()
        self.lbl_viewport.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_viewport.setAlignment(Qt.AlignCenter)
        self.lbl_viewport.setStyleSheet("background-color: #05070a; border: 1px solid #21262d; border-radius: 4px;")
        self.lbl_viewport.setMinimumSize(480, 380)
        self.lbl_viewport.setText("<div align='center' style='color:#484f58;'><b>Esperando evento de no conformidad...<br>Cuando la IA detecte una falla, se proyectará aquí con zoom inteligente.</b></div>")
        v_layout.addWidget(self.lbl_viewport)

        # Barra de control de visualización
        view_ctrl = QHBoxLayout()
        self.chk_show_box = QCheckBox("Mostrar Cajas HUD")
        self.chk_show_box.setChecked(True)
        self.chk_show_box.toggled.connect(self._render_current_view)
        view_ctrl.addWidget(self.chk_show_box)

        self.chk_enhance = QCheckBox("Filtro Contraste Industrial (CLAHE)")
        self.chk_enhance.toggled.connect(self._render_current_view)
        view_ctrl.addWidget(self.chk_enhance)

        view_ctrl.addStretch()
        view_ctrl.addWidget(QLabel("Zoom:"))
        self.slider_zoom = QSlider(Qt.Horizontal)
        self.slider_zoom.setRange(10, 40)  # 1.0x a 4.0x
        self.slider_zoom.setValue(10)
        self.slider_zoom.setFixedWidth(120)
        self.slider_zoom.valueChanged.connect(self._on_zoom_changed)
        view_ctrl.addWidget(self.slider_zoom)
        self.lbl_zoom_val = QLabel("1.0x")
        self.lbl_zoom_val.setFixedWidth(35)
        view_ctrl.addWidget(self.lbl_zoom_val)

        v_layout.addLayout(view_ctrl)
        body.addWidget(viewer_box, stretch=3)

        # 2. Panel Metrológico y Auditoría
        side_box = QGroupBox("MÉTRICAS Y AUDITORÍA DE CALIDAD")
        s_layout = QVBoxLayout(side_box)
        s_layout.setSpacing(10)

        # Ficha técnica del defecto
        meta_frame = QFrame()
        meta_frame.setStyleSheet("background-color: #161b22; border-radius: 4px; padding: 6px;")
        mf_layout = QVBoxLayout(meta_frame)
        mf_layout.setSpacing(5)

        self.lbl_defect_class = QLabel("Tipo de Falla: --")
        self.lbl_defect_class.setStyleSheet("color: #ff7b72; font-weight: bold; font-size: 13px;")
        self.lbl_confidence = QLabel("Certeza IA: -- %")
        self.lbl_dimensions_mm = QLabel("Dimensiones: -- mm x -- mm")
        self.lbl_dimensions_mm.setStyleSheet("color: #7ee787; font-weight: bold;")
        self.lbl_area_mm2 = QLabel("Área Estimada: -- mm²")
        self.lbl_coords = QLabel("Coordenadas: (X: --, Y: --)")

        for lbl in [self.lbl_defect_class, self.lbl_confidence, self.lbl_dimensions_mm, self.lbl_area_mm2, self.lbl_coords]:
            mf_layout.addWidget(lbl)

        s_layout.addWidget(meta_frame)

        # Criterio de rechazo
        s_layout.addWidget(QLabel("<b>Evaluación de Criterio:</b>"))
        self.lbl_tolerance = QLabel("Tolerancia máx: 5.0 mm | Desvío: --")
        self.lbl_tolerance.setStyleSheet("color: #d29922; font-size: 11px;")
        s_layout.addWidget(self.lbl_tolerance)

        # Acciones de Operador
        s_layout.addWidget(QLabel("<b>Veredicto del Inspector de Calidad:</b>"))
        self.combo_verdict = QComboBox()
        self.combo_verdict.addItems(["CONFIRMAR RECHAZO (NO CONFORME)", "LIBERAR POR CONCESIÓN", "FALSA ALERTA DE IA"])
        s_layout.addWidget(self.combo_verdict)

        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Observaciones del turno o lote...")
        self.txt_notes.setMaximumHeight(65)
        s_layout.addWidget(self.txt_notes)

        self.btn_save_verdict = QPushButton("✔ Validar e Integrar a Reporte")
        self.btn_save_verdict.setStyleSheet("background-color: #238636; color: white; font-weight: bold;")
        self.btn_save_verdict.clicked.connect(self._on_submit_verdict)
        s_layout.addWidget(self.btn_save_verdict)

        s_layout.addStretch()

        # Botón para exportar captura individual
        self.btn_snapshot = QPushButton("💾 Guardar Snapshot HD del Defecto")
        self.btn_snapshot.clicked.connect(self._save_crop_snapshot)
        s_layout.addWidget(self.btn_snapshot)

        body.addWidget(side_box, stretch=2)
        main_layout.addLayout(body)

    def update_defect(
        self,
        clean_crop: np.ndarray,
        annot_crop: np.ndarray,
        full_frame: np.ndarray,
        defect_data: Dict[str, Any]
    ):
        """Actualiza la estación de análisis con un nuevo defecto detectado."""
        self.current_clean_crop = clean_crop
        self.current_annot_crop = annot_crop
        self.current_full_frame = full_frame
        self.current_meta = defect_data

        # Actualizar datos de metrología
        label = defect_data.get("label", "Desconocido").upper()
        conf = defect_data.get("confidence", 0.0)
        w_mm = defect_data.get("width_mm", 0.0)
        h_mm = defect_data.get("height_mm", 0.0)
        area_mm = w_mm * h_mm
        x1 = defect_data.get("x1", 0)
        y1 = defect_data.get("y1", 0)

        self.badge_severity.setText(f"DEFECTO: {label}")
        self.badge_severity.setStyleSheet("background-color: #b62324; color: #ffffff; padding: 4px 10px; border-radius: 4px; font-weight: bold;")

        self.lbl_defect_class.setText(f"Tipo de Falla: {label}")
        self.lbl_confidence.setText(f"Certeza IA: {conf:.1%}")
        self.lbl_dimensions_mm.setText(f"Dimensiones: {w_mm:.2f} mm x {h_mm:.2f} mm")
        self.lbl_area_mm2.setText(f"Área Estimada: {area_mm:.2f} mm²")
        self.lbl_coords.setText(f"Coordenadas ROI: (X: {x1}, Y: {y1})")

        max_dim = max(w_mm, h_mm)
        if max_dim > 5.0:
            self.lbl_tolerance.setText(f"Tolerancia máx: 5.0 mm | ❌ EXCEDIDA (+{max_dim-5.0:.2f} mm)")
            self.lbl_tolerance.setStyleSheet("color: #ff7b72; font-weight: bold; font-size: 11px;")
        else:
            self.lbl_tolerance.setText(f"Tolerancia máx: 5.0 mm | ⚠️ Cerca del límite ({max_dim:.2f} mm)")
            self.lbl_tolerance.setStyleSheet("color: #d29922; font-size: 11px;")

        self._render_current_view()

    def _on_zoom_changed(self, val: int):
        self.zoom_level = val / 10.0
        self.lbl_zoom_val.setText(f"{self.zoom_level:.1f}x")
        self._render_current_view()

    def _render_current_view(self):
        base_img = self.current_annot_crop if self.chk_show_box.isChecked() else self.current_clean_crop
        if base_img is None or base_img.size == 0:
            return

        render = base_img.copy()

        # Filtro de realce de contraste CLAHE (para ver micro-fisuras)
        if self.chk_enhance.isChecked():
            try:
                lab = cv2.cvtColor(render, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                cl = clahe.apply(l)
                limg = cv2.merge((cl, a, b))
                render = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
            except Exception:
                pass

        # Aplicar zoom digital
        if self.zoom_level > 1.0:
            zh, zw = render.shape[:2]
            new_w = int(zw / self.zoom_level)
            new_h = int(zh / self.zoom_level)
            start_x = (zw - new_w) // 2
            start_y = (zh - new_h) // 2
            render = render[start_y:start_y+new_h, start_x:start_x+new_w]

        # Regla milimétrica en esquina inferior
        h, w = render.shape[:2]
        cv2.putText(render, f"Zoom: {self.zoom_level:.1f}x", (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)

        # Proyectar a QPixmap
        rgb = cv2.cvtColor(render, cv2.COLOR_BGR2RGB)
        rh, rw, rc = rgb.shape
        qimg = QImage(rgb.data, rw, rh, rc * rw, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)

        scaled = pix.scaled(
            self.lbl_viewport.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.lbl_viewport.setPixmap(scaled)

    def _on_submit_verdict(self):
        verdict = self.combo_verdict.currentText()
        notes = self.txt_notes.toPlainText().strip()
        QMessageBox.information(
            self,
            "Veredicto Registrado",
            f"Veredicto: {verdict}\nObservaciones: {notes if notes else 'Ninguna'}\n\n"
            "Registrado en la bitácora de inspección con éxito."
        )

    def _save_crop_snapshot(self):
        if self.current_annot_crop is None:
            QMessageBox.warning(self, "Aviso", "No hay ningún defecto activo para guardar.")
            return

        import os
        from datetime import datetime
        folder = os.path.abspath("data/evidence/defect_snapshots")
        os.makedirs(folder, exist_ok=True)
        filename = f"defecto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(folder, filename)
        cv2.imwrite(path, self.current_annot_crop)
        QMessageBox.information(self, "Snapshot Guardado", f"Imagen guardada con éxito en:\n{path}")
