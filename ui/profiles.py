"""Profiles and session history view for Scrcpy Studio."""
from __future__ import annotations

import json
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QFileDialog, QMessageBox, QApplication
)

import config_manager as cfg
import history_manager as hist
from .theme import C
from .state import AppState
from .widgets import card, hline
from .dialogs import PromptDialog

GOAL_INFO = {
    "gaming": ("🎮", "Gaming 120 FPS", C["cyan"]),
    "desktop": ("🖥️", "Escritorio / DeX", C["indigo"]),
    "camera": ("📷", "Cámara / Webcam", C["amber"]),
    "record": ("⏺️", "Grabación", C["red"]),
    "app": ("🪟", "App en Ventana", C["purple"]),
    "mirror": ("📱", "Espejo", C["emerald"]),
}


class ProfilesPage(QWidget):
    """Save/load custom presets, export/import JSON, and review execution history."""

    profile_loaded = Signal(str)

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
        lbl_h1 = QLabel("Perfiles e Historial")
        lbl_h1.setObjectName("h1")
        lbl_sub = QLabel("Guarda tus configuraciones favoritas, expórtalas a JSON y revisa las sesiones pasadas.")
        lbl_sub.setObjectName("sub")
        title_box.addWidget(lbl_h1)
        title_box.addWidget(lbl_sub)
        head.addLayout(title_box, 1)

        btn_import = QPushButton("📥 Importar Perfil")
        btn_import.setCursor(Qt.PointingHandCursor)
        btn_import.clicked.connect(self._import_profile)
        head.addWidget(btn_import)

        btn_save = QPushButton("💾 Guardar Configuración Actual")
        btn_save.setObjectName("primary")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self._save_current_profile)
        head.addWidget(btn_save)
        root.addLayout(head)

        body = QHBoxLayout()
        body.setSpacing(16)

        # Left: Profiles List
        prof_card = card("card")
        prof_lay = QVBoxLayout(prof_card)
        prof_lay.setContentsMargins(16, 14, 16, 14)
        prof_lay.setSpacing(10)

        lbl_prof = QLabel("MIS PERFILES GUARDADOS")
        lbl_prof.setObjectName("eyebrow")
        prof_lay.addWidget(lbl_prof)

        self.prof_scroll = QScrollArea()
        self.prof_scroll.setWidgetResizable(True)
        self.prof_container = QWidget()
        self.prof_list_lay = QVBoxLayout(self.prof_container)
        self.prof_list_lay.setContentsMargins(0, 4, 4, 4)
        self.prof_list_lay.setSpacing(8)
        self.prof_scroll.setWidget(self.prof_container)
        prof_lay.addWidget(self.prof_scroll, 1)

        body.addWidget(prof_card, 2)

        # Right: Session History
        hist_card = card("cardElevated")
        hist_lay = QVBoxLayout(hist_card)
        hist_lay.setContentsMargins(16, 14, 16, 14)
        hist_lay.setSpacing(10)

        hist_head = QHBoxLayout()
        lbl_hist = QLabel("HISTORIAL DE SESIONES")
        lbl_hist.setObjectName("eyebrow")
        hist_head.addWidget(lbl_hist)
        hist_head.addStretch()

        btn_clear_hist = QPushButton("Limpiar")
        btn_clear_hist.setObjectName("ghost")
        btn_clear_hist.clicked.connect(self._clear_history)
        hist_head.addWidget(btn_clear_hist)
        hist_lay.addLayout(hist_head)

        self.hist_scroll = QScrollArea()
        self.hist_scroll.setWidgetResizable(True)
        self.hist_container = QWidget()
        self.hist_list_lay = QVBoxLayout(self.hist_container)
        self.hist_list_lay.setContentsMargins(0, 4, 4, 4)
        self.hist_list_lay.setSpacing(8)
        self.hist_scroll.setWidget(self.hist_container)
        hist_lay.addWidget(self.hist_scroll, 1)

        body.addWidget(hist_card, 3)
        root.addLayout(body, 1)

    def refresh(self):
        self._refresh_profiles()
        self._refresh_history()

    def _refresh_profiles(self):
        self._clear_layout(self.prof_list_lay)
        profiles = cfg.list_profiles()
        if not profiles:
            lbl = QLabel("No has guardado perfiles personalizados aún.\nGuarda tu configuración actual para usarla en cualquier momento.")
            lbl.setObjectName("sub")
            lbl.setWordWrap(True)
            self.prof_list_lay.addWidget(lbl)
            return

        for p in profiles:
            data = cfg.get_profile_data(p)
            goal_key = data.get("_goal", "mirror")
            icon, goal_title, color = GOAL_INFO.get(goal_key, ("⚙️", "Personalizado", C["textMuted"]))

            p_card = card("cardElevated")
            p_lay = QVBoxLayout(p_card)
            p_lay.setContentsMargins(14, 10, 14, 10)
            p_lay.setSpacing(6)

            # Top Row: Title + Action buttons
            top = QHBoxLayout()
            top.setSpacing(8)

            lbl_name = QLabel(p)
            lbl_name.setStyleSheet("font-weight: 600; font-size: 14px;")
            top.addWidget(lbl_name, 1)

            btn_export = QPushButton("📤 Exportar")
            btn_export.setObjectName("ghost")
            btn_export.setCursor(Qt.PointingHandCursor)
            btn_export.setToolTip(f"Exportar perfil '{p}' a un archivo JSON")
            btn_export.clicked.connect(lambda _, name=p: self._export_profile(name))
            top.addWidget(btn_export)

            btn_load = QPushButton("Cargar")
            btn_load.setObjectName("primary")
            btn_load.setCursor(Qt.PointingHandCursor)
            btn_load.clicked.connect(lambda _, name=p: self._load_profile(name))
            top.addWidget(btn_load)

            btn_del = QPushButton("🗑️")
            btn_del.setObjectName("ghost")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setToolTip(f"Eliminar perfil '{p}'")
            btn_del.clicked.connect(lambda _, name=p: self._delete_profile(name))
            top.addWidget(btn_del)
            p_lay.addLayout(top)

            # Bottom Row: Chips (Goal + Key Settings)
            bot = QHBoxLayout()
            bot.setSpacing(8)

            lbl_goal_chip = QLabel(f"{icon} {goal_title}")
            lbl_goal_chip.setStyleSheet(
                f"border: 1px solid {color}44; background: {color}18; color: {color}; "
                f"font-size: 11px; font-weight: bold; border-radius: 4px; padding: 2px 6px;"
            )
            bot.addWidget(lbl_goal_chip)

            fps = data.get("fps", 60)
            br = data.get("bitrate", 8)
            codec = str(data.get("codec", "h264")).upper()
            kb = data.get("keyboard", "")
            control_str = "UHID" if kb == "uhid" else "SDK"

            lbl_specs = QLabel(f"{fps} FPS • {br} Mbps • {codec} • {control_str}")
            lbl_specs.setObjectName("muted")
            lbl_specs.setStyleSheet("font-size: 11px;")
            bot.addWidget(lbl_specs)

            bot.addStretch()
            p_lay.addLayout(bot)

            self.prof_list_lay.addWidget(p_card)

        self.prof_list_lay.addStretch()

    def _refresh_history(self):
        self._clear_layout(self.hist_list_lay)
        try:
            records = hist.get_history(limit=25)
        except Exception:
            records = []

        if not records:
            lbl = QLabel("El historial de ejecuciones está vacío.")
            lbl.setObjectName("sub")
            self.hist_list_lay.addWidget(lbl)
            return

        for r in records:
            r_card = card("card")
            r_lay = QVBoxLayout(r_card)
            r_lay.setContentsMargins(12, 8, 12, 8)
            r_lay.setSpacing(4)

            top = QHBoxLayout()
            lbl_t = QLabel(r.get("timestamp", ""))
            lbl_t.setObjectName("muted")
            top.addWidget(lbl_t)

            lbl_mode = QLabel(f"Objetivo: {r.get('preset', 'personalizado')}")
            lbl_mode.setStyleSheet(f"font-weight: bold; color: {C['cyan']};")
            top.addWidget(lbl_mode)
            top.addStretch()

            lbl_st = QLabel("✓ Éxito" if r.get("success") else "❌ Fallo")
            lbl_st.setStyleSheet(f"color: {C['success'] if r.get('success') else C['danger']}; font-weight: bold;")
            top.addWidget(lbl_st)
            r_lay.addLayout(top)

            cmd_row = QHBoxLayout()
            cmd_row.setSpacing(6)

            lbl_cmd = QLabel(r.get("command", ""))
            lbl_cmd.setObjectName("mono")
            lbl_cmd.setTextInteractionFlags(Qt.TextSelectableByMouse)
            cmd_row.addWidget(lbl_cmd, 1)

            btn_cp = QPushButton("📋")
            btn_cp.setObjectName("ghost")
            btn_cp.setFixedSize(26, 24)
            btn_cp.setCursor(Qt.PointingHandCursor)
            btn_cp.setToolTip("Copiar comando al portapapeles")
            btn_cp.clicked.connect(lambda _, c=r.get("command", ""): self._copy_text(c))
            cmd_row.addWidget(btn_cp)

            r_lay.addLayout(cmd_row)
            self.hist_list_lay.addWidget(r_card)

        self.hist_list_lay.addStretch()

    def _copy_text(self, text: str):
        if text:
            QApplication.clipboard().setText(text)
            main_win = self.window()
            if hasattr(main_win, "toast"):
                main_win.toast.show_message("Comando copiado al portapapeles", kind="ok")

    def _save_current_profile(self):
        dlg = PromptDialog("Guardar Perfil", "Ingresa un nombre para recordar esta configuración:", "ej. Mi Setup Gaming", parent=self)
        if dlg.exec():
            name = dlg.get_value()
            if name:
                cfg.save_profile(self.state, name)
                self.refresh()
                main_win = self.window()
                if hasattr(main_win, "toast"):
                    main_win.toast.show_message(f"Perfil '{name}' guardado con éxito.", kind="ok")

    def _load_profile(self, name: str):
        ok = cfg.load_profile(self.state, name)
        if ok:
            self.profile_loaded.emit(name)

    def _export_profile(self, name: str):
        data = cfg.get_profile_data(name)
        if not data:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Exportar Perfil — {name}",
            f"{name}.json",
            "Archivos JSON (*.json)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                main_win = self.window()
                if hasattr(main_win, "toast"):
                    main_win.toast.show_message(f"Perfil '{name}' exportado correctamente.", kind="ok")
            except Exception as e:
                QMessageBox.warning(self, "Error al Exportar", f"No se pudo guardar el archivo: {e}")

    def _import_profile(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar Perfil desde JSON",
            "",
            "Archivos JSON (*.json)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("El archivo JSON debe contener un objeto de configuración.")

            # Suggest name from filename
            import os
            base_name = os.path.splitext(os.path.basename(path))[0]
            dlg = PromptDialog("Nombre del Perfil Importado", "Confirma el nombre para guardar este perfil:", "", base_name, parent=self)
            if dlg.exec():
                prof_name = dlg.get_value()
                if prof_name:
                    profiles = cfg._read_profiles()
                    profiles[prof_name] = data
                    cfg._write_profiles(profiles)
                    self.refresh()
                    main_win = self.window()
                    if hasattr(main_win, "toast"):
                        main_win.toast.show_message(f"Perfil '{prof_name}' importado con éxito.", kind="ok")
        except Exception as e:
            QMessageBox.warning(self, "Error al Importar", f"No se pudo leer el archivo de perfil: {e}")

    def _delete_profile(self, name: str):
        # Safe confirmation guard (accidental-data-loss-prevention)
        reply = QMessageBox.question(
            self,
            "Eliminar Perfil",
            f"¿Estás seguro de que deseas eliminar permanentemente el perfil '{name}'?\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            cfg.delete_profile(name)
            self.refresh()
            main_win = self.window()
            if hasattr(main_win, "toast"):
                main_win.toast.show_message(f"Perfil '{name}' eliminado.", kind="warn")

    def _clear_history(self):
        reply = QMessageBox.question(
            self,
            "Limpiar Historial",
            "¿Deseas vaciar todo el registro de ejecuciones pasadas?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                hist.clear_history()
            except Exception:
                pass
            self.refresh()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

