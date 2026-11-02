import pytest
from src.app.main_window import MainWindow
from src.app.history_dialog import EvidenceHistoryDialog
from src.storage.database import DatabaseManager

def test_main_window_instantiation(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "Sistema de Visión Artificial — Inspección de Láminas Metálicas"
    assert window.badge_cam.text() == "CÁMARA: DESCONECTADA"
    assert window.btn_start.isEnabled()
    assert not window.btn_stop.isEnabled()
    assert not window.btn_capture.isEnabled()

def test_history_dialog_instantiation(qtbot, tmp_path):
    db_file = str(tmp_path / "test_gui_db.db")
    db = DatabaseManager(db_file)
    dlg = EvidenceHistoryDialog(db)
    qtbot.addWidget(dlg)
    assert "Historial de Evidencias" in dlg.windowTitle()
    assert dlg.table.columnCount() == 6
