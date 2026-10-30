"""Home view for Scrcpy Studio: Device Card, Goal Selector, Live Inspector, and Action Bar."""
from __future__ import annotations

import re
from typing import Optional
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QApplication, QLineEdit
)

import scrcpy_manager as mgr
from command_builder import build_scrcpy_args
from .theme import C, RADIUS_CARD, RADIUS_CTRL
from .state import AppState
from .schema import MAIN_SECTIONS, get_goal_sections
from .services import DeviceInfo, SessionManager, Diagnosis, run_async, scan_devices, scan_details
from .widgets import GoalCard, SettingRow, card, hline, label, Toast, format_command_html
from .dialogs import AdvancedDialog


GOALS = [
    {
        "id": "balanced",
        "icon": "🚀",
        "title": "Espejo Rápido",
        "desc": "1080p a 60 FPS con baja latencia para uso diario.",
    },
    {
        "id": "gaming",
        "icon": "🎮",
        "title": "Gaming 120 FPS",
        "desc": "Ultra fluido: 120 FPS, códec H.265 y búfer ultracorto.",
    },
    {
        "id": "desktop",
        "icon": "🖥️",
        "title": "Modo Escritorio",
        "desc": "1440p, teclado nativo y ratón virtual UHID independiente.",
    },
    {
        "id": "virtual",
        "icon": "📱",
        "title": "App en Ventana",
        "desc": "Pantalla virtual secundaria para aislar una aplicación.",
    },
    {
        "id": "record",
        "icon": "🔴",
        "title": "Grabar Pantalla",
        "desc": "Captura directa a video MP4/MKV sin retrasos ni marcas.",
    },
    {
        "id": "camera",
        "icon": "📷",
        "title": "Cámara Web",
        "desc": "Usa la cámara frontal o trasera como webcam para el PC.",
    },
]


