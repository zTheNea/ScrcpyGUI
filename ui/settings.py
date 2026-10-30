"""Settings and system diagnostics view for Scrcpy Studio."""
from __future__ import annotations

import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox
)

import scrcpy_manager as mgr
import config_manager as cfg
from .theme import C
from .state import AppState
from .widgets import card, hline
from .services import run_async, restart_adb_server
from .dialogs import AdvancedDialog
from paths import RECORDINGS_DIR


class SettingsPage(QWidget):
    """System configuration, scrcpy binary manager, and global defaults."""

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
        lbl_h1 = QLabel("Ajustes del Sistema")
        lbl_h1.setObjectName("h1")
        lbl_sub = QLabel("Estado del motor scrcpy, dependencias ADB y preferencias globales.")
        lbl_sub.setObjectName("sub")
        title_box.addWidget(lbl_h1)
        title_box.addWidget(lbl_sub)
        head.addLayout(title_box, 1)
        root.addLayout(head)

        # Engine Card
        engine_card = card("cardElevated")
        eng_lay = QVBoxLayout(engine_card)
        eng_lay.setContentsMargins(18, 14, 18, 14)
        eng_lay.setSpacing(12)

        lbl_eng = QLabel("MOTOR SCRCPY & ADB")
        lbl_eng.setObjectName("eyebrow")
        eng_lay.addWidget(lbl_eng)

        self.lbl_scrcpy_path = QLabel("Buscando scrcpy...")
        self.lbl_scrcpy_path.setObjectName("sub")
        eng_lay.addWidget(self.lbl_scrcpy_path)

        self.lbl_scrcpy_ver = QLabel("")
        self.lbl_scrcpy_ver.setObjectName("mono")
        eng_lay.addWidget(self.lbl_scrcpy_ver)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_check_update = QPushButton("🔄 Buscar Actualizaciones")
        self.btn_check_update.setObjectName("primary")
        self.btn_check_update.setCursor(Qt.PointingHandCursor)
        self.btn_check_update.clicked.connect(self._check_scrcpy_updates)
        btn_row.addWidget(self.btn_check_update)

        btn_open_folder = QPushButton("📂 Abrir Carpeta Scrcpy")
        btn_open_folder.setCursor(Qt.PointingHandCursor)
        btn_open_folder.clicked.connect(self._open_scrcpy_folder)
        btn_row.addWidget(btn_open_folder)

        self.btn_restart_adb = QPushButton("🔌 Reiniciar Servidor ADB")
        self.btn_restart_adb.setCursor(Qt.PointingHandCursor)
        self.btn_restart_adb.setToolTip("Detiene y vuelve a iniciar el demonio ADB en caso de desconexiones o bloqueos.")
        self.btn_restart_adb.clicked.connect(self._restart_adb)
        btn_row.addWidget(self.btn_restart_adb)

        btn_row.addStretch()
        eng_lay.addLayout(btn_row)

        self.lbl_update_status = QLabel("")
        self.lbl_update_status.setObjectName("sub")
        eng_lay.addWidget(self.lbl_update_status)

        root.addWidget(engine_card)

        # Advanced Parameters Card
        adv_card = card("cardElevated")
        adv_lay = QVBoxLayout(adv_card)
        adv_lay.setContentsMargins(18, 14, 18, 14)
        adv_lay.setSpacing(12)

        lbl_adv_title = QLabel("PARÁMETROS AVANZADOS DEL MOTOR")
        lbl_adv_title.setObjectName("eyebrow")
        adv_lay.addWidget(lbl_adv_title)

        lbl_adv_desc = QLabel(
            "Accede al catálogo completo con más de 50 banderas y opciones nativas de scrcpy: "
            "aceleración por GPU (D3D11VA), códecs H.265/AV1, audio de baja latencia, "
            "control UHID/AOA, recortes, orientación y pantalla virtual."
        )
        lbl_adv_desc.setObjectName("sub")
        lbl_adv_desc.setWordWrap(True)
        adv_lay.addWidget(lbl_adv_desc)

        adv_btn_row = QHBoxLayout()
        adv_btn_row.setSpacing(10)

        btn_open_adv = QPushButton("⚡ Abrir Editor Avanzado de Parámetros")
        btn_open_adv.setObjectName("primary")
        btn_open_adv.setCursor(Qt.PointingHandCursor)
        btn_open_adv.clicked.connect(self._open_advanced_dialog)
        adv_btn_row.addWidget(btn_open_adv)

        btn_open_recordings = QPushButton("🎬 Carpeta de Grabaciones")
        btn_open_recordings.setCursor(Qt.PointingHandCursor)
        btn_open_recordings.clicked.connect(self._open_recordings_folder)
        adv_btn_row.addWidget(btn_open_recordings)

        adv_btn_row.addStretch()
        adv_lay.addLayout(adv_btn_row)

        root.addWidget(adv_card)

        # Defaults & Maintenance Card
        maint_card = card("card")
        maint_lay = QVBoxLayout(maint_card)
        maint_lay.setContentsMargins(18, 14, 18, 14)
        maint_lay.setSpacing(12)

        lbl_maint = QLabel("MANTENIMIENTO Y RESTABLECIMIENTO")
        lbl_maint.setObjectName("eyebrow")
        maint_lay.addWidget(lbl_maint)

        lbl_maint_desc = QLabel("Si experimentas problemas con parámetros modificados, puedes restablecer todo al estado inicial recomendado.")
        lbl_maint_desc.setObjectName("sub")
        lbl_maint_desc.setWordWrap(True)
        maint_lay.addWidget(lbl_maint_desc)

        btn_reset = QPushButton("↺ Restablecer Todo a Valores por Defecto")
        btn_reset.setObjectName("danger")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self._reset_defaults)
        maint_lay.addWidget(btn_reset, 0, Qt.AlignLeft)

        root.addWidget(maint_card)

        # About Card
        about_card = card("card")
        abt_lay = QVBoxLayout(about_card)
        abt_lay.setContentsMargins(18, 14, 18, 14)
        abt_lay.setSpacing(6)

        lbl_abt_t = QLabel("Scrcpy Studio 2026")
        lbl_abt_t.setStyleSheet("font-weight: bold; font-size: 14px;")
        abt_lay.addWidget(lbl_abt_t)

        lbl_abt_desc = QLabel(
            "Diseñado y desarrollado con PySide6 y sistema de diseño UI/UX Pro Max.\n"
            "Basado en el motor de duplicación de alta fidelidad scrcpy por Genymobile."
        )
        lbl_abt_desc.setObjectName("muted")
        abt_lay.addWidget(lbl_abt_desc)

        root.addWidget(about_card)
        root.addStretch()

    def refresh(self):
        exe = mgr.get_scrcpy_path()
        ver = mgr.get_installed_version()
        adb = mgr._get_adb_path()

        if exe:
            self.lbl_scrcpy_path.setText(f"Ruta ejecutable: {exe}\nRuta ADB: {adb or 'Detectado en sistema'}")
            self.lbl_scrcpy_ver.setText(f"Versión de motor: {ver or 'scrcpy activo'}")
        else:
            self.lbl_scrcpy_path.setText("❌ scrcpy no está instalado o no se encuentra en la ruta.")
            self.lbl_scrcpy_ver.setText("")

    def _open_scrcpy_folder(self):
        exe = mgr.get_scrcpy_path()
        if exe and os.path.exists(exe):
            d = os.path.dirname(exe)
            os.startfile(d) if hasattr(os, "startfile") else None

    def _open_recordings_folder(self):
        os.makedirs(RECORDINGS_DIR, exist_ok=True)
        os.startfile(RECORDINGS_DIR) if hasattr(os, "startfile") else None

    def _open_advanced_dialog(self):
        dlg = AdvancedDialog(self.state, self)
        dlg.exec()

    def _restart_adb(self):
        self.btn_restart_adb.setEnabled(False)
        self.lbl_update_status.setText("Reiniciando servidor ADB...")

        def on_done(ok: bool, msg: str):
            self.btn_restart_adb.setEnabled(True)
            if ok:
                self.lbl_update_status.setText(f"✓ {msg}")
            else:
                self.lbl_update_status.setText(f"⚠️ {msg}")
            self.refresh()

        restart_adb_server(on_done)

    def _check_scrcpy_updates(self):
        self.lbl_update_status.setText("Comprobando repositorio oficial de scrcpy...")
        self.btn_check_update.setEnabled(False)

        def cb(tag, url, err):
            self.btn_check_update.setEnabled(True)
            if err:
                self.lbl_update_status.setText(f"No se pudo comprobar actualización: {err}")
            elif tag:
                cur = mgr.get_installed_version()
                if tag != cur:
                    self.lbl_update_status.setText(f"🌟 Nueva versión disponible: {tag}. (Actual: {cur or 'desconocida'})")
                else:
                    self.lbl_update_status.setText(f"✓ Estás al día con la última versión de scrcpy ({cur}).")

        mgr.check_latest(cb)

    def _reset_defaults(self):
        reply = QMessageBox.question(
            self,
            "Restablecer Valores",
            "¿Deseas restaurar todas las opciones a la configuración recomendada de fábrica?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.state.reset()
            self.refresh()

