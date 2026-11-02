import os
import sys
import subprocess

# Asegurar que la raíz del proyecto esté en sys.path si el archivo se ejecuta directamente
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import time
from typing import Optional, List
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox,
    QStatusBar, QMessageBox, QFrame, QSizePolicy, QSplitter, QComboBox, QScrollArea
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPixmap, QFont

from src.app.settings import AppSettings
from src.app.camera_worker import CameraWorker
from src.app.history_dialog import EvidenceHistoryDialog
from src.app.defect_viewer_window import DefectViewerWindow
from src.app.evidence_wall_window import EvidenceWallWindow
from src.camera.ip_webcam_source import IPWebcamSource
from src.camera.usb_camera_source import USBCameraSource
from src.camera.synthetic_source import SyntheticSheetSource
from src.camera.stream_diagnostics import diagnose_stream
from src.storage.database import DatabaseManager
from src.storage.evidence_repository import EvidenceRepository
from src.vision.yolo_adapter import YOLOAdapter
from src.vision.anomaly_adapter import AnomalyAdapter
from src.vision.detection_service import VisionDetector

class MainWindow(QMainWindow):
    """
    Ventana principal de grado de ingeniería para el Sistema de Visión Artificial.
    Estética oscura moderna con acentos azul/cian, vista central no deformada,
    controles desacoplados, persistencia en SQLite y diagnóstico transparente.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Visión Artificial — Inspección de Láminas Metálicas")
        self.resize(1180, 750)
        self.setMinimumSize(960, 580)

        # Cargar configuración persistente
        self.settings = AppSettings.load_from_file()

        # Componentes de persistencia
        self.db_manager = DatabaseManager(self.settings.storage.db_path)
        self.evidence_repo = EvidenceRepository(self.settings.storage.evidence_dir, self.db_manager)

        # Componentes de visión artificial
        self.yolo_detector = YOLOAdapter(
            weights_path=self.settings.vision.yolo_weights_path,
            conf_thresh=self.settings.vision.confidence_threshold
        )
        self.anomaly_detector = AnomalyAdapter(
            weights_path=self.settings.vision.patchcore_weights_path,
            threshold=self.settings.vision.anomaly_threshold
        )
        self.active_detector: Optional[VisionDetector] = None

        # Variables de estado
        self.camera_worker: Optional[CameraWorker] = None
        self.current_session_id: Optional[int] = None
        self.last_frame_orig: Optional[np.ndarray] = None
        self.last_frame_annot: Optional[np.ndarray] = None
        self.last_inference_result = None
        self.last_defect_patch: Optional[np.ndarray] = None
        self.total_defects_session: int = 0
        self.last_auto_capture_time: float = 0.0
        self.auto_capture_enabled: bool = True
        self.last_saved_signatures = []  # Firmas de deduplicación: (label, x_norm, y_norm, w_norm, h_norm, timestamp)
        self.gallery_items = []  # Lista de evidencias en memoria para la tira de miniaturas CCTV

        # Ventana independiente de análisis y metrología de defectos (Multi-monitor)
        self.defect_window = DefectViewerWindow(self)

        # Ventana independiente de Mosaico / Mural CCTV de Evidencias
        self.evidence_wall = EvidenceWallWindow(self)

        self._setup_style()
        self._setup_ui()
        self._update_detector_status_label()

    def _setup_style(self):
        # Paleta oscura profesional (Sleek Dark Theme)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121417;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QWidget {
                color: #d8d8d8;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #2a2e35;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 14px;
                font-weight: bold;
                color: #4da6ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
            }
            QPushButton {
                background-color: #1f242d;
                border: 1px solid #363d4a;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: 500;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background-color: #2a3240;
                border-color: #007acc;
            }
            QPushButton:pressed {
                background-color: #161b22;
            }
            QPushButton:disabled {
                background-color: #181a1f;
                border-color: #24272e;
                color: #555a64;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #1a1e24;
                border: 1px solid #363d4a;
                border-radius: 4px;
                padding: 4px 8px;
                color: #ffffff;
                selection-background-color: #007acc;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #00a8ff;
            }
            QComboBox {
                padding-right: 20px;
                min-height: 24px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 22px;
                border-left: 1px solid #363d4a;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: #1f242d;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #4da6ff;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                background-color: #16191f;
                color: #ffffff;
                border: 1px solid #007acc;
                border-radius: 4px;
                padding: 4px;
                selection-background-color: #007acc;
                selection-color: #ffffff;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 28px;
                padding: 4px 8px;
                color: #ffffff;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #212836;
                color: #58a6ff;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #007acc;
                color: #ffffff;
            }
            QScrollBar:vertical {
                border: none;
                background: #121417;
                width: 8px;
                margin: 0;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #2a313d;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #007acc;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #121417;
                height: 8px;
                margin: 0;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #2a313d;
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #007acc;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                height: 0px;
            }
            QStatusBar {
                background-color: #0d0f12;
                border-top: 1px solid #1f242d;
                color: #9aa0a6;
            }
            QMessageBox, QDialog {
                background-color: #1a1e24;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #f0f0f0;
                font-size: 13px;
                background-color: transparent;
            }
            QMessageBox QPushButton {
                min-width: 80px;
                background-color: #007acc;
                border: 1px solid #2a82c4;
                border-radius: 4px;
                padding: 6px 14px;
                color: #ffffff;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #0094f7;
            }
            QSplitter::handle {
                background-color: #242933;
                width: 4px;
            }
            QSplitter::handle:hover {
                background-color: #00a8ff;
            }
        """)

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 12, 14, 8)
        main_layout.setSpacing(10)

        # A. ENCABEZADO TÉCNICO
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #171a1f; border-radius: 6px; padding: 6px;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 6, 12, 6)

        title_box = QVBoxLayout()
        lbl_title = QLabel("SISTEMA DE VISIÓN ARTIFICIAL — INSPECCIÓN DE LÁMINAS")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00a8ff; letter-spacing: 0.5px;")
        lbl_subtitle = QLabel("Laboratorio de pruebas y validación experimental (Fase Prototipo IP Webcam)")
        lbl_subtitle.setStyleSheet("font-size: 11px; color: #8e95a0;")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_subtitle)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Badges de estado en el encabezado
        self.badge_mode = QLabel("MODO: PRUEBA CON IP WEBCAM")
        self.badge_mode.setStyleSheet("background-color: #252b36; color: #ffb74d; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        self.badge_cam = QLabel("CÁMARA: DESCONECTADA")
        self.badge_cam.setStyleSheet("background-color: #381c1c; color: #ff6b6b; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        self.badge_detector = QLabel("DETECTOR: NO DISPONIBLE")
        self.badge_detector.setStyleSheet("background-color: #2b2b24; color: #d4af37; padding: 4px 10px; border-radius: 4px; font-weight: bold;")

        header_layout.addWidget(self.badge_mode)
        header_layout.addWidget(self.badge_cam)
        header_layout.addWidget(self.badge_detector)

        main_layout.addWidget(header_frame)

        # CUERPO PRINCIPAL (VISTA DE CÁMARA + PANEL LATERAL)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(14)

        # B. VISTA DUAL INDUSTRIAL (TRANSMISIÓN EN VIVO + ENCAPSULADO DE DEFECTO)
        splitter_screens = QSplitter(Qt.Horizontal)

        # 1. MONITOR 1: TRANSMISIÓN EN VIVO
        view_container = QGroupBox("CANAL 1: TRANSMISIÓN EN VIVO (SUPERVISIÓN)")
        view_layout = QVBoxLayout(view_container)
        view_layout.setContentsMargins(6, 6, 6, 6)

        self.lbl_camera_view = QLabel()
        self.lbl_camera_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_camera_view.setAlignment(Qt.AlignCenter)
        self.lbl_camera_view.setStyleSheet("background-color: #0b0c0e; border: 1px solid #1e2229; border-radius: 4px;")
        self.lbl_camera_view.setMinimumSize(320, 240)
        self._set_camera_placeholder("Cámara desconectada.\nConfigure la dirección de IP Webcam e inicie la transmisión.")
        view_layout.addWidget(self.lbl_camera_view)

        # Indicadores de telemetría bajo la pantalla en vivo
        telemetry_layout = QHBoxLayout()
        self.lbl_tel_fps = QLabel("FPS Captura: 0.0 | FPS Proceso: 0.0")
        self.lbl_tel_res = QLabel("Resolución: 0 x 0")
        self.lbl_tel_latency = QLabel("Latencia: 0.0 ms")
        for lbl in [self.lbl_tel_fps, self.lbl_tel_res, self.lbl_tel_latency]:
            lbl.setStyleSheet("color: #798394; font-size: 11px;")
            telemetry_layout.addWidget(lbl)
        telemetry_layout.addStretch()
        view_layout.addLayout(telemetry_layout)
        splitter_screens.addWidget(view_container)

        # 2. MONITOR 2: ENCAPSULADO DE DEFECTO Y METROLOGÍA
        defect_container = QGroupBox("CANAL 2: AISLAMIENTO Y ENCAPSULADO DE NO CONFORMIDAD")
        defect_layout = QVBoxLayout(defect_container)
        defect_layout.setContentsMargins(6, 6, 6, 6)

        self.lbl_defect_view = QLabel()
        self.lbl_defect_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_defect_view.setAlignment(Qt.AlignCenter)
        self.lbl_defect_view.setStyleSheet("background-color: #0b0c0e; border: 1px solid #361b1b; border-radius: 4px;")
        self.lbl_defect_view.setMinimumSize(260, 240)
        self.lbl_defect_view.setText("<div align='center' style='color:#555a64;'><b>Sin defectos detectados.<br>El sistema aislará automáticamente cada anomalía aquí.</b></div>")
        defect_layout.addWidget(self.lbl_defect_view)

        # Barra de información del defecto aislado y botón para ventana flotante
        bottom_bar = QHBoxLayout()
        self.lbl_defect_info = QLabel("Estado: Ningún defecto activo | Tamaño estimado: -- mm")
        self.lbl_defect_info.setStyleSheet("color: #ff9999; font-size: 11px; font-weight: bold; padding: 2px;")
        bottom_bar.addWidget(self.lbl_defect_info, stretch=3)

        self.btn_open_defect_window = QPushButton("↗ Terminal Independiente")
        self.btn_open_defect_window.setStyleSheet("background-color: #21262d; border-color: #388bfd; color: #58a6ff; font-weight: bold; padding: 4px 10px;")
        self.btn_open_defect_window.clicked.connect(self._open_defect_window)
        bottom_bar.addWidget(self.btn_open_defect_window, stretch=1)

        defect_layout.addLayout(bottom_bar)

        splitter_screens.addWidget(defect_container)
        splitter_screens.setSizes([600, 450])
        body_layout.addWidget(splitter_screens, stretch=4)

        # C. PANEL LATERAL DE CONFIGURACIÓN Y ACCIONES CON SCROLL RESPONSIVO
        # Permite que en pantallas de 1366x768 o portátiles pequeños todo sea accesible y legible
        side_scroll = QScrollArea()
        side_scroll.setWidgetResizable(True)
        side_scroll.setFrameShape(QFrame.NoFrame)
        side_scroll.setStyleSheet("background: transparent;")
        side_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        side_scroll.setMinimumWidth(320)
        side_scroll.setMaximumWidth(420)

        side_widget = QWidget()
        side_widget.setStyleSheet("background: transparent;")
        side_panel = QVBoxLayout(side_widget)
        side_panel.setContentsMargins(4, 2, 8, 4)
        side_panel.setSpacing(10)

        # 1. Configuración de Conexión de Cámara (IP Webcam / USB)
        group_cam_cfg = QGroupBox("CONFIGURACIÓN DE CÁMARA")
        cam_cfg_layout = QVBoxLayout(group_cam_cfg)

        # Selector de Fuente: IP Webcam vs Cámara USB / Integrada
        source_type_row = QHBoxLayout()
        source_type_row.addWidget(QLabel("Dispositivo:"))
        self.combo_cam_type = QComboBox()
        self.combo_cam_type.addItem("📱 IP Webcam (Celular Android)", "ip_webcam")
        self.combo_cam_type.addItem("📷 Cámara USB / Dispositivo", "usb_camera")
        # Establecer según configuración
        current_source_idx = 1 if getattr(self.settings.camera, "source_mode", "ip_webcam") == "usb_camera" else 0
        self.combo_cam_type.setCurrentIndex(current_source_idx)
        self.combo_cam_type.currentIndexChanged.connect(self._on_cam_type_changed)
        source_type_row.addWidget(self.combo_cam_type)
        cam_cfg_layout.addLayout(source_type_row)

        # Contenedor para parámetros de IP Webcam
        self.ip_cam_container = QWidget()
        ip_box_layout = QVBoxLayout(self.ip_cam_container)
        ip_box_layout.setContentsMargins(0, 0, 0, 0)

        ip_row = QHBoxLayout()
        ip_row.addWidget(QLabel("IP / Host:"))
        self.txt_ip = QLineEdit(self.settings.camera.ip_or_host)
        ip_row.addWidget(self.txt_ip)
        ip_box_layout.addLayout(ip_row)

        port_row = QHBoxLayout()
        port_row.addWidget(QLabel("Puerto:"))
        self.spin_port = QSpinBox()
        self.spin_port.setRange(1, 65535)
        self.spin_port.setValue(self.settings.camera.port)
        port_row.addWidget(self.spin_port)
        ip_box_layout.addLayout(port_row)

        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("Ruta stream:"))
        self.txt_path = QLineEdit(self.settings.camera.stream_path)
        path_row.addWidget(self.txt_path)
        ip_box_layout.addLayout(path_row)

        self.chk_custom_url = QCheckBox("Usar URL manual completa")
        self.chk_custom_url.setChecked(self.settings.camera.use_custom_url)
        self.chk_custom_url.toggled.connect(self._toggle_custom_url)
        ip_box_layout.addWidget(self.chk_custom_url)

        self.txt_custom_url = QLineEdit(self.settings.camera.custom_url)
        self.txt_custom_url.setPlaceholderText("http://192.168.1.100:8080/video")
        self.txt_custom_url.setEnabled(self.settings.camera.use_custom_url)
        ip_box_layout.addWidget(self.txt_custom_url)
        cam_cfg_layout.addWidget(self.ip_cam_container)

        # Contenedor para parámetros de Cámara USB / Dispositivo
        self.usb_cam_container = QWidget()
        usb_box_layout = QVBoxLayout(self.usb_cam_container)
        usb_box_layout.setContentsMargins(0, 0, 0, 0)

        usb_row = QHBoxLayout()
        usb_row.addWidget(QLabel("Índice de Cámara:"))
        self.spin_usb_index = QSpinBox()
        self.spin_usb_index.setRange(0, 9)
        self.spin_usb_index.setValue(getattr(self.settings.camera, "usb_camera_index", 0))
        self.spin_usb_index.setToolTip("0 suele ser la cámara integrada o primera USB, 1 o 2 la segunda cámara USB.")
        usb_row.addWidget(self.spin_usb_index)
        usb_box_layout.addLayout(usb_row)

        self.btn_detect_usb = QPushButton("🔍 Auto-detectar Cámaras USB")
        self.btn_detect_usb.clicked.connect(self._auto_detect_usb_cameras)
        usb_box_layout.addWidget(self.btn_detect_usb)

        cam_cfg_layout.addWidget(self.usb_cam_container)

        # Mostrar/Ocultar contenedores según el tipo inicial
        self._on_cam_type_changed(self.combo_cam_type.currentIndex())

        # Botones de prueba y conexión
        btn_cam_row = QHBoxLayout()
        self.btn_test_conn = QPushButton("Probar Conexión")
        self.btn_test_conn.clicked.connect(self._on_test_connection_clicked)
        self.btn_save_cfg = QPushButton("Guardar Ajustes")
        self.btn_save_cfg.clicked.connect(self._save_settings)
        btn_cam_row.addWidget(self.btn_test_conn)
        btn_cam_row.addWidget(self.btn_save_cfg)
        cam_cfg_layout.addLayout(btn_cam_row)

        self.chk_synthetic = QCheckBox("Modo Sintético (Prueba sin cámara)")
        self.chk_synthetic.toggled.connect(self._on_toggle_synthetic)
        cam_cfg_layout.addWidget(self.chk_synthetic)

        side_panel.addWidget(group_cam_cfg)

        # 2. Controles de Inspección Operativa
        group_controls = QGroupBox("CONTROL DE OPERACIÓN")
        ctrl_layout = QVBoxLayout(group_controls)

        self.btn_start = QPushButton("▶ Iniciar Transmisión")
        self.btn_start.setStyleSheet("background-color: #0b6623; color: white; font-weight: bold; padding: 8px;")
        self.btn_start.clicked.connect(self._start_capture)
        ctrl_layout.addWidget(self.btn_start)

        pause_stop_row = QHBoxLayout()
        self.btn_pause = QPushButton("⏸ Pausar")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self._toggle_pause)
        self.btn_stop = QPushButton("⏹ Detener")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("background-color: #7a1f1d; color: white;")
        self.btn_stop.clicked.connect(self._stop_capture)
        pause_stop_row.addWidget(self.btn_pause)
        pause_stop_row.addWidget(self.btn_stop)
        ctrl_layout.addLayout(pause_stop_row)

        self.btn_capture = QPushButton("📸 Capturar Evidencia Manual")
        self.btn_capture.setStyleSheet("background-color: #007acc; color: white; font-weight: bold; padding: 8px;")
        self.btn_capture.setEnabled(False)
        self.btn_capture.clicked.connect(self._capture_evidence)
        ctrl_layout.addWidget(self.btn_capture)

        self.chk_auto_capture = QCheckBox("Auto-guardar si hay No Conformidad")
        self.chk_auto_capture.setChecked(True)
        self.chk_auto_capture.setStyleSheet("color: #4da6ff; font-weight: bold;")
        ctrl_layout.addWidget(self.chk_auto_capture)

        self.lbl_session_defects = QLabel("Defectos detectados en sesión: 0")
        self.lbl_session_defects.setStyleSheet("color: #ffcc00; font-size: 11px; font-weight: bold;")
        ctrl_layout.addWidget(self.lbl_session_defects)

        side_panel.addWidget(group_controls)

        # Grupo de Calibración Metrológica con Botón 'Por defecto'
        group_calib = QGroupBox("CALIBRACIÓN METROLÓGICA (PÍXEL A MM)")
        calib_layout = QVBoxLayout(group_calib)
        calib_row = QHBoxLayout()
        calib_row.addWidget(QLabel("Escala (mm/px):"))
        self.spin_mm_px = QDoubleSpinBox()
        self.spin_mm_px.setRange(0.01, 10.00)
        self.spin_mm_px.setSingleStep(0.05)
        self.spin_mm_px.setDecimals(3)
        self.spin_mm_px.setValue(getattr(self.settings.vision, "mm_per_pixel", 0.25))
        calib_row.addWidget(self.spin_mm_px)

        self.btn_calib_default = QPushButton("Por defecto")
        self.btn_calib_default.setToolTip("Restablece la escala nominal de metrología por defecto (0.250 mm/px)")
        self.btn_calib_default.setStyleSheet("background-color: #21262d; border-color: #007acc; color: #4da6ff; font-size: 11px; padding: 3px 8px;")
        self.btn_calib_default.clicked.connect(self._reset_calib_default)
        calib_row.addWidget(self.btn_calib_default)

        calib_layout.addLayout(calib_row)
        side_panel.addWidget(group_calib)

        # 3. Gestión y Evidencias
        group_mgmt = QGroupBox("EVIDENCIAS Y CALIDAD (ISO 9001)")
        mgmt_layout = QVBoxLayout(group_mgmt)

        self.btn_image_inspector = QPushButton("🔬 Ficha Forense / Inspeccionar Foto...")
        self.btn_image_inspector.setStyleSheet("background-color: #8957e5; border-color: #a371f7; color: white; font-weight: bold; padding: 7px;")
        self.btn_image_inspector.clicked.connect(self._open_image_inspector)
        mgmt_layout.addWidget(self.btn_image_inspector)

        self.btn_history = QPushButton("📋 Ver Historial y Revisiones")
        self.btn_history.clicked.connect(self._open_history_dialog)
        mgmt_layout.addWidget(self.btn_history)

        self.btn_export_report = QPushButton("📊 Exportar Reporte de Calidad (CSV)")
        self.btn_export_report.setStyleSheet("background-color: #1b3d2f; border-color: #2b6e50; font-weight: bold;")
        self.btn_export_report.clicked.connect(self._export_quality_report)
        mgmt_layout.addWidget(self.btn_export_report)

        self.btn_open_wall = QPushButton("🖼 Mural CCTV de Evidencias")
        self.btn_open_wall.setStyleSheet("background-color: #1a2a3a; border-color: #007acc; color: #4da6ff; font-weight: bold;")
        self.btn_open_wall.clicked.connect(self._open_evidence_wall)
        mgmt_layout.addWidget(self.btn_open_wall)

        self.btn_open_folder = QPushButton("📁 Abrir Carpeta de Evidencias")
        self.btn_open_folder.clicked.connect(self._open_evidence_folder)
        mgmt_layout.addWidget(self.btn_open_folder)

        side_panel.addWidget(group_mgmt)

        side_panel.addStretch()
        side_scroll.setWidget(side_widget)
        body_layout.addWidget(side_scroll, stretch=1)
        main_layout.addLayout(body_layout)

        # D. BARRA DE ESTADO INFERIOR
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo. Sistema en modo de pruebas.")

    def _set_camera_placeholder(self, text: str):
        self.lbl_camera_view.setText(f"<div align='center' style='color:#6d7582;'><b>{text}</b></div>")

    def _toggle_custom_url(self, checked: bool):
        self.txt_custom_url.setEnabled(checked)

    def _on_cam_type_changed(self, index: int):
        is_usb = (index == 1)
        if hasattr(self, "ip_cam_container") and hasattr(self, "usb_cam_container"):
            self.ip_cam_container.setVisible(not is_usb)
            self.usb_cam_container.setVisible(is_usb)
            if hasattr(self, "chk_synthetic") and not self.chk_synthetic.isChecked():
                if is_usb:
                    self.badge_mode.setText("MODO: CÁMARA USB / DISPOSITIVO")
                    self.badge_mode.setStyleSheet("background-color: #1a2736; color: #4da6ff; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
                else:
                    self.badge_mode.setText("MODO: PRUEBA CON IP WEBCAM")
                    self.badge_mode.setStyleSheet("background-color: #252b36; color: #ffb74d; padding: 4px 10px; border-radius: 4px; font-weight: bold;")

    def _reset_calib_default(self):
        """Restablece la escala nominal de metrología por defecto (0.250 mm/px)."""
        self.spin_mm_px.setValue(0.250)
        self.settings.vision.mm_per_pixel = 0.250
        self.status_bar.showMessage("Escala calibrada restablecida al valor nominal por defecto: 0.250 mm/px")

    def _auto_detect_usb_cameras(self):
        """Escanea los índices de dispositivos de video disponibles en el sistema."""
        self.status_bar.showMessage("Escaneando cámaras USB y del dispositivo...")
        available = []
        for idx in range(5):
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available.append(idx)
                cap.release()

        if available:
            self.spin_usb_index.setValue(available[0])
            cams_str = ", ".join(f"Cámara #{i}" for i in available)
            QMessageBox.information(
                self,
                "Cámaras Detectadas",
                f"✅ Se encontraron los siguientes dispositivos activos:\n\n{cams_str}\n\n"
                f"Se ha seleccionado automáticamente la Cámara #{available[0]}."
            )
            self.status_bar.showMessage(f"Cámaras USB detectadas: {cams_str}")
        else:
            QMessageBox.warning(
                self,
                "Sin Cámaras USB",
                "No se detectó ninguna cámara USB o integrada disponible.\nVerifique la conexión USB o los permisos de cámara en Windows."
            )
            self.status_bar.showMessage("No se detectaron cámaras USB.")

    def _on_toggle_synthetic(self, checked: bool):
        if checked:
            self.badge_mode.setText("MODO: SIMULACIÓN SINTÉTICA")
            self.badge_mode.setStyleSheet("background-color: #2b2b18; color: #ffdd57; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        else:
            is_usb = (self.combo_cam_type.currentIndex() == 1)
            if is_usb:
                self.badge_mode.setText("MODO: CÁMARA USB / DISPOSITIVO")
                self.badge_mode.setStyleSheet("background-color: #1a2736; color: #4da6ff; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
            else:
                self.badge_mode.setText("MODO: PRUEBA CON IP WEBCAM")
                self.badge_mode.setStyleSheet("background-color: #252b36; color: #ffb74d; padding: 4px 10px; border-radius: 4px; font-weight: bold;")

    def _update_detector_status_label(self):
        if self.yolo_detector.is_ready():
            self.badge_detector.setText("DETECTOR: YOLO + SUPERFICIE (ACTIVO)")
            self.badge_detector.setStyleSheet("background-color: #1a382b; color: #5cdb95; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
            self.active_detector = self.yolo_detector
        else:
            self.badge_detector.setText("DETECTOR: NO DISPONIBLE")
            self.badge_detector.setStyleSheet("background-color: #2b2b24; color: #d4af37; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
            self.active_detector = None

    def _sync_settings_from_ui(self):
        self.settings.camera.source_mode = "usb_camera" if self.combo_cam_type.currentIndex() == 1 else "ip_webcam"
        self.settings.camera.usb_camera_index = self.spin_usb_index.value()
        self.settings.camera.ip_or_host = self.txt_ip.text().strip()
        self.settings.camera.port = self.spin_port.value()
        self.settings.camera.stream_path = self.txt_path.text().strip()
        self.settings.camera.use_custom_url = self.chk_custom_url.isChecked()
        self.settings.camera.custom_url = self.txt_custom_url.text().strip()
        self.settings.vision.mm_per_pixel = self.spin_mm_px.value()

    def _save_settings(self):
        self._sync_settings_from_ui()
        self.settings.save_to_file()
        QMessageBox.information(self, "Configuración", "Ajustes guardados correctamente en config/settings.json.")

    def _on_test_connection_clicked(self):
        self._sync_settings_from_ui()

        if self.combo_cam_type.currentIndex() == 1:
            # Prueba de cámara USB
            usb_idx = self.spin_usb_index.value()
            self.status_bar.showMessage(f"Probando cámara USB #{usb_idx}...")
            test_src = USBCameraSource(camera_index=usb_idx)
            if test_src.open():
                w, h = test_src.get_resolution()
                test_src.release()
                QMessageBox.information(
                    self,
                    "Diagnóstico USB Exitoso",
                    f"✅ Cámara USB #{usb_idx} conectada con éxito.\n\n"
                    f"Resolución de captura: {w}x{h}\n"
                    f"Dispositivo listo para inspección en tiempo real."
                )
                self.status_bar.showMessage(f"Cámara USB #{usb_idx} verificada ({w}x{h}).")
            else:
                QMessageBox.warning(
                    self,
                    "Error de Cámara USB",
                    f"❌ No se pudo inicializar la Cámara USB #{usb_idx}.\n\n"
                    f"Recomendación: Use el botón 'Auto-detectar Cámaras USB' o verifique el puerto USB."
                )
                self.status_bar.showMessage(f"Fallo al conectar cámara USB #{usb_idx}.")
            return

        target_url = self.settings.camera.get_stream_url()
        self.status_bar.showMessage(f"Probando conexión con {target_url}...")
        diag = diagnose_stream(target_url, timeout=3.0)

        if diag.success:
            QMessageBox.information(
                self,
                "Diagnóstico Exitoso",
                f"✅ {diag.status_message}\n\n"
                f"Resolución detectada: {diag.width}x{diag.height}\n"
                f"Tiempo de respuesta: {diag.latency_ms:.1f} ms\n\n"
                f"Recomendación: {diag.recommendation}"
            )
        else:
            QMessageBox.warning(
                self,
                "Diagnóstico de Conexión",
                f"❌ Error: {diag.status_message}\n\n"
                f"Código: {diag.error_code}\n"
                f"Recomendación:\n{diag.recommendation}"
            )
        self.status_bar.showMessage("Diagnóstico finalizado.")

    def _start_capture(self):
        self._sync_settings_from_ui()

        # Determinar fuente de video
        if self.chk_synthetic.isChecked():
            source = SyntheticSheetSource()
            source_desc = "Generador Sintético"
            source_type = "Sintetico"
            source_url = ""
        elif self.combo_cam_type.currentIndex() == 1:
            usb_idx = self.settings.camera.usb_camera_index
            source = USBCameraSource(camera_index=usb_idx)
            source_desc = f"Cámara USB #{usb_idx}"
            source_type = "USB_Camera"
            source_url = f"usb://{usb_idx}"
        else:
            url = self.settings.camera.get_stream_url()
            source = IPWebcamSource(url)
            source_desc = f"IP Webcam ({url})"
            source_type = "IP_Webcam"
            source_url = url

        # Crear sesión en SQLite
        self.current_session_id = self.db_manager.create_session(
            session_name=f"Sesion_{source_desc}",
            source_type=source_type,
            source_url=source_url
        )

        # Iniciar Worker en segundo plano con calibración milimétrica
        self.camera_worker = CameraWorker(
            source,
            detector=self.active_detector,
            mm_per_pixel=self.settings.vision.mm_per_pixel
        )
        self.camera_worker.frame_ready.connect(self._on_frame_ready)
        self.camera_worker.metrics_updated.connect(self._on_metrics_updated)
        self.camera_worker.connection_status_changed.connect(self._on_connection_status_changed)
        self.camera_worker.error_occurred.connect(self._on_worker_error)

        self.camera_worker.start()

        # Actualizar UI
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_capture.setEnabled(True)

    @Slot(np.ndarray, np.ndarray, object)
    def _on_frame_ready(self, frame_orig: np.ndarray, frame_annot: np.ndarray, inference_res):
        self.last_frame_orig = frame_orig
        self.last_frame_annot = frame_annot
        self.last_inference_result = inference_res

        # Actualizar alerta de No Conformidad en la interfaz y encapsular el defecto
        if inference_res is not None and inference_res.has_detections and inference_res.regions:
            num_defects = len(inference_res.regions)
            self.total_defects_session += 1
            self.lbl_session_defects.setText(f"Defectos detectados en sesión: {self.total_defects_session}")
            self.badge_detector.setText(f"ESTADO: NO CONFORME ({num_defects} DEFECTOS)")
            self.badge_detector.setStyleSheet("background-color: #5c1818; color: #ff5252; padding: 4px 10px; border-radius: 4px; font-weight: bold; border: 1px solid #ff1744;")

            # Aislar / Encapsular el primer defecto en el monitor 2 con margen (Zoom ROI)
            primary_reg = inference_res.regions[0]
            fh, fw = frame_orig.shape[:2]
            margin = 35
            rx1 = max(0, primary_reg.x1 - margin)
            ry1 = max(0, primary_reg.y1 - margin)
            rx2 = min(fw, primary_reg.x2 + margin)
            ry2 = min(fh, primary_reg.y2 + margin)

            clean_crop = frame_orig[ry1:ry2, rx1:rx2].copy() if frame_orig is not None else None
            defect_crop = (frame_annot if frame_annot is not None else frame_orig)[ry1:ry2, rx1:rx2].copy()
            if defect_crop.size > 0:
                self.last_defect_patch = defect_crop
                defect_rgb = cv2.cvtColor(defect_crop, cv2.COLOR_BGR2RGB)
                dh, dw, dch = defect_rgb.shape
                d_qimg = QImage(defect_rgb.data, dw, dh, dch * dw, QImage.Format_RGB888)
                d_pixmap = QPixmap.fromImage(d_qimg)
                scaled_d_pix = d_pixmap.scaled(
                    self.lbl_defect_view.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.lbl_defect_view.setPixmap(scaled_d_pix)

                def_w = primary_reg.x2 - primary_reg.x1
                def_h = primary_reg.y2 - primary_reg.y1
                mm_factor = self.spin_mm_px.value()
                w_mm = def_w * mm_factor
                h_mm = def_h * mm_factor
                area_mm2 = w_mm * h_mm

                self.lbl_defect_info.setText(
                    f"⚠️ DEFECTO [{primary_reg.label.upper()}] | "
                    f"Certeza: {primary_reg.confidence_or_score:.1%} | "
                    f"Dim: {w_mm:.1f}x{h_mm:.1f} mm | Coord: ({primary_reg.x1}, {primary_reg.y1})"
                )

                # Sincronizar en tiempo real con la ventana independiente / segundo monitor
                if hasattr(self, "defect_window") and self.defect_window is not None:
                    self.defect_window.update_defect(
                        clean_crop=clean_crop,
                        annot_crop=defect_crop,
                        full_frame=frame_orig,
                        defect_data={
                            "label": primary_reg.label,
                            "confidence": primary_reg.confidence_or_score,
                            "width_mm": w_mm,
                            "height_mm": h_mm,
                            "x1": primary_reg.x1,
                            "y1": primary_reg.y1,
                            "width_px": def_w,
                            "height_px": def_h
                        }
                    )

            # Auto-captura industrial de evidencia con FILTRO ANTI-DUPLICADOS INTELIGENTE
            # Si el defecto es el mismo punto/hueco en la misma posición y tamaño dentro de una ventana temporal,
            # se ignora para no inundar el almacenamiento con fotos repetidas del mismo defecto.
            now = time.time()
            if getattr(self, "chk_auto_capture", None) and self.chk_auto_capture.isChecked():
                fh, fw = frame_orig.shape[:2]
                current_sig = (
                    primary_reg.label,
                    round(primary_reg.x1 / max(1, fw), 2),
                    round(primary_reg.y1 / max(1, fh), 2),
                    round((primary_reg.x2 - primary_reg.x1) / max(1, fw), 2),
                    round((primary_reg.y2 - primary_reg.y1) / max(1, fh), 2)
                )

                # Limpiar firmas con más de 12 segundos de antigüedad
                self.last_saved_signatures = [s for s in self.last_saved_signatures if now - s[5] < 12.0]

                # Comprobar si coincide con un defecto idéntico reciente (mismo punto y tamaño)
                is_duplicate = False
                for s in self.last_saved_signatures:
                    same_label = (s[0] == current_sig[0])
                    pos_dist = abs(s[1] - current_sig[1]) + abs(s[2] - current_sig[2])
                    size_diff = abs(s[3] - current_sig[3]) + abs(s[4] - current_sig[4])
                    if same_label and pos_dist < 0.04 and size_diff < 0.03:
                        is_duplicate = True
                        break

                if not is_duplicate and (now - self.last_auto_capture_time > 1.5):
                    self.last_auto_capture_time = now
                    self.last_saved_signatures.append((*current_sig, now))
                    try:
                        if self.chk_synthetic.isChecked():
                            s_info = "Sintetico"
                        elif self.combo_cam_type.currentIndex() == 1:
                            s_info = f"Camara_USB_#{self.settings.camera.usb_camera_index}"
                        else:
                            s_info = "IP_Webcam"

                        save_res = self.evidence_repo.save_capture(
                            frame_original=frame_orig,
                            session_id=self.current_session_id,
                            source_info=s_info,
                            frame_annotated=frame_annot,
                            model_name="YOLOv8 + Superficie (Auto)",
                            detections=[{
                                "label": r.label,
                                "confidence": r.confidence_or_score,
                                "x1": r.x1, "y1": r.y1, "x2": r.x2, "y2": r.y2,
                                "is_anomaly": r.is_anomaly_score
                            } for r in inference_res.regions]
                        )
                        self._add_to_gallery(frame_annot if frame_annot is not None else frame_orig, save_res)
                        self.status_bar.showMessage(f"⚠️ Nueva evidencia #{save_res['evidence_id']} registrada en galería CCTV")
                    except Exception as e:
                        pass
        else:
            if self.active_detector and self.active_detector.is_ready():
                self.badge_detector.setText("ESTADO: CONFORME (OK)")
                self.badge_detector.setStyleSheet("background-color: #1a382b; color: #5cdb95; padding: 4px 10px; border-radius: 4px; font-weight: bold;")

        # Convertir a QPixmap para visualización en Canal 1
        display_frame = frame_annot if frame_annot is not None else frame_orig
        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        # Escalar respetando el aspecto de la imagen
        scaled_pixmap = pixmap.scaled(
            self.lbl_camera_view.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.lbl_camera_view.setPixmap(scaled_pixmap)

    @Slot(float, float, float, int, int)
    def _on_metrics_updated(self, cap_fps: float, proc_fps: float, latency: float, w: int, h: int):
        self.lbl_tel_fps.setText(f"FPS Captura: {cap_fps:.1f} | FPS Proceso: {proc_fps:.1f}")
        self.lbl_tel_res.setText(f"Resolución Real: {w} x {h}")
        self.lbl_tel_latency.setText(f"Latencia: {latency:.1f} ms")

    @Slot(bool, str)
    def _on_connection_status_changed(self, connected: bool, message: str):
        if connected:
            self.badge_cam.setText("CÁMARA: CONECTADA")
            self.badge_cam.setStyleSheet("background-color: #1a382b; color: #5cdb95; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        else:
            self.badge_cam.setText("CÁMARA: DESCONECTADA")
            self.badge_cam.setStyleSheet("background-color: #381c1c; color: #ff6b6b; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
            self._set_camera_placeholder(message)
        self.status_bar.showMessage(message)

    @Slot(str, str)
    def _on_worker_error(self, code: str, desc: str):
        self.status_bar.showMessage(f"Aviso [{code}]: {desc}")
        self._stop_capture()

    def _toggle_pause(self):
        if not self.camera_worker:
            return
        if self.btn_pause.text().startswith("⏸"):
            self.camera_worker.pause()
            self.btn_pause.setText("▶ Reanudar")
            self.status_bar.showMessage("Captura pausada.")
        else:
            self.camera_worker.resume()
            self.btn_pause.setText("⏸ Pausar")
            self.status_bar.showMessage("Captura reanudada.")

    def _stop_capture(self):
        if self.camera_worker:
            self.camera_worker.stop()
            self.camera_worker = None

        if self.current_session_id:
            self.db_manager.close_session(self.current_session_id)
            self.current_session_id = None

        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("⏸ Pausar")
        self.btn_stop.setEnabled(False)
        self.btn_capture.setEnabled(False)
        self.badge_cam.setText("CÁMARA: DESCONECTADA")
        self.badge_cam.setStyleSheet("background-color: #381c1c; color: #ff6b6b; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        self._set_camera_placeholder("Transmisión finalizada.")
        self.status_bar.showMessage("Captura detenida y recursos liberados.")

    def _capture_evidence(self):
        if self.last_frame_orig is None:
            QMessageBox.warning(self, "Captura", "No hay ningún fotograma disponible para capturar.")
            return

        try:
            detections_to_save = []
            if self.last_inference_result and self.last_inference_result.regions:
                for reg in self.last_inference_result.regions:
                    detections_to_save.append({
                        "label": reg.label,
                        "confidence": reg.confidence_or_score,
                        "x1": reg.x1,
                        "y1": reg.y1,
                        "x2": reg.x2,
                        "y2": reg.y2,
                        "is_anomaly": reg.is_anomaly_score
                    })

            if self.chk_synthetic.isChecked():
                manual_source = "Sintetico"
            elif self.combo_cam_type.currentIndex() == 1:
                manual_source = f"Camara_USB_#{self.settings.camera.usb_camera_index}"
            else:
                manual_source = "IP_Webcam"

            res = self.evidence_repo.save_capture(
                frame_original=self.last_frame_orig,
                session_id=self.current_session_id,
                source_info=manual_source,
                frame_annotated=self.last_frame_annot,
                model_name="YOLOv8 + Superficie" if (self.active_detector and self.active_detector.is_ready()) else "NINGUNO",
                detections=detections_to_save
            )
            self._add_to_gallery(self.last_frame_annot if self.last_frame_annot is not None else self.last_frame_orig, res)
            self.status_bar.showMessage(f"Evidencia guardada exitosamente: #{res['evidence_id']} ({res['original_path']})")
            QMessageBox.information(
                self,
                "Evidencia Guardada",
                f"Fotograma capturado y registrado con éxito.\n\n"
                f"Identificador: #{res['evidence_id']}\n"
                f"Resolución: {res['width']}x{res['height']}\n"
                f"Ruta: {res['original_path']}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", f"No se pudo guardar la evidencia: {e}")

    def _open_evidence_wall(self):
        """Abre la ventana independiente de Monitoreo CCTV / Mural de Evidencias."""
        if hasattr(self, "evidence_wall") and self.evidence_wall is not None:
            self.evidence_wall.show()
            self.evidence_wall.raise_()
            self.evidence_wall.activateWindow()

    def _add_to_gallery(self, frame: np.ndarray, evidence_res: dict):
        """Envía la captura a la ventana independiente del Mural CCTV de Evidencias."""
        if frame is None or frame.size == 0:
            return

        meta = {
            "evidence_id": evidence_res.get("evidence_id", 0),
            "source_info": evidence_res.get("source_info", "En Vivo"),
            "original_path": evidence_res.get("original_path", ""),
            "annotated_path": evidence_res.get("annotated_path", ""),
            "detections": evidence_res.get("detections", []),
            "frame_orig": self.last_frame_orig if self.last_frame_orig is not None else frame,
            "time_str": time.strftime("%H:%M:%S")
        }

        # Actualizar mural independiente en tiempo real
        if hasattr(self, "evidence_wall") and self.evidence_wall is not None:
            self.evidence_wall.add_evidence(frame, meta)

    def _export_quality_report(self):
        """Exporta un informe consolidado de calidad de la sesión o histórico en formato CSV."""
        import csv
        from datetime import datetime

        try:
            evidences = self.db_manager.list_evidences(limit=500)
            if not evidences:
                QMessageBox.information(self, "Reporte de Calidad", "No hay evidencias registradas todavía para generar reporte.")
                return

            reports_dir = os.path.abspath("reports")
            os.makedirs(reports_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(reports_dir, f"reporte_calidad_tejas_{timestamp}.csv")

            total = len(evidences)
            no_conformes = sum(1 for e in evidences if (e.get("defects_count") or 0) > 0)
            conformes = total - no_conformes
            rate = (conformes / total * 100.0) if total > 0 else 100.0

            with open(report_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["REPORTE DE CONTROL DE CALIDAD - INSPECCIÓN DE TEJAS"])
                writer.writerow(["Fecha de Generación", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow(["Total de Muestras Inspeccionadas", total])
                writer.writerow(["Conformes (Aprobadas)", conformes])
                writer.writerow(["No Conformes (Rechazadas)", no_conformes])
                writer.writerow(["Índice de Calidad (Yield)", f"{rate:.1f}%"])
                writer.writerow([])
                writer.writerow(["ID Evidencia", "Fecha/Hora", "Resolución", "Modelo IA", "Defectos", "Estado Revisión", "Ruta Archivo Original"])

                for ev in evidences:
                    writer.writerow([
                        ev.get("id"),
                        ev.get("timestamp"),
                        f"{ev.get('width', 0)}x{ev.get('height', 0)}",
                        ev.get("model_name"),
                        ev.get("defects_count", 0),
                        ev.get("review_status", "PENDIENTE"),
                        ev.get("original_image_path", "")
                    ])

            QMessageBox.information(
                self,
                "Reporte Generado",
                f"✅ Reporte de control de calidad generado exitosamente.\n\n"
                f"Muestras analizadas: {total}\n"
                f"No conformidades: {no_conformes}\n"
                f"Calidad del turno: {rate:.1f}%\n\n"
                f"Guardado en:\n{report_file}"
            )
            # Abrir carpeta del reporte
            try:
                os.startfile(reports_dir)
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "Error al generar reporte", f"No se pudo exportar el reporte: {e}")

    def _open_image_inspector(self):
        from src.app.image_report_dialog import ImageInspectionReportDialog
        
        # Si la cámara tiene un último fotograma capturado o en memoria, podemos ofrecerlo
        temp_img_path = None
        if hasattr(self, "_last_frame_clean") and self._last_frame_clean is not None:
            # Guardar fotograma actual en scratch para inspección rápida
            os.makedirs("data/temp", exist_ok=True)
            temp_img_path = os.path.abspath("data/temp/live_snapshot.png")
            cv2.imwrite(temp_img_path, self._last_frame_clean)

        # Usar el detector YOLO configurado en el sistema
        detector_to_use = self.active_detector or self.yolo_detector

        dlg = ImageInspectionReportDialog(
            detector=detector_to_use,
            mm_per_pixel=self.spin_mm_px.value(),
            initial_image_path=temp_img_path,
            parent=self
        )
        dlg.exec()

    def _open_history_dialog(self):
        dlg = EvidenceHistoryDialog(self.db_manager, self)
        dlg.exec()

    def _open_evidence_folder(self):
        folder = os.path.abspath(self.settings.storage.evidence_dir)
        os.makedirs(folder, exist_ok=True)
        try:
            os.startfile(folder)
        except Exception as e:
            QMessageBox.information(self, "Carpeta de Evidencias", f"Ruta de evidencias:\n{folder}")

    def _open_defect_window(self):
        """Abre o trae al frente la Terminal Independiente de Defectos para estaciones multi-monitor."""
        if hasattr(self, "defect_window") and self.defect_window is not None:
            self.defect_window.show()
            self.defect_window.raise_()
            self.defect_window.activateWindow()

    def closeEvent(self, event):
        """Cierre seguro garantizando detención de hilos y liberación de recursos."""
        self._stop_capture()
        if hasattr(self, "defect_window") and self.defect_window is not None:
            self.defect_window.close()
        event.accept()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from src.utils.logging_config import setup_logging

    setup_logging(log_dir="logs")
    app = QApplication(sys.argv)
    app.setApplicationName("Sistema de Visión Artificial - Inspección de Láminas")
    app.setOrganizationName("Control de Calidad e Ingeniería")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

