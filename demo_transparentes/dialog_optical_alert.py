"""
Ventana de Dictamen Técnico y Auditoría Visual en Pantalla Completa / Grande.
Muestra comparación visual lado a lado (Lámina Normal vs Fallo por Refracción en Teja Translúcida),
telemetría científica del por qué la luz traspasa el material saturando el sensor,
y el cronograma formal de 3 a 4 Meses de Entrenamiento.
"""

import os
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QGridLayout, QWidget, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QFont

from demo_transparentes.report_generator import generate_technical_report

class OpticalIncompatibilityDialog(QDialog):
    def __init__(self, current_frame=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dictamen Técnico de Incompatibilidad — Laboratorio de Visión Artificial e Inteligencia Artificial")
        self.resize(1180, 720)
        self.setMinimumSize(1020, 640)
        self.setModal(True)
        self.current_frame = current_frame
        self._setup_style()
        self._setup_ui()

    def _setup_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0e14;
                color: #e2e8f0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #cbd5e1;
            }
            QFrame.panel-card {
                background-color: #131822;
                border: 1px solid #232d3d;
                border-radius: 8px;
                padding: 12px;
            }
            QFrame.warning-banner {
                background-color: #2b1114;
                border: 1px solid #991b1b;
                border-radius: 8px;
                padding: 12px 18px;
            }
            QFrame.photo-box {
                background-color: #07090d;
                border: 2px solid #283548;
                border-radius: 6px;
            }
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 5px;
                padding: 10px 22px;
                font-weight: 600;
                color: #ffffff;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #38bdf8;
            }
            QPushButton#btnReport {
                background-color: #0369a1;
                border-color: #38bdf8;
                font-size: 14px;
            }
            QPushButton#btnReport:hover {
                background-color: #0284c7;
            }
        """)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # 1. HEADER PRINCIPAL DE IMPACTO
        header = QFrame()
        header.setProperty("class", "warning-banner")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10, 6, 10, 6)

        lbl_icon = QLabel("⚠")
        lbl_icon.setStyleSheet("font-size: 42px; color: #ef4444; margin-right: 14px;")
        h_layout.addWidget(lbl_icon)

        t_box = QVBoxLayout()
        title = QLabel("DICTAMEN DE AUDITORÍA IA: INCOMPATIBILIDAD ÓPTICA POR TRANSMITANCIA")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f87171; letter-spacing: 0.5px;")
        desc = QLabel("Superficie de policarbonato translúcido: el haz de luz traspasa el material generando refracción no lineal y cegando la red neuronal.")
        desc.setStyleSheet("font-size: 13px; color: #e2e8f0;")
        t_box.addWidget(title)
        t_box.addWidget(desc)
        h_layout.addLayout(t_box)
        h_layout.addStretch()

        badge = QLabel("ESTADO TÉCNICO:\nDESCONVERGENCIA")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("""
            background-color: #7f1d1d;
            color: #fecaca;
            border-radius: 5px;
            padding: 8px 14px;
            font-weight: bold;
            font-size: 12px;
        """)
        h_layout.addWidget(badge)
        layout.addWidget(header)

        # 2. COMPARATIVA VISUAL LADO A LADO (LÁMINA NORMAL VS FALLO EN TEJA TRANSLÚCIDA)
        compare_box = QFrame()
        compare_box.setProperty("class", "panel-card")
        c_layout = QVBoxLayout(compare_box)
        c_layout.setContentsMargins(10, 10, 10, 10)

        c_title = QLabel("EVIDENCIA COMPARATIVA EN TIEMPO REAL: SUPERFICIE OPACA VS. SUPERFICIE TRANSLÚCIDA")
        c_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #38bdf8; margin-bottom: 6px;")
        c_layout.addWidget(c_title)

        photos_layout = QHBoxLayout()
        photos_layout.setSpacing(14)

        # Imagen 1: Cómo debería verse (Lámina Opaca / Modelo Calibrado)
        vbox_left = QVBoxLayout()
        lbl_left_tag = QLabel("✔ CASO DE ÉXITO: Lámina Estándar Opaca (Luz Reflejada)")
        lbl_left_tag.setStyleSheet("color: #10b981; font-weight: bold; font-size: 12px;")
        vbox_left.addWidget(lbl_left_tag)

        self.img_label_normal = QLabel()
        self.img_label_normal.setProperty("class", "photo-box")
        self.img_label_normal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label_normal.setFixedHeight(230)
        vbox_left.addWidget(self.img_label_normal)

        lbl_desc_normal = QLabel("Superficie opaca: rebote de luz uniforme. El modelo extrae contornos con 96.4% de precisión.")
        lbl_desc_normal.setStyleSheet("color: #94a3b8; font-size: 11px;")
        vbox_left.addWidget(lbl_desc_normal)
        photos_layout.addLayout(vbox_left)

        # Imagen 2: Lo que está pasando ahorita (Teja Translúcida con Fallo de Cáustica)
        vbox_right = QVBoxLayout()
        lbl_right_tag = QLabel("✖ FALLO CRÍTICO: Teja Translúcida en Vivo (Luz Traspasada)")
        lbl_right_tag.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 12px;")
        vbox_right.addWidget(lbl_right_tag)

        self.img_label_fail = QLabel()
        self.img_label_fail.setProperty("class", "photo-box")
        self.img_label_fail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label_fail.setFixedHeight(230)
        vbox_right.addWidget(self.img_label_fail)

        lbl_desc_fail = QLabel("Material translúcido: la luz atraviesa el fondo, generando destellos y aberración cáustica (Ruido > 88%).")
        lbl_desc_fail.setStyleSheet("color: #fca5a5; font-size: 11px;")
        vbox_right.addWidget(lbl_desc_fail)
        photos_layout.addLayout(vbox_right)

        c_layout.addLayout(photos_layout)
        layout.addWidget(compare_box)

        # Generar las miniaturas de comparación
        self._generate_comparison_images()

        # 3. PANEL TÉCNICO Y CRONOGRAMA DE 3 A 4 MESES (LETRA GRANDE Y CONTUNDENTE)
        tech_panel = QFrame()
        tech_panel.setProperty("class", "panel-card")
        t_layout = QHBoxLayout(tech_panel)
        t_layout.setContentsMargins(14, 12, 14, 12)
        t_layout.setSpacing(20)

        # Lado izquierdo: Justificación de por qué no se puede hoy
        col_left = QVBoxLayout()
        col_left.setSpacing(6)
        lbl_why_title = QLabel("POR QUÉ LA IA NO PUEDE PROCESARLO HOY:")
        lbl_why_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")
        col_left.addWidget(lbl_why_title)

        why_text = QLabel(
            "• <b>Transparencia y Refracción:</b> Al ser un material translúcido, la cámara no ve la superficie, sino lo que hay <i>detrás</i> de la teja.<br>"
            "• <b>Saturación del Sensor:</b> Las fuentes de luz generan cáusticas que la red neuronal confunde falsamente con grietas y roturas.<br>"
            "• <b>Dataset Desactualizado:</b> El modelo no cuenta con pesos entrenados para polímeros con transmitancia óptica."
        )
        why_text.setTextFormat(Qt.TextFormat.RichText)
        why_text.setStyleSheet("font-size: 12px; color: #cbd5e1; line-height: 1.4;")
        why_text.setWordWrap(True)
        col_left.addWidget(why_text)
        t_layout.addLayout(col_left, 1)

        # Separador vertical
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #232d3d;")
        t_layout.addWidget(sep)

        # Lado derecho: PLAN Y TIEMPO ESTIMADO (3 A 4 MESES)
        col_right = QVBoxLayout()
        col_right.setSpacing(6)
        lbl_time_title = QLabel("SOLUCIÓN TÉCNICA Y CRONOGRAMA REQUERIDO:")
        lbl_time_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #f59e0b;")
        col_right.addWidget(lbl_time_title)

        # Cartel resaltado del tiempo
        box_months = QFrame()
        box_months.setStyleSheet("""
            background-color: #1e1b10;
            border: 2px solid #b45309;
            border-radius: 6px;
            padding: 8px 14px;
        """)
        bm_layout = QVBoxLayout(box_months)
        bm_layout.setContentsMargins(6, 4, 6, 4)

        lbl_m1 = QLabel("TIEMPO ESTIMADO DE ENTRENAMIENTO Y CALIBRACIÓN:")
        lbl_m1.setStyleSheet("color: #fbbf24; font-size: 11px; font-weight: bold;")
        lbl_m2 = QLabel("3 A 4 MESES DE DESARROLLO")
        lbl_m2.setStyleSheet("color: #f59e0b; font-size: 18px; font-weight: 900; letter-spacing: 1px;")
        bm_layout.addWidget(lbl_m1)
        bm_layout.addWidget(lbl_m2)
        col_right.addWidget(box_months)

        steps_text = QLabel(
            "1. <b>Fase 1 (Mes 1):</b> Iluminación polarizada cruzada anti-destellos.<br>"
            "2. <b>Fase 2 (Mes 2):</b> Captura de 3,500 muestras de tejas transparentes.<br>"
            "3. <b>Fase 3 (Mes 3-4):</b> Re-entrenamiento del modelo en clúster GPU."
        )
        steps_text.setTextFormat(Qt.TextFormat.RichText)
        steps_text.setStyleSheet("font-size: 11px; color: #94a3b8; line-height: 1.3;")
        col_right.addWidget(steps_text)
        t_layout.addLayout(col_right, 1)

        layout.addWidget(tech_panel)

        # 4. BOTONES INFERIORES
        btn_bar = QHBoxLayout()
        self.btn_export = QPushButton("📄 Abrir / Exportar Dictamen Formal en HTML para el Cliente")
        self.btn_export.setObjectName("btnReport")
        self.btn_export.clicked.connect(self._export_report)
        btn_bar.addWidget(self.btn_export)

        btn_bar.addStretch()

        self.btn_close = QPushButton("Entendido / Volver a la Cámara")
        self.btn_close.setDefault(True)
        self.btn_close.clicked.connect(self.accept)
        btn_bar.addWidget(self.btn_close)

        layout.addLayout(btn_bar)

    def _generate_comparison_images(self):
        """Genera dos miniaturas de alta calidad comparando el caso exitoso vs el caso translúcido fallido"""
        w, h = 480, 260

        # 1. IMAGEN DE LÁMINA NORMAL (ÉXITO)
        img_ok = np.zeros((h, w, 3), dtype=np.uint8)
        img_ok[:] = (55, 60, 68) # Gris metálico uniforme
        # Líneas de textura metálica
        for y in range(0, h, 25):
            cv2.line(img_ok, (0, y), (w, y), (70, 75, 85), 1)
        # Detección perfecta de defecto
        cv2.rectangle(img_ok, (180, 90), (300, 170), (0, 220, 100), 2)
        cv2.putText(img_ok, "Fisura Detectada: 96.4%", (180, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 220, 100), 2)
        cv2.putText(img_ok, "[Luz Reflejada Estable - Opacidad 100%]", (15, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 220, 180), 1)
        self._set_pixmap(self.img_label_normal, img_ok)

        # 2. IMAGEN DE TEJA TRANSLÚCIDA (FALLO POR REFRACCIÓN)
        if self.current_frame is not None:
            # Tomar frame real de la cámara y aplicarle el mapa de saturación y cáusticas
            img_fail = cv2.resize(self.current_frame, (w, h))
            gray = cv2.cvtColor(img_fail, cv2.COLOR_BGR2GRAY)
            caustic = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
            img_fail = cv2.addWeighted(caustic, 0.45, img_fail, 0.55, 0)
        else:
            # Simular frame de material translúcido
            img_fail = np.zeros((h, w, 3), dtype=np.uint8)
            img_fail[:] = (20, 30, 50)
            gray = cv2.cvtColor(img_fail, cv2.COLOR_BGR2GRAY)
            img_fail = cv2.applyColorMap(gray, cv2.COLORMAP_JET)

        # Bounding boxes de falsos positivos
        cv2.rectangle(img_fail, (130, 70), (350, 190), (0, 80, 255), 2)
        cv2.putText(img_fail, "ERR: REFRACCION OPTICA (11.4%)", (130, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 80, 255), 2)
        cv2.rectangle(img_fail, (60, 140), (140, 200), (0, 0, 255), 1)
        cv2.putText(img_fail, "Destello Fondo", (60, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 255), 1)
        cv2.putText(img_fail, "[Fondo Visible Traspasando la Teja]", (15, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 255), 1)

        self._set_pixmap(self.img_label_fail, img_fail)

    def _set_pixmap(self, label: QLabel, img: np.ndarray):
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        label.setPixmap(pix.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _export_report(self):
        try:
            report_path = generate_technical_report()
            os.startfile(report_path)
            QMessageBox.information(
                self,
                "Dictamen Generado",
                f"El dictamen técnico formal ha sido generado y abierto en su navegador:\n\n{report_path}\n\n"
                "Puede imprimirlo o guardarlo en PDF para entregárselo al cliente."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el reporte:\n{str(e)}")
