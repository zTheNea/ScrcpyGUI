"""Devices view for Scrcpy Studio: Device listing, Wi-Fi pairing/connect, and full diagnostics."""
from __future__ import annotations

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QListWidget, QListWidgetItem
)

import re
import scrcpy_manager as mgr
from .theme import C
from .state import AppState
from .services import DeviceInfo, run_async, scan_devices, scan_details
from .widgets import card, hline, Toggle
from .dialogs import PairDeviceDialog, PromptDialog


class DevicesPage(QWidget):
    """Manage connected devices, Wi-Fi connections, and inspect hardware diagnostics."""

    device_selected = Signal(str)

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self.devices: list[DeviceInfo] = []
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
        lbl_h1 = QLabel("Dispositivos Conectados")
        lbl_h1.setObjectName("h1")
        lbl_sub = QLabel("Administra conexiones USB y Wi-Fi y diagnostica compatibilidad de hardware.")
        lbl_sub.setObjectName("sub")
        title_box.addWidget(lbl_h1)
        title_box.addWidget(lbl_sub)
        head.addLayout(title_box, 1)

        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.refresh)
        head.addWidget(btn_refresh)
        root.addLayout(head)

        # Main Split: Device list on left, Actions & Details on right
        body = QHBoxLayout()
        body.setSpacing(16)

        # Left Column: Devices List
        left_card = card("card")
        left_lay = QVBoxLayout(left_card)
        left_lay.setContentsMargins(16, 14, 16, 14)
        left_lay.setSpacing(10)

        lbl_list = QLabel("DISPOSITIVOS ACTIVOS")
        lbl_list.setObjectName("eyebrow")
        left_lay.addWidget(lbl_list)

        self.dev_scroll = QScrollArea()
        self.dev_scroll.setWidgetResizable(True)
        self.dev_container = QWidget()
        self.dev_list_lay = QVBoxLayout(self.dev_container)
        self.dev_list_lay.setContentsMargins(0, 4, 4, 4)
        self.dev_list_lay.setSpacing(8)
        self.dev_scroll.setWidget(self.dev_container)
        left_lay.addWidget(self.dev_scroll, 1)

        body.addWidget(left_card, 3)

        # Right Column: Wi-Fi Tools & Hardware Inspector
        right_col = QVBoxLayout()
        right_col.setSpacing(14)

        # Wi-Fi Tools Card
        wifi_card = card("cardElevated")
        wifi_lay = QVBoxLayout(wifi_card)
        wifi_lay.setContentsMargins(16, 14, 16, 14)
        wifi_lay.setSpacing(10)

        lbl_wifi = QLabel("CONEXIÓN INALÁMBRICA (WI-FI)")
        lbl_wifi.setObjectName("eyebrow")
        wifi_lay.addWidget(lbl_wifi)

        # 1-Click Auto USB -> Wi-Fi Connect
        self.btn_auto_wifi = QPushButton("⚡ Activar Wi-Fi Automático por USB (1 Clic)")
        self.btn_auto_wifi.setObjectName("primary")
        self.btn_auto_wifi.setCursor(Qt.PointingHandCursor)
        self.btn_auto_wifi.setToolTip("Activa TCP/IP en el móvil conectado por USB, detecta su IP y conecta automáticamente")
        self.btn_auto_wifi.clicked.connect(self._auto_connect_usb)
        wifi_lay.addWidget(self.btn_auto_wifi)

        # Toggle for auto-connecting whenever USB is plugged in
        auto_row = QHBoxLayout()
        auto_row.setSpacing(10)
        lbl_auto = QLabel("Auto-conectar por Wi-Fi al enchufar USB:")
        lbl_auto.setObjectName("sub")
        self.toggle_auto_wifi = Toggle()
        self.toggle_auto_wifi.setChecked(bool(self.state.get("auto_wifi")))
        self.toggle_auto_wifi.toggled.connect(lambda on: self.state.set("auto_wifi", on))
        auto_row.addWidget(lbl_auto, 1)
        auto_row.addWidget(self.toggle_auto_wifi)
        wifi_lay.addLayout(auto_row)

        wifi_lay.addWidget(hline())

        lbl_manual = QLabel("O CONECTA MANUALMENTE:")
        lbl_manual.setObjectName("sectionTitle")
        wifi_lay.addWidget(lbl_manual)

        # Quick Connect IP
        ip_row = QHBoxLayout()
        self.inp_ip = QLineEdit()
        self.inp_ip.setPlaceholderText("IP:Puerto (ej. 192.168.1.50:5555)")
        ip_row.addWidget(self.inp_ip, 1)

        btn_conn = QPushButton("Conectar")
        btn_conn.setCursor(Qt.PointingHandCursor)
        btn_conn.clicked.connect(self._connect_ip)
        ip_row.addWidget(btn_conn)
        wifi_lay.addLayout(ip_row)

        btn_pair = QPushButton("🔑 Vincular con código (Android 11+)")
        btn_pair.setCursor(Qt.PointingHandCursor)
        btn_pair.clicked.connect(self._open_pair_dialog)
        wifi_lay.addWidget(btn_pair)

        self.lbl_wifi_status = QLabel("")
        self.lbl_wifi_status.setObjectName("sub")
        self.lbl_wifi_status.setWordWrap(True)
        wifi_lay.addWidget(self.lbl_wifi_status)

        right_col.addWidget(wifi_card)

        # Hardware Inspector Card
        self.diag_card = card("cardElevated")
        self.diag_lay = QVBoxLayout(self.diag_card)
        self.diag_lay.setContentsMargins(16, 14, 16, 14)
        self.diag_lay.setSpacing(10)

        lbl_diag = QLabel("CAPACIDADES DE HARDWARE")
        lbl_diag.setObjectName("eyebrow")
        self.diag_lay.addWidget(lbl_diag)

        self.lbl_diag_details = QLabel("Selecciona un dispositivo para inspeccionar sus encoders, cámaras y pantallas.")
        self.lbl_diag_details.setObjectName("sub")
        self.lbl_diag_details.setWordWrap(True)
        self.diag_lay.addWidget(self.lbl_diag_details)

        self.btn_run_diag = QPushButton("🔍 Ejecutar Análisis Completo")
        self.btn_run_diag.setCursor(Qt.PointingHandCursor)
        self.btn_run_diag.clicked.connect(self._analyze_selected)
        self.btn_run_diag.setEnabled(False)
        self.diag_lay.addWidget(self.btn_run_diag)

        self.btn_preview_device = QPushButton("📸 Capturar Pantalla del Móvil")
        self.btn_preview_device.setObjectName("ghost")
        self.btn_preview_device.setCursor(Qt.PointingHandCursor)
        self.btn_preview_device.clicked.connect(self._preview_selected)
        self.btn_preview_device.setEnabled(False)
        self.diag_lay.addWidget(self.btn_preview_device)

        self.lbl_preview_img = QLabel()
        self.lbl_preview_img.setAlignment(Qt.AlignCenter)
        self.lbl_preview_img.hide()
        self.diag_lay.addWidget(self.lbl_preview_img)

        self.diag_lay.addStretch()
        right_col.addWidget(self.diag_card, 1)

        body.addLayout(right_col, 2)
        root.addLayout(body, 1)

    def refresh(self):
        self._clear_layout(self.dev_list_lay)
        lbl = QLabel("Buscando dispositivos...")
        lbl.setObjectName("sub")
        self.dev_list_lay.addWidget(lbl)
        run_async(scan_devices, self._on_scanned)

    def _on_scanned(self, res):
        self._clear_layout(self.dev_list_lay)
        if isinstance(res, Exception) or not res.get("adb"):
            lbl = QLabel("ADB no disponible. Verifica la instalación.")
            lbl.setObjectName("warn")
            self.dev_list_lay.addWidget(lbl)
            return

        self.devices = res.get("devices", [])
        if not self.devices:
            lbl = QLabel("No hay dispositivos conectados por USB o Wi-Fi.")
            lbl.setObjectName("sub")
            self.dev_list_lay.addWidget(lbl)
            self.btn_run_diag.setEnabled(False)
            return

        for dev in self.devices:
            dev_frame = card("cardElevated" if self.state.device == dev.serial else "card")
            dev_lay = QHBoxLayout(dev_frame)
            dev_lay.setContentsMargins(12, 10, 12, 10)
            dev_lay.setSpacing(10)

            icon = QLabel("📶" if dev.wifi else "📱")
            icon.setStyleSheet("font-size: 20px;")
            dev_lay.addWidget(icon)

            info = QVBoxLayout()
            info.setSpacing(2)
            lbl_title = QLabel(dev.title)
            lbl_title.setStyleSheet("font-weight: bold; font-size: 14px;")
            info.addWidget(lbl_title)

            lbl_sub = QLabel(f"{dev.serial} ({'Wi-Fi' if dev.wifi else 'USB'})")
            lbl_sub.setObjectName("sub")
            info.addWidget(lbl_sub)
            dev_lay.addLayout(info, 1)

            btn_use = QPushButton("Usar" if self.state.device != dev.serial else "✓ Activo")
            btn_use.setObjectName("primary" if self.state.device == dev.serial else "")
            btn_use.setCursor(Qt.PointingHandCursor)
            btn_use.clicked.connect(lambda _, s=dev.serial: self._select_device(s))
            dev_lay.addWidget(btn_use)

            self.dev_list_lay.addWidget(dev_frame)

        self.dev_list_lay.addStretch()
        self.btn_run_diag.setEnabled(True)
        self.btn_preview_device.setEnabled(True)

    def _select_device(self, serial: str):
        self.state.device = serial
        self.device_selected.emit(serial)
        self.refresh()

    def _analyze_selected(self):
        target = self.state.device or (self.devices[0].serial if self.devices else None)
        if not target:
            return
        self.lbl_diag_details.setText("Analizando capacidades de hardware... Por favor espera unos segundos.")
        self.btn_run_diag.setEnabled(False)
        run_async(lambda: scan_details(target), self._on_diag_done)

    def _on_diag_done(self, res):
        self.btn_run_diag.setEnabled(True)
        if not isinstance(res, dict) or not res.get("caps"):
            self.lbl_diag_details.setText("No se pudieron obtener las capacidades del dispositivo.")
            return

        caps = res["caps"]
        lines = [
            f"📱 Dispositivo: {caps.get('brand', '')} {caps.get('model', '')} (Android {caps.get('android_version', '?')})",
            f"🎬 Códecs Video: {', '.join(caps.get('video_codecs', [])) or 'H264'}",
            f"🔊 Códecs Audio: {', '.join(caps.get('audio_codecs', [])) or 'Estándar'}",
            f"📷 Cámaras detectadas: {len(caps.get('cameras', []))}",
            f"🖥️ Pantallas detectadas: {len(caps.get('displays', []))}",
        ]
        bat = res.get("battery")
        if bat:
            lvl = bat.get("level") if isinstance(bat, dict) else bat
            if lvl is not None:
                lines.append(f"🔋 Batería: {lvl}%")
        lat = res.get("latency")
        if lat is not None:
            lines.append(f"📶 Latencia Wi-Fi: {lat} ms")
        scr = res.get("screen")
        if scr and scr.get("res"):
            lines.append(f"📐 Pantalla física: {scr['res']} @ {scr.get('fps', '60')}Hz")

        self.lbl_diag_details.setText("\n".join(lines))

    def _preview_selected(self):
        target = self.state.device or (self.devices[0].serial if self.devices else None)
        if not target:
            return
        from .services import capture_quick_preview
        from PySide6.QtGui import QImage, QPixmap

        self.btn_preview_device.setEnabled(False)
        self.btn_preview_device.setText("⏳ Capturando...")

        def _done(raw_png):
            self.btn_preview_device.setEnabled(True)
            self.btn_preview_device.setText("📸 Capturar Pantalla del Móvil")
            if not raw_png or not isinstance(raw_png, bytes):
                return
            img = QImage.fromData(raw_png)
            if img.isNull():
                return
            pix = QPixmap.fromImage(img)
            self.lbl_preview_img.setPixmap(pix.scaled(200, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.lbl_preview_img.show()

        run_async(lambda: capture_quick_preview(target), _done)

    def _connect_ip(self):
        ip = self.inp_ip.text().strip()
        if not ip:
            return
        self.lbl_wifi_status.setText("Conectando...")
        run_async(lambda: mgr.connect_wifi(ip), self._on_wifi_connected)

    def _on_wifi_connected(self, res):
        ok, msg = res if isinstance(res, tuple) else (False, str(res))
        self.lbl_wifi_status.setText(f"{'✅' if ok else '❌'} {msg}")
        self.refresh()

    def _open_pair_dialog(self):
        dlg = PairDeviceDialog(self)
        if dlg.exec():
            host, code = dlg.get_data()
            if host and code:
                self.lbl_wifi_status.setText("Vinculando...")
                run_async(lambda: mgr.pair_device(host, code), self._on_wifi_connected)

    def _auto_connect_usb(self):
        target = self.state.device
        if not target or ":" in target:
            for d in self.devices:
                if not d.wifi:
                    target = d.serial
                    break
        if not target or ":" in target:
            self.lbl_wifi_status.setText("⚠️ Conecta tu móvil por cable USB primero para activar el modo Wi-Fi.")
            return

        self.btn_auto_wifi.setEnabled(False)
        self.btn_auto_wifi.setText("⏳ Configurando Wi-Fi...")
        self.lbl_wifi_status.setText("⚡ Activando TCP/IP y buscando IP Wi-Fi...")

        def on_done(res):
            self.btn_auto_wifi.setEnabled(True)
            self.btn_auto_wifi.setText("⚡ Activar Wi-Fi Automático por USB (1 Clic)")
            msg = str(res)
            ok = "Conectado a" in msg
            self.lbl_wifi_status.setText(f"{'✅' if ok else '❌'} {msg}")
            if ok:
                m = re.search(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b', msg)
                if m:
                    target_ip = f"{m.group(1)}:5555"
                    self.inp_ip.setText(target_ip)
                    self.state.device = target_ip
                    self.device_selected.emit(target_ip)
                self.refresh()

        run_async(lambda: mgr.enable_tcpip(target), on_done)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
