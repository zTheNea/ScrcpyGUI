"""Settings and system diagnostics view for Scrcpy Studio."""
from __future__ import annotations

import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QProgressBar
)

import scrcpy_manager as mgr
import config_manager as cfg
from .theme import C, RADIUS_CARD
from .state import AppState
from .widgets import card, hline
from .services import run_async, restart_adb_server
from .dialogs import AdvancedDialog
from paths import RECORDINGS_DIR


class SettingsPage(QWidget):
    """System configuration, scrcpy binary manager, and global defaults."""

    scrcpy_installed = Signal(str)
    _sig_check_done = Signal(str, str, str)
    _sig_dl_progress = Signal(float)
    _sig_dl_done = Signal(str)

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self._auto_install_after_check = False
        self._pending_update_tag = ""
        self._pending_update_url = ""
        self._downloading_tag = ""
        self._downloading_url = ""
        self._is_downloading = False

        self._sig_check_done.connect(self._on_check_done)
        self._sig_dl_progress.connect(self._on_dl_progress)
        self._sig_dl_done.connect(self._on_dl_done)

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
        self.engine_card = card("cardElevated")
        eng_lay = QVBoxLayout(self.engine_card)
        eng_lay.setContentsMargins(18, 14, 18, 14)
        eng_lay.setSpacing(12)

        lbl_eng = QLabel("MOTOR SCRCPY & ADB")
        lbl_eng.setObjectName("eyebrow")
        eng_lay.addWidget(lbl_eng)

        self.lbl_scrcpy_path = QLabel("Buscando scrcpy...")
        self.lbl_scrcpy_path.setObjectName("sub")
        self.lbl_scrcpy_path.setWordWrap(True)
        eng_lay.addWidget(self.lbl_scrcpy_path)

        self.lbl_scrcpy_ver = QLabel("")
        self.lbl_scrcpy_ver.setObjectName("mono")
        self.lbl_scrcpy_ver.setWordWrap(True)
        eng_lay.addWidget(self.lbl_scrcpy_ver)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_install_scrcpy = QPushButton("⬇️ Instalar Scrcpy Ahora")
        self.btn_install_scrcpy.setObjectName("primary")
        self.btn_install_scrcpy.setCursor(Qt.PointingHandCursor)
        self.btn_install_scrcpy.clicked.connect(self._install_scrcpy_one_click)
        btn_row.addWidget(self.btn_install_scrcpy)

        self.btn_check_update = QPushButton("🔄 Buscar Actualizaciones")
        self.btn_check_update.setCursor(Qt.PointingHandCursor)
        self.btn_check_update.clicked.connect(self._check_scrcpy_updates)
        btn_row.addWidget(self.btn_check_update)

        self.btn_open_folder = QPushButton("📂 Abrir Carpeta Scrcpy")
        self.btn_open_folder.setCursor(Qt.PointingHandCursor)
        self.btn_open_folder.clicked.connect(self._open_scrcpy_folder)
        btn_row.addWidget(self.btn_open_folder)

        self.btn_restart_adb = QPushButton("🔌 Reiniciar Servidor ADB")
        self.btn_restart_adb.setCursor(Qt.PointingHandCursor)
        self.btn_restart_adb.setToolTip("Detiene y vuelve a iniciar el demonio ADB en caso de desconexiones o bloqueos.")
        self.btn_restart_adb.clicked.connect(self._restart_adb)
        btn_row.addWidget(self.btn_restart_adb)

        btn_row.addStretch()
        eng_lay.addLayout(btn_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        eng_lay.addWidget(self.progress_bar)

        self.lbl_update_status = QLabel("")
        self.lbl_update_status.setObjectName("sub")
        self.lbl_update_status.setWordWrap(True)
        eng_lay.addWidget(self.lbl_update_status)

        root.addWidget(self.engine_card)

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
        if self._is_downloading:
            return

        exe = mgr.get_scrcpy_path()
        ver = mgr.get_installed_version()
        adb = mgr._get_adb_path()

        if exe:
            self.engine_card.setStyleSheet("")
            self.lbl_scrcpy_path.setText(f"✅ Ruta ejecutable: {exe}\n🔌 Ruta ADB: {adb or 'Detectado en sistema'}")
            self.lbl_scrcpy_Path_color = C["text2"]
            self.lbl_scrcpy_ver.setText(f"Versión de motor: {ver or 'scrcpy activo'}")
            if self._pending_update_tag:
                self.btn_install_scrcpy.setText(f"⬇️ Instalar Actualización ({self._pending_update_tag})")
                self.btn_install_scrcpy.setObjectName("primary")
                self.btn_check_update.setObjectName("")
            else:
                self.btn_install_scrcpy.setText("⬇️ Reinstalar Scrcpy")
                self.btn_install_scrcpy.setObjectName("")
                self.btn_check_update.setObjectName("primary")
            self.btn_check_update.show()
            self.btn_open_folder.setEnabled(True)
            self.btn_restart_adb.setEnabled(True)
        else:
            self.engine_card.setStyleSheet(
                f"QFrame#cardElevated {{ border: 1px solid {C['warning']}; border-radius: {RADIUS_CARD}px; }}"
            )
            self.lbl_scrcpy_path.setText("⚠️ scrcpy no está instalado en este equipo.")
            self.lbl_scrcpy_ver.setText(
                "Presiona el botón de abajo para descargar e instalar automáticamente scrcpy y ADB en un solo clic."
            )
            self.btn_install_scrcpy.setText("⬇️ Instalar Scrcpy Ahora")
            self.btn_install_scrcpy.setObjectName("primary")
            self.btn_check_update.hide()
            self.btn_open_folder.setEnabled(False)
            self.btn_restart_adb.setEnabled(False)

        for btn in (self.btn_install_scrcpy, self.btn_check_update):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def focus_install_button(self):
        """Highlight and focus the 1-click install button when navigated from missing scrcpy prompt."""
        self.refresh()
        self.btn_install_scrcpy.setFocus()

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
        self.lbl_update_status.setStyleSheet("")
        self.lbl_update_status.setText("Reiniciando servidor ADB...")

        def on_done(ok: bool, msg: str):
            self.btn_restart_adb.setEnabled(True)
            if ok:
                self.lbl_update_status.setText(f"✓ {msg}")
            else:
                self.lbl_update_status.setText(f"⚠️ {msg}")
            self.refresh()

        restart_adb_server(on_done)

    def _install_scrcpy_one_click(self):
        """1-Click install or update scrcpy: fetches latest release if needed, then downloads & extracts."""
        if self._is_downloading:
            return

        if self._pending_update_url and self._pending_update_tag:
            self._start_download(self._pending_update_tag, self._pending_update_url)
            return

        self._auto_install_after_check = True
        self.btn_install_scrcpy.setEnabled(False)
        self.btn_check_update.setEnabled(False)
        self.btn_install_scrcpy.setText("⏳ Preparando instalación...")
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        self.lbl_update_status.setStyleSheet(f"color: {C['cyan_bright']};")
        self.lbl_update_status.setText("🔍 Conectando con el repositorio oficial de scrcpy en GitHub...")

        mgr.check_latest(lambda tag, url, err: self._sig_check_done.emit(tag or "", url or "", err or ""))

    def _check_scrcpy_updates(self):
        if self._is_downloading:
            return
        self._auto_install_after_check = False
        self.lbl_update_status.setStyleSheet("")
        self.lbl_update_status.setText("Comprobando repositorio oficial de scrcpy...")
        self.btn_check_update.setEnabled(False)
        self.btn_install_scrcpy.setEnabled(False)

        mgr.check_latest(lambda tag, url, err: self._sig_check_done.emit(tag or "", url or "", err or ""))

    def _on_check_done(self, tag: str, url: str, err: str):
        auto_install = self._auto_install_after_check
        self._auto_install_after_check = False

        if err:
            self.progress_bar.hide()
            self.btn_check_update.setEnabled(True)
            self.btn_install_scrcpy.setEnabled(True)
            self.lbl_update_status.setStyleSheet(f"color: {C['danger']};")
            self.lbl_update_status.setText(f"❌ No se pudo conectar con GitHub: {err}")
            self.refresh()
            return

        if auto_install:
            if not url:
                self.progress_bar.hide()
                self.btn_check_update.setEnabled(True)
                self.btn_install_scrcpy.setEnabled(True)
                self.lbl_update_status.setStyleSheet(f"color: {C['warning']};")
                self.lbl_update_status.setText(
                    "⚠️ La descarga automática directa solo está disponible para Windows (64-bit)."
                )
                self.refresh()
                return
            self._start_download(tag or "latest", url)
            return

        # Manual check only
        self.btn_check_update.setEnabled(True)
        self.btn_install_scrcpy.setEnabled(True)
        if tag:
            cur = mgr.get_installed_version()
            if tag != cur:
                self._pending_update_tag = tag
                self._pending_update_url = url
                self.lbl_update_status.setStyleSheet(f"color: {C['cyan_bright']}; font-weight: 600;")
                self.lbl_update_status.setText(
                    f"🌟 Nueva versión disponible: {tag} (Actual: {cur or 'desconocida'}). "
                    f"Presiona 'Instalar Actualización' para actualizar con un clic."
                )
            else:
                self._pending_update_tag = ""
                self._pending_update_url = ""
                self.lbl_update_status.setStyleSheet(f"color: {C['success']};")
                self.lbl_update_status.setText(f"✓ Estás al día con la última versión de scrcpy ({cur}).")
        self.refresh()

    def _start_download(self, tag: str, url: str):
        self._is_downloading = True
        self._downloading_tag = tag
        self._downloading_url = url
        self.btn_install_scrcpy.setEnabled(False)
        self.btn_check_update.setEnabled(False)
        self.btn_install_scrcpy.setText(f"⏳ Instalando {tag}...")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.lbl_update_status.setStyleSheet(f"color: {C['cyan_bright']};")
        self.lbl_update_status.setText(f"⬇️ Descargando scrcpy {tag}... 0%")

        mgr.download_and_install(
            url,
            progress_cb=lambda r: self._sig_dl_progress.emit(float(r)),
            done_cb=lambda e: self._sig_dl_done.emit(e or ""),
        )

    def _on_dl_progress(self, ratio: float):
        if ratio < 0:
            self.progress_bar.setRange(0, 0)
            self.lbl_update_status.setText(
                f"📦 Extrayendo e instalando scrcpy {self._downloading_tag} y ADB..."
            )
        else:
            pct = max(0, min(100, int(ratio * 100)))
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(pct)
            self.lbl_update_status.setText(f"⬇️ Descargando scrcpy {self._downloading_tag}... {pct}%")

    def _on_dl_done(self, err: str):
        self._is_downloading = False
        self.progress_bar.hide()
        self.btn_install_scrcpy.setEnabled(True)
        self.btn_check_update.setEnabled(True)

        if err:
            self.lbl_update_status.setStyleSheet(f"color: {C['danger']};")
            self.lbl_update_status.setText(f"❌ Error al instalar scrcpy: {err}")
            self.refresh()
            return

        tag = self._downloading_tag or "latest"
        mgr._save_version(tag, self._downloading_url)
        self._pending_update_tag = ""
        self._pending_update_url = ""
        self.lbl_update_status.setStyleSheet(f"color: {C['success']}; font-weight: 600;")
        self.lbl_update_status.setText(f"✅ ¡Scrcpy {tag} y ADB instalados correctamente! El programa ya está listo.")
        self.refresh()
        self.scrcpy_installed.emit(tag)

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

