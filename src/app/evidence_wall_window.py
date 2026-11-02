import cv2
import numpy as np
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QFrame, QScrollArea, QGridLayout,
    QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap

class EvidenceWallWindow(QMainWindow):
    """
    Ventana independiente de Estación de Monitoreo CCTV / Mosaico de Evidencias (Video Wall).
    Muestra en cuadrícula responsiva (estilo 4x2, 4x3 o 6x4) las fotos de no conformidades,
    permitiendo inspeccionar cada captura en alta definición al hacer clic, sin saturar
    la ventana principal.
    """

    open_detail_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mural de Evidencias CCTV — Monitoreo Continuo de Defectos")
        self.resize(1080, 680)
        self.setMinimumSize(780, 500)

        self.cards_data: List[Dict[str, Any]] = []

        self._setup_style()
        self._setup_ui()

    def _setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0d10;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QWidget {
                color: #d0d0d0;
                font-size: 12px;
            }
            QGroupBox {
                border: 1px solid #21262d;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 12px;
                font-weight: bold;
                color: #4da6ff;
            }
            QPushButton {
                background-color: #1a2230;
                border: 1px solid #303e54;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: 500;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #243247;
                border-color: #007acc;
            }
            QScrollBar:vertical {
                border: none;
                background: #0d0f12;
                width: 8px;
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
        """)

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # Barra superior con estadísticas y controles
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #12151b; border: 1px solid #212733; border-radius: 6px; padding: 6px 12px;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(6, 4, 6, 4)

        title_col = QVBoxLayout()
        lbl_title = QLabel("ESTACIÓN DE MONITOREO CCTV — MOSAICO DE NO CONFORMIDADES")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #58a6ff;")
        title_col.addWidget(lbl_title)

        self.lbl_stats = QLabel("0 evidencias capturadas | Filtro anti-duplicados: ACTIVO")
        self.lbl_stats.setStyleSheet("font-size: 11px; color: #8b949e;")
        title_col.addWidget(self.lbl_stats)
        top_layout.addLayout(title_col)

        top_layout.addStretch()

        self.btn_clear = QPushButton("🧹 Limpiar Vista de Mosaico")
        self.btn_clear.clicked.connect(self.clear_wall)
        top_layout.addWidget(self.btn_clear)

        main_layout.addWidget(top_bar)

        # Cuadrícula responsiva con scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("background-color: #08090c; border: 1px solid #1a1e24; border-radius: 6px;")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.lbl_empty = QLabel("Las evidencias capturadas en vivo aparecerán organizadas en este mosaico automáticamente.")
        self.lbl_empty.setStyleSheet("color: #484f58; font-size: 13px; font-style: italic; padding: 40px;")
        self.lbl_empty.setAlignment(Qt.AlignCenter)
        self.grid_layout.addWidget(self.lbl_empty, 0, 0, 1, 4)

        self.scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll_area)

    def add_evidence(self, frame: np.ndarray, meta: dict):
        """Agrega una nueva foto al mosaico multicámara."""
        if frame is None or frame.size == 0:
            return

        if self.lbl_empty.isVisible():
            self.lbl_empty.setVisible(False)

        # Miniatura nítida
        h, w = frame.shape[:2]
        target_w = 240
        target_h = int(h * (target_w / max(1, w)))
        rgb = cv2.cvtColor(cv2.resize(frame, (target_w, target_h)), cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, target_w, target_h, target_w * 3, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)

        # Crear Card estilo cámara industrial
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #12151b;
                border: 1px solid #2d333b;
                border-radius: 5px;
                padding: 4px;
            }
            QFrame:hover {
                border-color: #007acc;
                background-color: #171c24;
            }
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(4, 4, 4, 4)
        c_layout.setSpacing(4)

        lbl_pic = QLabel()
        lbl_pic.setPixmap(pix)
        lbl_pic.setAlignment(Qt.AlignCenter)
        lbl_pic.setStyleSheet("background-color: #000000; border-radius: 3px;")
        c_layout.addWidget(lbl_pic)

        ev_id = meta.get("evidence_id", len(self.cards_data) + 1)
        source = meta.get("source_info", "En Vivo")
        time_str = meta.get("time_str", "")

        info_row = QHBoxLayout()
        info_lbl = QLabel(f"<b>CÁMARA #{len(self.cards_data)+1:02d}</b> | Evidencia #{ev_id}")
        info_lbl.setStyleSheet("color: #58a6ff; font-size: 11px;")
        info_row.addWidget(info_lbl)
        info_row.addStretch()

        btn_inspect = QPushButton("🔍 Inspeccionar")
        btn_inspect.setStyleSheet("""
            QPushButton {
                background-color: #005a9e;
                color: #ffffff;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 6px;
                border-radius: 3px;
                border: none;
            }
            QPushButton:hover {
                background-color: #007acc;
            }
        """)
        info_row.addWidget(btn_inspect)
        c_layout.addLayout(info_row)

        sub_lbl = QLabel(f"⏱ {time_str} | {source}")
        sub_lbl.setStyleSheet("color: #8b949e; font-size: 10px;")
        c_layout.addWidget(sub_lbl)

        # Referencia para el diálogo de detalle
        card_entry = {
            "widget": card,
            "meta": meta,
            "frame_annot": frame.copy(),
            "frame_orig": meta.get("frame_orig", frame).copy()
        }

        # Permitir tocar la imagen o hacer clic en el botón para abrir el visor con zoom
        def open_card_detail(event=None):
            self._open_detail_for_entry(card_entry)

        card.mousePressEvent = open_card_detail
        lbl_pic.mousePressEvent = open_card_detail
        btn_inspect.clicked.connect(lambda: self._open_detail_for_entry(card_entry))

        self.cards_data.insert(0, card_entry)

        # Limitar a 48 capturas activas en el mural
        if len(self.cards_data) > 48:
            old = self.cards_data.pop()
            old["widget"].setParent(None)
            old["widget"].deleteLater()

        self._rebuild_grid()
        self.lbl_stats.setText(f"{len(self.cards_data)} evidencias en mosaico CCTV | Filtro anti-duplicados: ACTIVO")

    def _open_detail_for_entry(self, card_entry: dict):
        """Abre el visor en alta definición con zoom interactivo, filtros y dictamen de calidad."""
        from src.app.evidence_detail_dialog import EvidenceDetailDialog
        
        dlg = EvidenceDetailDialog(self)
        dlg.load_evidence(
            frame_orig=card_entry.get("frame_orig"),
            frame_annot=card_entry.get("frame_annot"),
            meta=card_entry.get("meta", {})
        )

        # Si el diálogo guarda un dictamen, emitir o actualizar BD
        if hasattr(self.parent(), "db_manager") and self.parent().db_manager:
            def on_verdict(ev_id, verd, notes):
                try:
                    self.parent().db_manager.update_evidence_review(ev_id, verd, notes)
                except Exception:
                    pass
            dlg.verdict_saved.connect(on_verdict)

        dlg.exec()

    def _rebuild_grid(self):
        # Limpiar layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget() and item.widget() != self.lbl_empty:
                item.widget().setParent(None)

        cols = 4  # 4 columnas estilo pantalla dividida (Quad/CCTV)
        for idx, item in enumerate(self.cards_data):
            row = idx // cols
            col = idx % cols
            self.grid_layout.addWidget(item["widget"], row, col)

    def clear_wall(self):
        for item in self.cards_data:
            item["widget"].setParent(None)
            item["widget"].deleteLater()
        self.cards_data.clear()
        self.lbl_empty.setVisible(True)
        self.grid_layout.addWidget(self.lbl_empty, 0, 0, 1, 4)
        self.lbl_stats.setText("0 evidencias capturadas | Filtro anti-duplicados: ACTIVO")

