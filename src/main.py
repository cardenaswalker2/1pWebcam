import sys
import os

# Asegurar que el directorio raíz del proyecto esté en el PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from src.app.main_window import MainWindow
from src.utils.logging_config import setup_logging

def main():
    # Inicializar registro de eventos
    setup_logging(log_dir="logs")

    # Iniciar ciclo de eventos de PySide6
    app = QApplication(sys.argv)
    app.setApplicationName("Sistema de Visión Artificial - Inspección de Láminas")
    app.setOrganizationName("Control de Calidad e Ingeniería")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
