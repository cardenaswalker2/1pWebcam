"""
Ventana Principal — Sistema de Inspección Óptica para Láminas y Tejas Translúcidas.
Diseñada para demostración técnica con soporte completo de IP Webcam, cámara USB y fuente sintética.
Incluye modo de simulación de incompatibilidad con disparador [Ctrl+X] o tecla [X].
"""

import sys
import os
import time
from typing import Optional
import cv2
import numpy as np

# Rutas del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox,
    QStatusBar, QMessageBox, QFrame, QSizePolicy, QSplitter, QComboBox
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QImage, QPixmap, QFont, QKeySequence, QShortcut

from src.camera.ip_webcam_source import IPWebcamSource
from src.camera.usb_camera_source import USBCameraSource
from src.camera.synthetic_source import SyntheticSheetSource
from src.app.camera_worker import CameraWorker
from demo_transparentes.transparent_engine import TransparentInferenceEngine
from demo_transparentes.dialog_optical_alert import OpticalIncompatibilityDialog

class TransparentInspectionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Visión Artificial — Inspección de Tejas y Perfiles Translúcidos v4.2")
        self.resize(1200, 780)
        self.setMinimumSize(1000, 620)

        # Motor de inferencia especializado
        self.engine = TransparentInferenceEngine()
        self.camera_worker: Optional[CameraWorker] = None
        self.last_raw_frame: Optional[np.ndarray] = None

        # Atajos de teclado para la demostración
        # 1. Ctrl+X
        self.shortcut_ctrl_x = QShortcut(QKeySequence("Ctrl+X"), self)
        self.shortcut_ctrl_x.activated.connect(self.trigger_demo_alert)

        # 2. X sola (para máxima facilidad en caso de pulsar rápido)
        self.shortcut_x = QShortcut(QKeySequence("X"), self)
        self.shortcut_x.activated.connect(self.trigger_demo_alert)

        # 3. Tecla R para reiniciar el estado si se desea
        self.shortcut_r = QShortcut(QKeySequence("Ctrl+R"), self)
        self.shortcut_r.activated.connect(self.reset_demo_state)

        self._setup_style()
        self._setup_ui()

    def _setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #111419;
                color: #e2e8f0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QWidget {
                color: #cbd5e1;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #2d3748;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 14px;
                font-weight: bold;
                color: #38bdf8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
            }
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 7px 16px;
                font-weight: 500;
                color: #f1f5f9;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #0284c7;
            }
            QPushButton:pressed {
                background-color: #0f172a;
            }
            QPushButton#btnConnect {
                background-color: #0369a1;
                border-color: #38bdf8;
                font-weight: bold;
            }
            QPushButton#btnConnect:hover {
                background-color: #0284c7;
            }
            QPushButton#btnDisconnect {
                background-color: #881337;
                border-color: #f43f5e;
            }
            QPushButton#btnDisconnect:hover {
                background-color: #9f1239;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 5px 8px;
                color: #ffffff;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #38bdf8;
            }
        """)

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        # Divisor principal
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ------------------ PANEL IZQUIERDO: CONTROLES ------------------
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(12)
        left_panel.setMaximumWidth(360)
        left_panel.setMinimumWidth(300)

        # 1. Origen de Video
        source_group = QGroupBox("FUENTE DE CAPTURA ÓPTICA")
        source_layout = QVBoxLayout(source_group)

        src_type_layout = QHBoxLayout()
        src_type_layout.addWidget(QLabel("Dispositivo:"))
        self.combo_source = QComboBox()
        self.combo_source.addItems(["IP Webcam (Wi-Fi/LAN)", "Cámara USB / Industrial", "Simulador Sintético"])
        self.combo_source.currentIndexChanged.connect(self._on_source_changed)
        src_type_layout.addWidget(self.combo_source)
        source_layout.addLayout(src_type_layout)

        # Entrada URL IP
        self.lbl_ip = QLabel("URL del Stream IP Webcam:")
        source_layout.addWidget(self.lbl_ip)
        self.input_ip = QLineEdit("http://192.168.1.50:8080/video")
        source_layout.addWidget(self.input_ip)

        # Botones de Conexión
        btn_conn_layout = QHBoxLayout()
        self.btn_connect = QPushButton("Conectar Cámara")
        self.btn_connect.setObjectName("btnConnect")
        self.btn_connect.clicked.connect(self._start_camera)
        btn_conn_layout.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton("Detener")
        self.btn_disconnect.setObjectName("btnDisconnect")
        self.btn_disconnect.setEnabled(False)
        self.btn_disconnect.clicked.connect(self._stop_camera)
        btn_conn_layout.addWidget(self.btn_disconnect)
        source_layout.addLayout(btn_conn_layout)

        left_layout.addWidget(source_group)

        # 2. Configuración de Inferencia y Óptica
        optics_group = QGroupBox("PARÁMETROS DE REFRACCIÓN Y MODELO")
        optics_layout = QVBoxLayout(optics_group)

        # Selector de Modelo
        optics_layout.addWidget(QLabel("Red Neuronal de Inferencia:"))
        self.combo_model = QComboBox()
        self.combo_model.addItems(["YOLOv8-OpticTrans v4.2 [Policarbonato]", "PatchCore-Spectral AutoEncoder"])
        optics_layout.addWidget(self.combo_model)

        # Parámetro Índice de Refracción
        idx_layout = QHBoxLayout()
        idx_layout.addWidget(QLabel("Índice Refracción (η):"))
        self.spin_eta = QDoubleSpinBox()
        self.spin_eta.setRange(1.000, 2.000)
        self.spin_eta.setValue(1.492) # Policarbonato
        self.spin_eta.setSingleStep(0.005)
        idx_layout.addWidget(self.spin_eta)
        optics_layout.addLayout(idx_layout)

        # Filtro de Aberración Cromática
        self.chk_cpl = QCheckBox("Filtro Polarizador Digital (CPL)")
        self.chk_cpl.setChecked(True)
        optics_layout.addWidget(self.chk_cpl)

        # Sensibilidad
        sens_layout = QHBoxLayout()
        sens_layout.addWidget(QLabel("Umbral Confianza:"))
        self.spin_conf = QDoubleSpinBox()
        self.spin_conf.setRange(0.10, 0.99)
        self.spin_conf.setValue(0.75)
        self.spin_conf.setSingleStep(0.05)
        sens_layout.addWidget(self.spin_conf)
        optics_layout.addLayout(sens_layout)

        left_layout.addWidget(optics_group)

        # 3. Estado de Telemetría
        status_group = QGroupBox("TELEMETRÍA DE INFERENCIA")
        status_layout = QVBoxLayout(status_group)

        self.lbl_telemetry_status = QLabel("ESTADO: EN ESPERA DE STREAM")
        self.lbl_telemetry_status.setStyleSheet("font-weight: bold; color: #94a3b8;")
        status_layout.addWidget(self.lbl_telemetry_status)

        self.lbl_fps_info = QLabel("FPS Inferencia: -- | Latencia: -- ms")
        self.lbl_fps_info.setStyleSheet("color: #64748b; font-size: 11px;")
        status_layout.addWidget(self.lbl_fps_info)

        self.lbl_convergence = QLabel("Convergencia Espectral: ESTABLE (0.00)")
        self.lbl_convergence.setStyleSheet("color: #64748b; font-size: 11px;")
        status_layout.addWidget(self.lbl_convergence)

        left_layout.addWidget(status_group)

        left_layout.addStretch()

        # Nota al pie sutil
        lbl_hint = QLabel("Atajo de diagnóstico: [Ctrl+X]")
        lbl_hint.setStyleSheet("color: #475569; font-size: 10px; font-style: italic;")
        left_layout.addWidget(lbl_hint)

        splitter.addWidget(left_panel)

        # ------------------ PANEL DERECHO: VISOR DE VIDEO ------------------
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 6, 6, 6)

        # Banner de Estado Superior
        self.top_status_banner = QFrame()
        self.top_status_banner.setStyleSheet("background-color: #1e293b; border-radius: 5px; padding: 6px;")
        top_banner_layout = QHBoxLayout(self.top_status_banner)
        top_banner_layout.setContentsMargins(10, 4, 10, 4)

        self.lbl_banner_text = QLabel("● SISTEMA EN LÍNEA: Monitoreo Espectral y Detección de Fisuras en Polímeros")
        self.lbl_banner_text.setStyleSheet("font-weight: bold; color: #38bdf8;")
        top_banner_layout.addWidget(self.lbl_banner_text)

        top_banner_layout.addStretch()

        self.lbl_clock = QLabel("CALIBRACIÓN: ACTIVA")
        self.lbl_clock.setStyleSheet("color: #10b981; font-weight: bold; font-size: 11px;")
        top_banner_layout.addWidget(self.lbl_clock)

        right_layout.addWidget(self.top_status_banner)

        # Área de Video
        self.video_label = QLabel("CONECTE LA CÁMARA O INICIE EL SIMULADOR\n\n(Soporta URL de IP Webcam, cámara USB o video sintético)")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("""
            background-color: #090b0e;
            border: 2px solid #1e293b;
            border-radius: 8px;
            color: #64748b;
            font-size: 14px;
            font-weight: 500;
        """)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout.addWidget(self.video_label)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # Barra de estado
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Sistema listo para operar. Presione Conectar Cámara.")

    def _on_source_changed(self, index: int):
        if index == 0:
            self.lbl_ip.setText("URL del Stream IP Webcam:")
            self.input_ip.setText("http://192.168.1.50:8080/video")
            self.input_ip.setEnabled(True)
        elif index == 1:
            self.lbl_ip.setText("Índice de Cámara USB (0, 1, 2...):")
            self.input_ip.setText("0")
            self.input_ip.setEnabled(True)
        else:
            self.lbl_ip.setText("Simulador de Lámina Translúcida:")
            self.input_ip.setText("[Generador Sintético Interno]")
            self.input_ip.setEnabled(False)

    def _start_camera(self):
        source_idx = self.combo_source.currentIndex()
        try:
            if source_idx == 0:
                url = self.input_ip.text().strip()
                if not url:
                    QMessageBox.warning(self, "Error de URL", "Por favor ingresa la URL de IP Webcam.")
                    return
                cam_source = IPWebcamSource(url)
            elif source_idx == 1:
                dev_id = int(self.input_ip.text().strip())
                cam_source = USBCameraSource(dev_id)
            else:
                cam_source = SyntheticSheetSource()

            self.camera_worker = CameraWorker(cam_source)
            self.camera_worker.frame_ready.connect(self._on_frame_received)
            self.camera_worker.error_occurred.connect(self._on_camera_error)
            self.camera_worker.start()

            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
            self.combo_source.setEnabled(False)
            self.input_ip.setEnabled(False)
            self.lbl_telemetry_status.setText("ESTADO: STREAMING ACTIVO")
            self.lbl_telemetry_status.setStyleSheet("font-weight: bold; color: #10b981;")
            self.statusBar.showMessage("Captura en tiempo real iniciada.")

        except Exception as e:
            QMessageBox.critical(self, "Fallo al Iniciar Fuente", f"No se pudo conectar a la cámara:\n{str(e)}")

    def _stop_camera(self):
        if self.camera_worker:
            self.camera_worker.stop()
            self.camera_worker.wait(2000)
            self.camera_worker = None

        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self.combo_source.setEnabled(True)
        self.input_ip.setEnabled(True)
        self.lbl_telemetry_status.setText("ESTADO: DETENIDO")
        self.lbl_telemetry_status.setStyleSheet("font-weight: bold; color: #94a3b8;")
        self.statusBar.showMessage("Cámara detenida.")

    @Slot(np.ndarray)
    def _on_frame_received(self, frame: np.ndarray):
        self.last_raw_frame = frame

        # Procesar mediante el motor óptico
        annotated_frame, stats = self.engine.process_frame(frame)

        # Actualizar telemetría de GUI
        fps = stats.get("fps", 30.0)
        ms = stats.get("inference_time_ms", 30.0)
        self.lbl_fps_info.setText(f"FPS Inferencia: {fps:.1f} | Latencia: {ms:.1f} ms")

        if stats.get("status") == "ERROR_REFRACTION_UNCONVERGED":
            self.lbl_telemetry_status.setText("ESTADO: DIVERGENCIA ÓPTICA [CRÍTICO]")
            self.lbl_telemetry_status.setStyleSheet("font-weight: bold; color: #ef4444;")
            self.lbl_convergence.setText("Convergencia: DIVERGENTE (Loss: 2.842)")
            self.lbl_convergence.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 11px;")
            self.top_status_banner.setStyleSheet("background-color: #450a0a; border-radius: 5px; padding: 6px;")
            self.lbl_banner_text.setText("⚠ ATENCIÓN: ABERRACIÓN CÁUSTICA DETECTADA — MODELO NO CONVERGENTE")
            self.lbl_banner_text.setStyleSheet("font-weight: bold; color: #fca5a5;")
            self.lbl_clock.setText("CALIBRACIÓN: SUSPENDIDA")
            self.lbl_clock.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 11px;")
        else:
            self.lbl_telemetry_status.setText("ESTADO: TRANSMISIÓN ÓPTICA NORMAL")
            self.lbl_telemetry_status.setStyleSheet("font-weight: bold; color: #10b981;")
            self.lbl_convergence.setText("Convergencia Espectral: ESTABLE (0.012)")
            self.lbl_convergence.setStyleSheet("color: #10b981; font-size: 11px;")
            self.top_status_banner.setStyleSheet("background-color: #1e293b; border-radius: 5px; padding: 6px;")
            self.lbl_banner_text.setText("● SISTEMA EN LÍNEA: Monitoreo Espectral y Detección de Fisuras en Polímeros")
            self.lbl_banner_text.setStyleSheet("font-weight: bold; color: #38bdf8;")
            self.lbl_clock.setText("CALIBRACIÓN: ACTIVA")
            self.lbl_clock.setStyleSheet("color: #10b981; font-weight: bold; font-size: 11px;")

        # Renderizar en QLabel conservando aspecto
        self._display_frame(annotated_frame)

    def _display_frame(self, frame: np.ndarray):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        # Escalar a la dimensión del label manteniendo aspecto
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)

    @Slot(str)
    def _on_camera_error(self, err_msg: str):
        self._stop_camera()
        self.statusBar.showMessage(f"Error de captura: {err_msg}")
        self.lbl_telemetry_status.setText("ESTADO: ERROR DE CONEXIÓN")
        self.lbl_telemetry_status.setStyleSheet("font-weight: bold; color: #ef4444;")
        QMessageBox.warning(
            self,
            "Error de Conexión con Cámara",
            f"No se pudo conectar al flujo de video:\n{err_msg}\n\n"
            "Verifica que:\n"
            "1. La app 'IP Webcam' en tu celular esté iniciada ('Start server').\n"
            "2. El celular y la PC estén en la misma red Wi-Fi.\n"
            "3. La IP y puerto coincidan con los que muestra la pantalla del celular (ej. http://192.168.1.X:8080/video).\n\n"
            "Consejo para pruebas sin celular: Selecciona 'Simulador Sintético' en Dispositivo."
        )

    def trigger_demo_alert(self):
        """
        Disparado con [Ctrl+X] o [X]:
        Activa el overlay visual en el video y abre el diálogo formal técnico.
        """
        # 1. Activar el HUD parpadeante en el motor de video
        self.engine.trigger_optical_alert()

        # Si no hay cámara activa, crear un frame sintético para que se aprecie de inmediato
        if self.last_raw_frame is None:
            synth = SyntheticSheetSource()
            frame = synth.read()
            if frame is not None:
                self._on_frame_received(frame)

        # 2. Abrir la ventana formal de incompatibilidad
        dialog = OpticalIncompatibilityDialog(self)
        dialog.exec()

    def reset_demo_state(self):
        """Disparado con Ctrl+R para restaurar si se desea continuar demostración normal"""
        self.engine.reset_alert()
        self.statusBar.showMessage("Motor de inferencia restaurado a modo nominal.")

    def closeEvent(self, event):
        self._stop_camera()
        event.accept()
