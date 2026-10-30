"""Master window for Scrcpy Studio: Navigation Rail, Pages Stack, and Console Drawer."""
from __future__ import annotations

from typing import Optional
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QFrame, QPushButton, QLabel, QPlainTextEdit, QSplitter, QApplication
)

import config_manager as cfg
from .theme import C, stylesheet
from .state import AppState
from .services import SessionManager
from .nav import RailButton
from .widgets import Toast, card
from .home import HomePage
from .devices import DevicesPage
from .profiles import ProfilesPage
from .recordings import RecordingsPage
from .settings import SettingsPage


class AppWindow(QMainWindow):
    """Main application shell for Scrcpy Studio."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scrcpy Studio v2.0.0 — Centro de Control Móvil")
        self.resize(1180, 760)
        self.setMinimumSize(960, 620)
        self.setObjectName("root")

        # Core State & Services
        self.state = AppState()
        self.session_mgr = SessionManager()

        # Load persisted settings if any
        try:
            cfg.load_config(self.state)
        except Exception:
            pass

        self._build_ui()
        self._wire_signals()
        self._setup_shortcuts()

        # Apply global theme stylesheet
        self.setStyleSheet(stylesheet())

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("root")
        self.setCentralWidget(central)

        main_lay = QHBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── 1. Left Navigation Rail ─────────────────────────────────
        rail = QFrame()
        rail.setObjectName("rail")
        rail.setFixedWidth(76)
        rail_lay = QVBoxLayout(rail)
        rail_lay.setContentsMargins(0, 14, 0, 14)
        rail_lay.setSpacing(6)

        # Logo Icon
        lbl_logo = QLabel("⚡")
        lbl_logo.setStyleSheet(f"font-size: 24px; color: {C['cyan']}; background: transparent; padding-bottom: 6px;")
        lbl_logo.setAlignment(Qt.AlignCenter)
        rail_lay.addWidget(lbl_logo)

        # Navigation Buttons
        self.btn_nav_home = RailButton("🚀", "Inicio")
        self.btn_nav_devices = RailButton("📶", "Dispositivos")
        self.btn_nav_profiles = RailButton("💾", "Perfiles")
        self.btn_nav_recordings = RailButton("🎬", "Grabaciones")
        self.btn_nav_settings = RailButton("⚙️", "Ajustes")

        self.nav_buttons = [
            self.btn_nav_home,
            self.btn_nav_devices,
            self.btn_nav_profiles,
            self.btn_nav_recordings,
            self.btn_nav_settings,
        ]

        for idx, btn in enumerate(self.nav_buttons):
            btn.clicked.connect(lambda _, i=idx: self.navigate_to(i))
            rail_lay.addWidget(btn)

        rail_lay.addStretch(1)

        # Device connection status indicator
        self.lbl_device_dot = QLabel("●")
        self.lbl_device_dot.setStyleSheet(f"font-size: 16px; color: {C['muted']};")
        self.lbl_device_dot.setAlignment(Qt.AlignCenter)
        self.lbl_device_dot.setToolTip("Estado del dispositivo")
        rail_lay.addWidget(self.lbl_device_dot)

        main_lay.addWidget(rail)

        # ── 2. Content + Console Splitter ────────────────────────────
        content_box = QWidget()
        content_lay = QVBoxLayout(content_box)
        content_lay.setContentsMargins(0, 0, 0, 0)
        content_lay.setSpacing(0)

        # Pages Stack
        self.stack = QStackedWidget()
        self.page_home = HomePage(self.state, self.session_mgr, self)
        self.page_devices = DevicesPage(self.state, self)
        self.page_profiles = ProfilesPage(self.state, self)
        self.page_recordings = RecordingsPage(self.state, self)
        self.page_settings = SettingsPage(self.state, self)

        self.stack.addWidget(self.page_home)
        self.stack.addWidget(self.page_devices)
        self.stack.addWidget(self.page_profiles)
        self.stack.addWidget(self.page_recordings)
        self.stack.addWidget(self.page_settings)

        content_lay.addWidget(self.stack, 1)

        # ── 3. Bottom Expandable Console Drawer ──────────────────────
        self.console_drawer = card("console")
        console_lay = QVBoxLayout(self.console_drawer)
        console_lay.setContentsMargins(16, 6, 16, 8)
        console_lay.setSpacing(6)

        # Console Header Bar
        console_bar = QHBoxLayout()
        console_bar.setSpacing(10)

        self.btn_toggle_console = QPushButton("▲ Consola de registros")
        self.btn_toggle_console.setObjectName("ghost")
        self.btn_toggle_console.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_console.clicked.connect(self._toggle_console)
        console_bar.addWidget(self.btn_toggle_console)

        self.lbl_console_hint = QLabel("Registros en tiempo real de scrcpy")
        self.lbl_console_hint.setObjectName("muted")
        console_bar.addWidget(self.lbl_console_hint)

        console_bar.addStretch()

        self.btn_copy_logs = QPushButton("Copiar")
        self.btn_copy_logs.setObjectName("ghost")
        self.btn_copy_logs.setCursor(Qt.PointingHandCursor)
        self.btn_copy_logs.clicked.connect(self._copy_logs)
        self.btn_copy_logs.hide()
        console_bar.addWidget(self.btn_copy_logs)

        self.btn_clear_logs = QPushButton("Limpiar")
        self.btn_clear_logs.setObjectName("ghost")
        self.btn_clear_logs.setCursor(Qt.PointingHandCursor)
        self.btn_clear_logs.clicked.connect(self._clear_logs)
        self.btn_clear_logs.hide()
        console_bar.addWidget(self.btn_clear_logs)

        console_lay.addLayout(console_bar)

        # Console Text Output
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(160)
        self.log_text.hide()
        console_lay.addWidget(self.log_text)

        content_lay.addWidget(self.console_drawer)
        main_lay.addWidget(content_box, 1)

        # Global Toast Container
        self.toast = Toast(self)

        # Select first nav item
        self.btn_nav_home.setChecked(True)

    def _wire_signals(self):
        # Home signals
        self.page_home.launch_requested.connect(self._start_mirror)
        self.page_home.stop_all_requested.connect(self.session_mgr.stop_all)
        self.page_home.open_devices_tab.connect(lambda: self.navigate_to(1))
        self.page_home.wifi_auto_connected.connect(
            lambda msg, ip: self.toast.show_message(f"🎉 {msg}. ¡Ya puedes desconectar el cable USB!", kind="ok", ms=6000)
        )
        self.page_home.wifi_auto_failed.connect(
            lambda err: self.toast.show_message(f"⚠️ Wi-Fi Auto: {err}", kind="warn", ms=5000)
        )

        # Devices signals
        self.page_devices.device_selected.connect(self._on_device_selected_from_tab)

        # Profiles signals
        self.page_profiles.profile_loaded.connect(self._on_profile_loaded)

        # Session Manager signals
        self.session_mgr.log.connect(self._append_log)
        self.session_mgr.started.connect(lambda t: self.toast.show_message(f"🚀 Sesión iniciada: {t}", kind="ok"))
        self.session_mgr.failed.connect(self._on_session_failed)
        self.session_mgr.recorded.connect(self._on_recorded)

        # State subscription for device indicator
        self.state.subscribe(self._on_state_change)

    def _on_recorded(self, sid: str, path: str):
        fn = os.path.basename(path)
        try:
            mb = os.path.getsize(path) / (1024 * 1024)
            self.toast.show_message(f"🎬 Grabación guardada: {fn} ({mb:.1f} MB)", kind="ok", ms=6000)
        except Exception:
            self.toast.show_message(f"🎬 Grabación guardada: {fn}", kind="ok", ms=6000)

    def _setup_shortcuts(self):
        # Ctrl+Return to launch
        sc_launch = QShortcut(QKeySequence("Ctrl+Return"), self)
        sc_launch.activated.connect(self._start_mirror)

        # Ctrl+Enter (numeric keypad)
        sc_launch2 = QShortcut(QKeySequence("Ctrl+Enter"), self)
        sc_launch2.activated.connect(self._start_mirror)

        # F5 to refresh
        sc_refresh = QShortcut(QKeySequence("F5"), self)
        sc_refresh.activated.connect(self.page_home.refresh_devices)

    def navigate_to(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        # Refresh target page if needed
        if index == 1:
            self.page_devices.refresh()
        elif index == 2:
            self.page_profiles.refresh()
        elif index == 3:
            self.page_recordings.refresh()
        elif index == 4:
            self.page_settings.refresh()

    def _start_mirror(self):
        cfg_dict = self.state.to_config()
        if self.page_home.current_device:
            cfg_dict["device"] = self.page_home.current_device.serial
        caps = self.page_home.current_device.caps if self.page_home.current_device else None
        ok = self.session_mgr.start(cfg_dict, caps)
        if ok:
            # Persist state
            try:
                cfg.save_config(self.state)
            except Exception:
                pass

    def _on_device_selected_from_tab(self, serial: str):
        self.navigate_to(0)
        self.page_home.refresh_devices()
        self.toast.show_message(f"Dispositivo activo: {serial}", kind="info")

    def _on_profile_loaded(self, name: str):
        self.navigate_to(0)
        self.toast.show_message(f"Perfil '{name}' cargado.", kind="ok")

    def _on_session_failed(self, diag):
        if diag:
            self.toast.show_message(diag.message, kind="error")
            # Auto expand console if failed
            if not self.log_text.isVisible():
                self._toggle_console()

    def _toggle_console(self):
        is_visible = self.log_text.isVisible()
        self.log_text.setVisible(not is_visible)
        self.btn_copy_logs.setVisible(not is_visible)
        self.btn_clear_logs.setVisible(not is_visible)
        self.btn_toggle_console.setText("▼ Ocultar consola" if not is_visible else "▲ Consola de registros")

    def _append_log(self, text: str):
        self.log_text.appendPlainText(text)

    def _copy_logs(self):
        QApplication.clipboard().setText(self.log_text.toPlainText())
        self.toast.show_message("Registros copiados al portapapeles", kind="info")

    def _clear_logs(self):
        self.log_text.clear()

    def _on_state_change(self, key: str):
        has_dev = bool(self.state.device)
        self.lbl_device_dot.setStyleSheet(f"font-size: 16px; color: {C['success'] if has_dev else C['muted']};")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.toast.reposition()

    def closeEvent(self, event):
        try:
            cfg.save_config(self.state)
        except Exception:
            pass
        self.session_mgr.stop_all()
        super().closeEvent(event)
