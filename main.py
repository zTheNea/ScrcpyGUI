"""Scrcpy Studio — Entry Point."""
import os
import sys
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from paths import IS_WINDOWS, get_asset_path
from ui.app_window import AppWindow


def main():
    if "--legacy" in sys.argv:
        import importlib
        scrcpy_mod = importlib.import_module("scrcpy_gui")
        app = scrcpy_mod.ScrcpyGUI()
        app.mainloop()
        return

    if IS_WINDOWS:
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ScrcpyStudio.v2.0")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    icon_path = get_asset_path(os.path.join("ui", "assets", "icon.ico"))
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    win = AppWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
