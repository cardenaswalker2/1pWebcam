"""
Punto de Entrada — Inspección Óptica de Tejas y Polímeros Translúcidos.
"""

import sys
import os

# Ajustar PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PySide6.QtWidgets import QApplication
from demo_transparentes.main_window import TransparentInspectionWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Sistema de Inspección Óptica — Polímeros Translúcidos")
    app.setOrganizationName("Control de Calidad e Ingeniería")

    window = TransparentInspectionWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