class HomePage(QWidget):
    """The main studio experience: Device -> Goal -> Launch with live inspector."""

    launch_requested = Signal()
    stop_all_requested = Signal()
    open_devices_tab = Signal()
    wifi_auto_connected = Signal(str, str)
    wifi_auto_failed = Signal(str)

    def __init__(self, state: AppState, session_mgr: SessionManager, parent=None):
        super().__init__(parent)
        self.state = state
        self.session_mgr = session_mgr
        self.current_device: Optional[DeviceInfo] = None
        self._current_diagnosis: Optional[Diagnosis] = None
        self._wifi_auto_in_progress = False

        self._build_ui()
        self._wire_events()
        self.refresh_devices()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        # ── 1. Top Device Card ──────────────────────────────────────
        self.device_frame = card("deviceCard")
        self.device_frame_lay = QVBoxLayout(self.device_frame)
        self.device_frame_lay.setContentsMargins(18, 14, 18, 14)
        self.device_frame_lay.setSpacing(10)
        root.addWidget(self.device_frame)

        # ── 2. Middle Content (Goals + Right Inspector) ─────────────
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(16)

        # Left Column: Goals Grid + App Picker
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        goals_header = QHBoxLayout()
        lbl_goals = QLabel("¿QUÉ DESEAS HACER?")
        lbl_goals.setObjectName("eyebrow")
        goals_header.addWidget(lbl_goals)
        goals_header.addStretch()
        left_col.addLayout(goals_header)

        # Goals 2x3 Grid
        self.goals_grid = QGridLayout()
        self.goals_grid.setSpacing(10)
        self.goal_buttons: dict[str, GoalCard] = {}

        for idx, g in enumerate(GOALS):
            btn = GoalCard(g["icon"], g["title"], g["desc"])
            btn.clicked.connect(lambda _, gid=g["id"]: self._on_goal_selected(gid))
            btn.doubleClicked.connect(lambda _, gid=g["id"]: self._on_goal_double_clicked(gid))
            row, col = divmod(idx, 2)
            self.goals_grid.addWidget(btn, row, col)
            self.goal_buttons[g["id"]] = btn

        left_col.addLayout(self.goals_grid)
        left_col.addStretch(1)

        mid_layout.addLayout(left_col, 3)

        # Right Column: Inspector Panel (Collapsible Quick Settings)
        self.inspector_card = card("card")
        self.inspector_card.setMinimumWidth(320)
        self.inspector_card.setMaximumWidth(400)
        insp_lay = QVBoxLayout(self.inspector_card)
        insp_lay.setContentsMargins(16, 14, 16, 14)
        insp_lay.setSpacing(10)

        insp_header = QHBoxLayout()
        self.lbl_insp = QLabel("AJUSTES RÁPIDOS")
        self.lbl_insp.setObjectName("eyebrow")
        insp_header.addWidget(self.lbl_insp)
        insp_header.addStretch()

        btn_reset = QPushButton("↺ Restaurar")
        btn_reset.setObjectName("ghost")
        btn_reset.setToolTip("Restaurar valores predeterminados para este modo")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self._reset_current_goal)
        insp_header.addWidget(btn_reset)

        btn_adv = QPushButton("⚙️ Opciones avanzadas")
        btn_adv.setObjectName("ghost")
        btn_adv.setCursor(Qt.PointingHandCursor)
        btn_adv.clicked.connect(self._open_advanced)
        insp_header.addWidget(btn_adv)
        insp_lay.addLayout(insp_header)

        # Scroll Area for Quick Settings Rows
        insp_scroll = QScrollArea()
        insp_scroll.setWidgetResizable(True)
        self.insp_content = QWidget()
        self.insp_content_lay = QVBoxLayout(self.insp_content)
        self.insp_content_lay.setContentsMargins(0, 4, 4, 4)
        self.insp_content_lay.setSpacing(8)

        insp_scroll.setWidget(self.insp_content)
        insp_lay.addWidget(insp_scroll, 1)

        # Populate initial inspector rows based on active mode
        cur_mode = self.state.active_mode.get() or "balanced"
        self._render_inspector_for_goal(cur_mode)

        mid_layout.addWidget(self.inspector_card, 2)
        root.addLayout(mid_layout, 1)

        # ── 3. Action Bar (Bottom Fixed) ────────────────────────────
        self.action_bar = card("actionBar")
        act_lay = QHBoxLayout(self.action_bar)
        act_lay.setContentsMargins(16, 10, 16, 10)
        act_lay.setSpacing(12)

        # Primary Launch CTA
        self.btn_launch = QPushButton("▶ Iniciar Sesión")
        self.btn_launch.setObjectName("primary")
        self.btn_launch.setCursor(Qt.PointingHandCursor)
        self.btn_launch.setMinimumWidth(180)
        self.btn_launch.clicked.connect(self.launch_requested.emit)
        act_lay.addWidget(self.btn_launch)

        # Summary Chips (Interactive: Clicking scrolls/highlights)
        self.chip_res = QPushButton("1080p")
        self.chip_res.setObjectName("chip")
        self.chip_fps = QPushButton("60 FPS")
        self.chip_fps.setObjectName("chip")
        self.chip_bitrate = QPushButton("8 Mbps")
        self.chip_bitrate.setObjectName("chip")
        self.chip_codec = QPushButton("H.264")
        self.chip_codec.setObjectName("chip")
        self.chip_audio = QPushButton("🔊 Audio")
        self.chip_audio.setObjectName("chip")

        for chip in (self.chip_res, self.chip_fps, self.chip_bitrate, self.chip_codec, self.chip_audio):
            chip.setCursor(Qt.PointingHandCursor)
            chip.clicked.connect(self._open_advanced)
            act_lay.addWidget(chip)

        act_lay.addStretch(1)

        # Active Sessions Badge & Stop Button
        self.lbl_sessions = QLabel("● 0 activas")
        self.lbl_sessions.setObjectName("muted")
        act_lay.addWidget(self.lbl_sessions)

        self.btn_stop = QPushButton("⏹ Detener")
        self.btn_stop.setObjectName("danger")
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.clicked.connect(self.stop_all_requested.emit)
        self.btn_stop.hide()
        act_lay.addWidget(self.btn_stop)

        root.addWidget(self.action_bar)

        # ── 4. Diagnosis Banner (Error recovery) ─────────────────────
        self.diag_banner = card("cardElevated")
        self.diag_banner.setStyleSheet(f"QFrame#cardElevated {{ border: 1px solid {C['warning']}; background: #2A1F08; }}")
        diag_lay = QHBoxLayout(self.diag_banner)
        diag_lay.setContentsMargins(16, 10, 16, 10)
        diag_lay.setSpacing(12)

        self.lbl_diag_icon = QLabel("⚠️")
        self.lbl_diag_icon.setStyleSheet("font-size: 18px;")
        diag_lay.addWidget(self.lbl_diag_icon)

        self.lbl_diag_msg = QLabel("")
        self.lbl_diag_msg.setObjectName("warn")
        self.lbl_diag_msg.setWordWrap(True)
        diag_lay.addWidget(self.lbl_diag_msg, 1)

        self.btn_diag_fix = QPushButton("Corregir y reintentar")
        self.btn_diag_fix.setObjectName("primary")
        self.btn_diag_fix.setCursor(Qt.PointingHandCursor)
        self.btn_diag_fix.clicked.connect(self._apply_diagnosis_fix)
        diag_lay.addWidget(self.btn_diag_fix)

        self.btn_diag_dismiss = QPushButton("✕")
        self.btn_diag_dismiss.setObjectName("ghost")
        self.btn_diag_dismiss.setFixedWidth(28)
        self.btn_diag_dismiss.clicked.connect(self.diag_banner.hide)
        diag_lay.addWidget(self.btn_diag_dismiss)

        self.diag_banner.hide()
        root.addWidget(self.diag_banner)

        # ── 5. Real-Time Command Bar ─────────────────────────────────
        self.cmd_bar = card("card")
        cmd_lay = QHBoxLayout(self.cmd_bar)
        cmd_lay.setContentsMargins(14, 6, 14, 6)
        cmd_lay.setSpacing(10)

        lbl_cmd_tag = QLabel("$")
        lbl_cmd_tag.setObjectName("mono")
        lbl_cmd_tag.setStyleSheet(f"color: {C['cyan']}; font-weight: bold;")
        cmd_lay.addWidget(lbl_cmd_tag)

        self.lbl_cmd = QLabel("scrcpy")
        self.lbl_cmd.setObjectName("mono")
        self.lbl_cmd.setTextInteractionFlags(Qt.TextSelectableByMouse)
        cmd_lay.addWidget(self.lbl_cmd, 1)

        self.btn_copy_cmd = QPushButton("📋 Copiar")
        self.btn_copy_cmd.setObjectName("ghost")
        self.btn_copy_cmd.setCursor(Qt.PointingHandCursor)
        self.btn_copy_cmd.clicked.connect(self._copy_command)
        cmd_lay.addWidget(self.btn_copy_cmd)

        root.addWidget(self.cmd_bar)

    def _wire_events(self):
        # Update command and chips when state changes
        self.state.subscribe(self._on_state_change)
        # Session manager signals
        self.session_mgr.changed.connect(self._update_sessions_state)
        self.session_mgr.failed.connect(self._on_session_failed)

        # Sync initial state and render contextual inspector
        mode = self.state.active_mode.get() or "balanced"
        if mode in self.goal_buttons:
            self.goal_buttons[mode].setChecked(True)
        self._on_goal_selected(mode)

    def _on_goal_double_clicked(self, gid: str):
        self._on_goal_selected(gid)
        self.launch_requested.emit()

    def _on_goal_selected(self, gid: str):
        self.state.apply_preset(gid)
        goal_title = self.goal_buttons[gid].accessibleName()
        self.btn_launch.setText(f"▶ Iniciar {goal_title}")
        self.lbl_insp.setText(f"AJUSTES — {goal_title.upper()}")
        self._render_inspector_for_goal(gid)
        if gid == "virtual" and self.current_device and not self.state.available_apps:
            run_async(lambda: mgr.get_installed_apps(self.current_device.serial),
                      lambda apps: self.state.set_available_apps(apps) if apps else None)

    def _render_inspector_for_goal(self, gid: str):
        self._clear_layout(self.insp_content_lay)
        sections = get_goal_sections(gid)
        for sec_name, specs in sections:
            sec_lbl = QLabel(sec_name.upper())
            sec_lbl.setObjectName("sectionTitle")
            self.insp_content_lay.addWidget(sec_lbl)
            for spec in specs:
                row = SettingRow(self.state, spec, self.insp_content)
                self.insp_content_lay.addWidget(row)
            self.insp_content_lay.addSpacing(6)
        self.insp_content_lay.addStretch()

    def _on_state_change(self, key: str):
        self._update_command_line()
        self._update_chips()

    def _reset_current_goal(self):
        cur_mode = self.state.active_mode.get() or "balanced"
        self.state.apply_preset(cur_mode)
        self._render_inspector_for_goal(cur_mode)
        self._update_command_line()
        self._update_chips()

    def _update_command_line(self):
        cfg = self.state.to_config()
        if self.current_device:
            cfg["device"] = self.current_device.serial
        args = ["scrcpy"] + build_scrcpy_args(cfg, is_windows=mgr.IS_WINDOWS, scrcpy_version=mgr.get_installed_version())
        self._raw_cmd_str = " ".join(args)
        cmd_html = format_command_html(args)
        self.lbl_cmd.setText(cmd_html)
        self.lbl_cmd.setToolTip(self._raw_cmd_str)

    def _update_chips(self):
        max_size = str(self.state.get("max_size"))
        res_text = {"0": "Original", "3840": "4K", "2560": "1440p", "1920": "1080p", "1280": "720p", "854": "480p"}.get(max_size, f"{max_size}px" if max_size else "Auto")
        self.chip_res.setText(f"📐 {res_text}")
        self.chip_fps.setText(f"⚡ {self.state.get('fps')} FPS")
        self.chip_bitrate.setText(f"📊 {self.state.get('bitrate')} Mbps")
        self.chip_codec.setText(f"🎬 {str(self.state.get('codec')).upper()}")
        audio_on = bool(self.state.get("audio"))
        self.chip_audio.setText("🔊 Audio ON" if audio_on else "🔇 Audio OFF")
        self.chip_audio.setStyleSheet(f"color: {C['text'] if audio_on else C['muted']};")

    def _copy_command(self):
        raw_cmd = getattr(self, "_raw_cmd_str", self.lbl_cmd.text())
        QApplication.clipboard().setText(raw_cmd)
        self.btn_copy_cmd.setText("✓ Copiado")
        self.btn_copy_cmd.setStyleSheet(f"color: {C['success']}; font-weight: bold;")
        QTimer.singleShot(1500, lambda: (
            self.btn_copy_cmd.setText("📋 Copiar"),
            self.btn_copy_cmd.setStyleSheet("")
        ))

    def _update_sessions_state(self):
        cnt = self.session_mgr.count()
        if cnt > 0:
            self.lbl_sessions.setText(f"● {cnt} activa{'s' if cnt > 1 else ''}")
            self.lbl_sessions.setStyleSheet(f"color: {C['success']}; font-weight: bold;")
            self.btn_stop.show()
            self.btn_stop.setText(f"⏹ Detener ({cnt})")
        else:
            self.lbl_sessions.setText("● 0 activas")
            self.lbl_sessions.setStyleSheet(f"color: {C['muted']};")
            self.btn_stop.hide()

    def _on_session_failed(self, diag: Optional[Diagnosis]):
        if not diag:
            return
        self._current_diagnosis = diag
        self.lbl_diag_msg.setText(diag.message)
        self.btn_diag_fix.setText(diag.fix_label)
        self.diag_banner.show()

    def _apply_diagnosis_fix(self):
        if not self._current_diagnosis:
            return
        diag = self._current_diagnosis
        self.diag_banner.hide()
        if diag.action == "refresh":
            self.refresh_devices()
            return
        if diag.fix:
            for k, v in diag.fix.items():
                self.state.set(k, v)
            # Re-launch
            self.launch_requested.emit()

    def _open_advanced(self):
        dlg = AdvancedDialog(self.state, self)
        dlg.exec()

    # ── Device Detection & Card Rendering ──────────────────────────
    def refresh_devices(self):
        self._render_device_loading()
        run_async(scan_devices, self._on_devices_scanned)

    def _on_devices_scanned(self, res):
        if isinstance(res, Exception) or not res.get("adb"):
            self._render_device_empty("ADB no disponible. Verifica que Android SDK o scrcpy estén instalados.")
            return

        devs: list[DeviceInfo] = res.get("devices", [])
        if not devs:
            self._render_device_empty()
            return

        # Pick first device (prefer Wi-Fi if available, or USB)
        selected = devs[0]
        self.current_device = selected
        self.state.device = selected.serial
        self._update_command_line()

        # If auto_wifi is enabled and connected via USB, auto-connect wirelessly
        if bool(self.state.get("auto_wifi")) and not selected.wifi and not self._wifi_auto_in_progress:
            has_wifi = any(d.wifi for d in devs)
            if not has_wifi:
                self._trigger_auto_wifi(selected.serial)

        # Fetch detailed specs in background
        run_async(lambda: scan_details(selected.serial), self._on_device_details)
        self._render_device_connected(selected)

    def _on_device_details(self, res):
        if isinstance(res, dict) and self.current_device and self.current_device.serial == res.get("serial"):
            self.current_device.caps = res.get("caps")
            self.current_device.battery = res.get("battery")
            self.current_device.latency = res.get("latency")
            self.current_device.screen = res.get("screen")
            apps = res.get("apps", [])
            if apps:
                self.state.set_available_apps(apps)
            self._render_device_connected(self.current_device)

    def _render_device_loading(self):
        self._clear_layout(self.device_frame_lay)
        lbl = QLabel("🔍 Buscando dispositivos Android conectados...")
        lbl.setObjectName("sub")
        self.device_frame_lay.addWidget(lbl)

    def _render_device_empty(self, reason: str = ""):
        self.current_device = None
        self._clear_layout(self.device_frame_lay)

        top_row = QHBoxLayout()
        icon = QLabel("🔌")
        icon.setStyleSheet("font-size: 24px;")
        top_row.addWidget(icon)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_t = QLabel("No se detectó ningún dispositivo conectado")
        lbl_t.setObjectName("h2")
        lbl_s = QLabel(reason or "Sigue estos 3 pasos rápidos en tu móvil Android para conectar:")
        lbl_s.setObjectName("sub")
        title_box.addWidget(lbl_t)
        title_box.addWidget(lbl_s)
        top_row.addLayout(title_box, 1)

        btn_retry = QPushButton("Buscar de nuevo")
        btn_retry.setObjectName("primary")
        btn_retry.setCursor(Qt.PointingHandCursor)
        btn_retry.clicked.connect(self.refresh_devices)
        top_row.addWidget(btn_retry)
        self.device_frame_lay.addLayout(top_row)

        # 3 Guided Steps
        steps_box = QHBoxLayout()
        steps_box.setSpacing(12)

        for num, text in [
            ("1", "Ajustes > Acerca del teléfono > Pulsa 7 veces en 'Número de compilación'"),
            ("2", "Ajustes > Sistema > Opciones de desarrollador > Activa 'Depuración USB'"),
            ("3", "Conecta el cable USB a tu PC y pulsa 'Permitir siempre' en la pantalla"),
        ]:
            card_step = card("card")
            card_step.setStyleSheet(f"QFrame#card {{ background: rgba(255,255,255,0.03); border: 1px solid {C['border']}; }}")
            step_lay = QHBoxLayout(card_step)
            step_lay.setContentsMargins(10, 8, 10, 8)
            step_lay.setSpacing(8)

            lbl_num = QLabel(num)
            lbl_num.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {C['cyan']}; background: {C['elevated']}; border-radius: 10px; min-width: 20px; max-width: 20px; min-height: 20px; max-height: 20px; qproperty-alignment: AlignCenter;")
            step_lay.addWidget(lbl_num)

            lbl_step = QLabel(text)
            lbl_step.setWordWrap(True)
            lbl_step.setStyleSheet(f"font-size: 11px; color: {C['text2']};")
            step_lay.addWidget(lbl_step, 1)
            steps_box.addWidget(card_step)

        self.device_frame_lay.addLayout(steps_box)

    def _render_device_connected(self, dev: DeviceInfo):
        self._clear_layout(self.device_frame_lay)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        icon = QLabel("📱" if not dev.wifi else "📶")
        icon.setStyleSheet("font-size: 26px;")
        top_row.addWidget(icon)

        # Name and Serial
        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        lbl_name = QLabel(dev.title)
        lbl_name.setObjectName("h2")
        name_row.addWidget(lbl_name)

        conn_badge = QLabel(" Wi-Fi " if dev.wifi else " USB ")
        conn_badge.setStyleSheet(f"background: {C['elevated']}; border: 1px solid {C['border_strong']}; border-radius: 4px; font-size: 11px; font-weight: bold; color: {C['cyan']}; padding: 2px 6px;")
        name_row.addWidget(conn_badge)

        # Battery Indicator
        if dev.battery is not None:
            if isinstance(dev.battery, dict):
                lvl = dev.battery.get("level")
                charging = dev.battery.get("charging", False)
            else:
                lvl = dev.battery
                charging = False

            if lvl is not None:
                icon_b = "⚡" if charging else "🔋"
                if lvl > 50:
                    b_color, b_bg = C["success"], "rgba(16, 185, 129, 0.14)"
                elif lvl >= 20:
                    b_color, b_bg = C["warning"], "rgba(245, 158, 11, 0.14)"
                else:
                    b_color, b_bg = C["danger"], "rgba(244, 63, 94, 0.16)"
                    icon_b = "🪫"

                bat_badge = QLabel(f" {icon_b} {lvl}% ")
                bat_badge.setStyleSheet(
                    f"background: {b_bg}; border: 1px solid {b_color}; "
                    f"border-radius: 4px; font-size: 11px; font-weight: bold; "
                    f"color: {b_color}; padding: 2px 6px;"
                )
                name_row.addWidget(bat_badge)

        # Wi-Fi Latency Indicator
        if dev.wifi and dev.latency is not None:
            if dev.latency < 25:
                l_color, l_txt = C["success"], f"📶 {dev.latency} ms (Rápido)"
            elif dev.latency < 60:
                l_color, l_txt = C["warning"], f"📶 {dev.latency} ms (Estable)"
            else:
                l_color, l_txt = C["danger"], f"📶 {dev.latency} ms (Lento)"

            lat_badge = QLabel(f" {l_txt} ")
            lat_badge.setStyleSheet(
                f"background: {C['elevated']}; border: 1px solid {l_color}; "
                f"border-radius: 4px; font-size: 11px; font-weight: 600; "
                f"color: {l_color}; padding: 2px 6px;"
            )
            name_row.addWidget(lat_badge)

        # Physical Screen Resolution Chip
        if dev.screen and dev.screen.get("res"):
            res_txt = dev.screen["res"]
            if dev.screen.get("fps"):
                res_txt += f" @ {dev.screen['fps']}Hz"
            scr_badge = QLabel(f" 📐 {res_txt} ")
            scr_badge.setStyleSheet(
                f"background: {C['elevated']}; border: 1px solid {C['border']}; "
                f"border-radius: 4px; font-size: 11px; color: {C['text2']}; padding: 2px 6px;"
            )
            name_row.addWidget(scr_badge)

        name_row.addStretch()
        info_col.addLayout(name_row)

        sub_text = f"Serial: {dev.serial}"
        if dev.android:
            sub_text += f"  ·  Android {dev.android}"
        lbl_sub = QLabel(sub_text)
        lbl_sub.setObjectName("sub")
        info_col.addWidget(lbl_sub)
        top_row.addLayout(info_col, 1)

        # Quick preview button
        btn_preview = QPushButton("📸 Vista Previa")
        btn_preview.setObjectName("ghost")
        btn_preview.setCursor(Qt.PointingHandCursor)
        btn_preview.setToolTip("Capturar una vista previa rápida de la pantalla del móvil")
        btn_preview.clicked.connect(lambda: self._show_screen_preview(dev.serial, btn_preview))
        top_row.addWidget(btn_preview)

        # Auto-connect Wi-Fi button when connected via USB
        if not dev.wifi:
            btn_auto_wifi = QPushButton("📶 Pasar a Wi-Fi (Auto)")
            btn_auto_wifi.setObjectName("primary")
            btn_auto_wifi.setCursor(Qt.PointingHandCursor)
            btn_auto_wifi.setToolTip("Activa ADB inalámbrico y conecta por Wi-Fi automáticamente sin escribir la IP")
            btn_auto_wifi.clicked.connect(lambda: self._trigger_auto_wifi(dev.serial, btn_auto_wifi))
            top_row.addWidget(btn_auto_wifi)

        btn_change = QPushButton("Dispositivos")
        btn_change.setCursor(Qt.PointingHandCursor)
        btn_change.clicked.connect(self.open_devices_tab.emit)
        top_row.addWidget(btn_change)

        self.device_frame_lay.addLayout(top_row)

    def _show_screen_preview(self, serial: str, btn: QPushButton):
        from .services import capture_quick_preview
        from PySide6.QtGui import QImage, QPixmap
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel

        btn.setEnabled(False)
        btn.setText("⏳ Capturando...")

        def _done(raw_png):
            btn.setEnabled(True)
            btn.setText("📸 Vista Previa")
            if not raw_png or not isinstance(raw_png, bytes):
                main_win = self.window()
                if hasattr(main_win, "toast"):
                    main_win.toast.show_message("No se pudo capturar la vista previa", kind="warn")
                return

            img = QImage.fromData(raw_png)
            if img.isNull():
                return

            dlg = QDialog(self)
            dlg.setWindowTitle("📸 Vista Previa — Pantalla en Vivo")
            dlg.resize(360, 640)
            dlg_lay = QVBoxLayout(dlg)
            dlg_lay.setContentsMargins(16, 16, 16, 16)
            dlg_lay.setSpacing(10)

            lbl_img = QLabel()
            pix = QPixmap.fromImage(img)
            pix_scaled = pix.scaled(320, 560, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_img.setPixmap(pix_scaled)
            lbl_img.setAlignment(Qt.AlignCenter)
            dlg_lay.addWidget(lbl_img, 1)

            btn_close = QPushButton("Cerrar")
            btn_close.clicked.connect(dlg.accept)
            dlg_lay.addWidget(btn_close)
            dlg.exec()

        run_async(lambda: capture_quick_preview(serial), _done)

    def _trigger_auto_wifi(self, serial: str, btn: Optional[QPushButton] = None):
        if self._wifi_auto_in_progress or ":" in serial:
            return
        self._wifi_auto_in_progress = True
        if btn:
            btn.setEnabled(False)
            btn.setText("⏳ Conectando Wi-Fi...")

        def on_done(res):
            self._wifi_auto_in_progress = False
            if btn:
                btn.setEnabled(True)
                btn.setText("📶 Pasar a Wi-Fi (Auto)")
            msg = str(res)
            if "Conectado a" in msg:
                m = re.search(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b', msg)
                target_ip = f"{m.group(1)}:5555" if m else ""
                self.wifi_auto_connected.emit(msg, target_ip)
                if target_ip:
                    self.state.device = target_ip
                self.refresh_devices()
            else:
                self.wifi_auto_failed.emit(msg)

        run_async(lambda: mgr.enable_tcpip(serial), on_done)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
