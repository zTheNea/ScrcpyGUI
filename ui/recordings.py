"""Recordings manager view for Scrcpy Studio."""
from __future__ import annotations

import os
import subprocess
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QFileDialog, QComboBox
)

from .theme import C
from .state import AppState
from .widgets import card, hline


class RecordingsPage(QWidget):
    """Manage screen recordings, destination folders, and recorded clips."""

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        # Header
        head = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_h1 = QLabel("Grabaciones de Pantalla")
        lbl_h1.setObjectName("h1")
        lbl_sub = QLabel("Configura la carpeta de destino y reproduce tus capturas de video.")
        lbl_sub.setObjectName("sub")
        title_box.addWidget(lbl_h1)
        title_box.addWidget(lbl_sub)
        head.addLayout(title_box, 1)

        btn_open = QPushButton("📂 Abrir en Explorador")
        btn_open.setObjectName("primary")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.clicked.connect(self._open_folder_explorer)
        head.addWidget(btn_open)
        root.addLayout(head)

        # Settings Card
        cfg_card = card("cardElevated")
        cfg_lay = QHBoxLayout(cfg_card)
        cfg_lay.setContentsMargins(16, 12, 16, 12)
        cfg_lay.setSpacing(14)

        lbl_dest = QLabel("Carpeta de guardado:")
        lbl_dest.setObjectName("sub")
        cfg_lay.addWidget(lbl_dest)

        self.lbl_path = QLabel(self._get_recordings_dir())
        self.lbl_path.setObjectName("mono")
        self.lbl_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        cfg_lay.addWidget(self.lbl_path, 1)

        btn_change = QPushButton("Cambiar...")
        btn_change.setCursor(Qt.PointingHandCursor)
        btn_change.clicked.connect(self._pick_folder)
        cfg_lay.addWidget(btn_change)

        root.addWidget(cfg_card)

        # List Card
        list_card = card("card")
        list_lay = QVBoxLayout(list_card)
        list_lay.setContentsMargins(16, 14, 16, 14)
        list_lay.setSpacing(10)

        lbl_rec = QLabel("ARCHIVOS GRABADOS RECIENTES")
        lbl_rec.setObjectName("eyebrow")
        list_lay.addWidget(lbl_rec)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.files_lay = QVBoxLayout(self.container)
        self.files_lay.setContentsMargins(0, 4, 4, 4)
        self.files_lay.setSpacing(8)
        self.scroll.setWidget(self.container)
        list_lay.addWidget(self.scroll, 1)

        root.addWidget(list_card, 1)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()

    def _get_recordings_dir(self) -> str:
        from paths import ensure_recordings_dir
        rec_file = self.state.get("record_file")
        if rec_file and os.path.isabs(str(rec_file)):
            d = os.path.dirname(str(rec_file))
            if os.path.isdir(d):
                return d
        return ensure_recordings_dir()

    def refresh(self):
        self._clear_layout(self.files_lay)
        folder = self._get_recordings_dir()
        self.lbl_path.setText(folder)

        if not os.path.isdir(folder):
            lbl = QLabel("La carpeta de grabaciones no existe.")
            lbl.setObjectName("sub")
            self.files_lay.addWidget(lbl)
            return

        videos = []
        for f in os.listdir(folder):
            if f.lower().endswith((".mp4", ".mkv", ".opus", ".aac")):
                p = os.path.join(folder, f)
                videos.append((p, os.path.getmtime(p), os.path.getsize(p)))

        videos.sort(key=lambda x: x[1], reverse=True)
        if not videos:
            lbl = QLabel("No hay grabaciones de video en esta carpeta aún.")
            lbl.setObjectName("sub")
            self.files_lay.addWidget(lbl)
            return

        for path, mtime, size in videos:
            f_card = card("cardElevated")
            f_lay = QHBoxLayout(f_card)
            f_lay.setContentsMargins(14, 10, 14, 10)
            f_lay.setSpacing(12)

            is_audio = path.lower().endswith((".opus", ".aac", ".m4a"))
            icon = QLabel("🎵" if is_audio else "🎬")
            icon.setStyleSheet("font-size: 22px;")
            f_lay.addWidget(icon)

            info = QVBoxLayout()
            info.setSpacing(2)
            fname = os.path.basename(path)
            lbl_name = QLabel(fname)
            lbl_name.setStyleSheet("font-weight: 600; font-size: 13px;")
            info.addWidget(lbl_name)

            dt_str = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
            mb = size / (1024 * 1024)
            lbl_sub = QLabel(f"{dt_str}  ·  {mb:.1f} MB")
            lbl_sub.setObjectName("sub")
            info.addWidget(lbl_sub)
            f_lay.addLayout(info, 1)

            # Actions Row
            btn_play = QPushButton("▶ Reproducir")
            btn_play.setObjectName("primary")
            btn_play.setCursor(Qt.PointingHandCursor)
            btn_play.clicked.connect(lambda _, p=path: self._open_file(p))
            f_lay.addWidget(btn_play)

            btn_reveal = QPushButton("📂 Mostrar")
            btn_reveal.setObjectName("ghost")
            btn_reveal.setToolTip("Mostrar y seleccionar este archivo en el Explorador de Windows")
            btn_reveal.setCursor(Qt.PointingHandCursor)
            btn_reveal.clicked.connect(lambda _, p=path: self._reveal_in_explorer(p))
            f_lay.addWidget(btn_reveal)

            btn_copy = QPushButton("📋")
            btn_copy.setObjectName("ghost")
            btn_copy.setToolTip("Copiar ruta completa al portapapeles")
            btn_copy.setCursor(Qt.PointingHandCursor)
            btn_copy.clicked.connect(lambda _, p=path: self._copy_path(p))
            f_lay.addWidget(btn_copy)

            btn_del = QPushButton("🗑️")
            btn_del.setObjectName("danger")
            btn_del.setToolTip("Eliminar grabación")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.clicked.connect(lambda _, p=path, n=fname: self._safe_delete(p, n))
            f_lay.addWidget(btn_del)

            self.files_lay.addWidget(f_card)

        self.files_lay.addStretch()

    def _copy_path(self, path: str):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(path)
        main_win = self.window()
        if hasattr(main_win, "toast"):
            main_win.toast.show_message("Ruta copiada al portapapeles", kind="ok")

    def _reveal_in_explorer(self, path: str):
        if not os.path.exists(path):
            return
        norm = os.path.normpath(path)
        if hasattr(os, "startfile"):
            subprocess.run(["explorer", f"/select,{norm}"])
        else:
            subprocess.run(["xdg-open", os.path.dirname(norm)])

    def _safe_delete(self, path: str, filename: str):
        from PySide6.QtWidgets import QMessageBox
        res = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar permanentemente esta grabación?\n\nArchivo: {filename}\n\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if res == QMessageBox.Yes:
            try:
                os.remove(path)
                main_win = self.window()
                if hasattr(main_win, "toast"):
                    main_win.toast.show_message(f"Grabación '{filename}' eliminada", kind="warn")
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el archivo:\n{exc}")

    def _pick_folder(self):
        cur = self._get_recordings_dir()
        d = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de grabaciones", cur)
        if d:
            new_file = os.path.join(d, "captura_%Y%m%d_%H%M%S.mp4")
            self.state.set("record_file", new_file)
            self.refresh()

    def _open_folder_explorer(self):
        d = self._get_recordings_dir()
        if os.path.exists(d):
            os.startfile(d) if hasattr(os, "startfile") else subprocess.run(["xdg-open", d])

    def _open_file(self, path: str):
        if os.path.exists(path):
            os.startfile(path) if hasattr(os, "startfile") else subprocess.run(["xdg-open", path])

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
