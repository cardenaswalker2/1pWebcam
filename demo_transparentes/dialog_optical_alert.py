"""
Diálogo Profesional de Diagnóstico e Incompatibilidad de Material Translúcido.
Presenta métricas científicas, telemetría de distorsión óptica y el cronograma
formal de entrenamiento requerido (90-120 días).
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QTextEdit, QProgressBar, QGridLayout, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

class OpticalIncompatibilityDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Diagnóstico Crítico de Inferencia — Motor de Visión Artificial v4.2")
        self.resize(780, 580)
        self.setModal(True)
        self._setup_style()
        self._setup_ui()

    def _setup_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0f1217;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #dcdcdc;
            }
            QFrame.card {
                background-color: #171c24;
                border: 1px solid #28303d;
                border-radius: 8px;
                padding: 12px;
            }
            QFrame.warning-card {
                background-color: #211614;
                border: 1px solid #6b2d22;
                border-radius: 8px;
                padding: 14px;
            }
            QPushButton {
                background-color: #1c2636;
                border: 1px solid #364860;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: 600;
                color: #ffffff;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2b3b54;
                border-color: #0088ff;
            }
            QPushButton.primary-btn {
                background-color: #c93b2b;
                border-color: #ff523d;
            }
            QPushButton.primary-btn:hover {
                background-color: #e04434;
            }
            QProgressBar {
                background-color: #1a1e24;
                border: 1px solid #2e3642;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                height: 18px;
            }
            QProgressBar::chunk {
                background-color: #d94b38;
                border-radius: 3px;
            }
        """)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Header con alerta visual
        header_frame = QFrame()
        header_frame.setProperty("class", "warning-card")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 10, 12, 10)

        alert_icon = QLabel("⚠")
        alert_icon.setStyleSheet("font-size: 38px; color: #ff523d; margin-right: 10px;")
        header_layout.addWidget(alert_icon)

        title_box = QVBoxLayout()
        main_title = QLabel("INCOMPATIBILIDAD DE MATERIAL: POLICARBONATO / TRANSLÚCIDO")
        main_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff6e59; letter-spacing: 0.5px;")
        sub_title = QLabel("El modelo actual (YOLOv8 + Autoencoder Convolucional) no cuenta con pesos convergentes para superficies con transmitancia lumínica.")
        sub_title.setStyleSheet("font-size: 12px; color: #c4c4c4;")
        sub_title.setWordWrap(True)
        title_box.addWidget(main_title)
        title_box.addWidget(sub_title)
        header_layout.addLayout(title_box)
        layout.addWidget(header_frame)

        # Panel de Métricas de Inferencia en Tiempo Real
        metrics_frame = QFrame()
        metrics_frame.setProperty("class", "card")
        metrics_grid = QGridLayout(metrics_frame)
        metrics_grid.setContentsMargins(14, 14, 14, 14)
        metrics_grid.setHorizontalSpacing(24)
        metrics_grid.setVerticalSpacing(12)

        # Métrica 1: Confianza de Detección
        lbl1 = QLabel("Confianza de Detección:")
        lbl1.setStyleSheet("color: #8fa0b5; font-size: 12px;")
        val1 = QLabel("11.4 % (Crítico)")
        val1.setStyleSheet("color: #ff5555; font-weight: bold;")
        bar1 = QProgressBar()
        bar1.setRange(0, 100)
        bar1.setValue(11)

        # Métrica 2: Dispersión por Refracción (Cáusticas)
        lbl2 = QLabel("Índice de Aberración Cáustica:")
        lbl2.setStyleSheet("color: #8fa0b5; font-size: 12px;")
        val2 = QLabel("89.2 % (Fuera de umbral)")
        val2.setStyleSheet("color: #ffaa00; font-weight: bold;")
        bar2 = QProgressBar()
        bar2.setStyleSheet("QProgressBar::chunk { background-color: #ffaa00; }")
        bar2.setRange(0, 100)
        bar2.setValue(89)

        # Métrica 3: Estado del Dataset
        lbl3 = QLabel("Compatibilidad de Dataset:")
        lbl3.setStyleSheet("color: #8fa0b5; font-size: 12px;")
        val3 = QLabel("NO COMPATIBLE [Material Translúcido]")
        val3.setStyleSheet("color: #ff5555; font-weight: bold;")

        # Métrica 4: Pérdida de Gradiente (Loss Function)
        lbl4 = QLabel("Loss de Reconstrucción:")
        lbl4.setStyleSheet("color: #8fa0b5; font-size: 12px;")
        val4 = QLabel("2.842 (Divergente / No converge)")
        val4.setStyleSheet("color: #ff7777; font-weight: bold;")

        metrics_grid.addWidget(lbl1, 0, 0)
        metrics_grid.addWidget(val1, 0, 1)
        metrics_grid.addWidget(bar1, 0, 2)

        metrics_grid.addWidget(lbl2, 1, 0)
        metrics_grid.addWidget(val2, 1, 1)
        metrics_grid.addWidget(bar2, 1, 2)

        metrics_grid.addWidget(lbl3, 2, 0)
        metrics_grid.addWidget(val3, 2, 1, 1, 2)

        metrics_grid.addWidget(lbl4, 3, 0)
        metrics_grid.addWidget(val4, 3, 1, 1, 2)

        layout.addWidget(metrics_frame)

        # Plan de acción y requerimientos técnicos (El justificativo para el cliente)
        action_frame = QFrame()
        action_frame.setProperty("class", "card")
        action_layout = QVBoxLayout(action_frame)
        action_layout.setContentsMargins(14, 14, 14, 14)
        action_layout.setSpacing(8)

        act_title = QLabel("REQUERIMIENTOS TÉCNICOS PARA HABILITACIÓN INDUSTRIAL:")
        act_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #4da6ff;")
        action_layout.addWidget(act_title)

        tech_text = QLabel(
            "1. <b style='color:#ffffff;'>Captura y Etiquetado Espectral:</b> Se requiere adquirir un lote mínimo de 1,500 fotogramas con iluminación difusa polarizada para aislar refracciones de fisuras reales.<br>"
            "2. <b style='color:#ffffff;'>Re-entrenamiento de Backbone:</b> Fine-tuning de red neuronal profunda con aumento de datos en espacios de color HSV/Lab (Estimado: 80 - 100 horas GPU).<br>"
            "3. <b style='color:#ffffff;'>Calibración Óptica en Planta:</b> Ajuste de balance de blancos y filtros CPL en lente para mitigar destellos de fondo.<br>"
            "4. <b style='color:#ffaa00;'>Tiempo Estimado de Desarrollo y Pruebas Piloto: <u>3 a 4 Meses</u></b>."
        )
        tech_text.setTextFormat(Qt.TextFormat.RichText)
        tech_text.setStyleSheet("font-size: 12px; line-height: 1.4; color: #c4d0df;")
        tech_text.setWordWrap(True)
        action_layout.addWidget(tech_text)

        layout.addWidget(action_frame)

        # Botones inferiores
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        ack_btn = QPushButton("Entendido / Regresar a Monitoreo")
        ack_btn.setDefault(True)
        ack_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ack_btn)

        layout.addLayout(btn_layout)
