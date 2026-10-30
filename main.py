"""Scrcpy Studio — Entry Point."""
import sys
from PySide6.QtWidgets import QApplication
from ui.app_window import AppWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = AppWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
