"""Reusable Qt components for Scrcpy Studio."""
from __future__ import annotations

from PySide6.QtCore import (
    Qt, QSize, QRectF, QPropertyAnimation, QEasingCurve, Property, Signal,
    QTimer,
)
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPen, QBrush, QPainterPath
from PySide6.QtWidgets import (
    QAbstractButton, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QComboBox, QLineEdit, QWidget, QGraphicsDropShadowEffect, QSizePolicy,
    QPushButton, QInputDialog,
)

from .schema import Spec, VALUE_LABELS, STD_NUM_MAPS
from .state import AppState
from .theme import C


def hline() -> QFrame:
    f = QFrame()
    f.setObjectName("sep")
    f.setFrameShape(QFrame.HLine)
    return f


def label(text: str, name: str = "", wrap: bool = False) -> QLabel:
    lb = QLabel(text)
    if name:
        lb.setObjectName(name)
    lb.setWordWrap(wrap)
    return lb


def card(name: str = "card") -> QFrame:
    f = QFrame()
    f.setObjectName(name)
    return f


def _gradient(rect: QRectF) -> QLinearGradient:
    g = QLinearGradient(rect.topLeft(), rect.bottomRight())
    g.setColorAt(0, QColor(C["cyan"]))
    g.setColorAt(1, QColor(C["indigo"]))
    return g


class Toggle(QAbstractButton):
    """Animated iOS-style switch (44x24, accessible, keyboard focusable)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(44, 24)
        self.setFocusPolicy(Qt.StrongFocus)
        self._pos = 0.0
        self._anim = QPropertyAnimation(self, b"knob", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self.toggled.connect(self._animate)

    def _animate(self, on: bool):
        self._anim.stop()
        self._anim.setEndValue(1.0 if on else 0.0)
        self._anim.start()

    def get_knob(self) -> float:
        return self._pos

    def set_knob(self, v: float):
        self._pos = v
        self.update()

    knob = Property(float, get_knob, set_knob)

    def setChecked(self, on: bool):  # snap without animation when set from state
        super().setChecked(on)
        self._anim.stop()
        self._pos = 1.0 if on else 0.0
        self.update()

    def sizeHint(self):
        return QSize(44, 24)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(0, 0, self.width(), self.height())
        track = QPainterPath()
        track.addRoundedRect(r.adjusted(1, 1, -1, -1), 11, 11)
        enabled = self.isEnabled()
        if self.isChecked() or self._pos > 0.5:
            p.fillPath(track, QBrush(_gradient(r)) if enabled else QColor(C["border_strong"]))
        else:
            p.fillPath(track, QColor(C["border"] if enabled else C["surface"]))
            p.setPen(QPen(QColor(C["border_strong"]), 1))
            p.drawPath(track)
        x = 3 + self._pos * (self.width() - 24 + 0)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#FFFFFF" if enabled else C["muted"]))
        p.drawEllipse(QRectF(x, 3, 18, 18))
        if self.hasFocus():
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(C["cyan"]), 2))
            p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 11, 11)


def format_command_html(args: list[str]) -> str:
    """Format scrcpy CLI command into rich syntax-highlighted HTML."""
    if not args:
        return ""
    parts = []
    # Binary name in emerald green
    parts.append(f"<span style='color: #10B981; font-weight: 700;'>{args[0]}</span>")

    for arg in args[1:]:
        if arg.startswith("-"):
            if "=" in arg:
                flag, val = arg.split("=", 1)
                # App packages or paths -> Soft purple
                if "+" in val or "/" in val or "\\" in val:
                    val_color = "#C084FC"
                # Numbers or units -> Amber gold
                elif val.isdigit() or val.endswith("M") or val.endswith("K") or val.endswith("FPS"):
                    val_color = "#FBBF24"
                # Codecs and strings -> Soft cyan
                else:
                    val_color = "#67E8F9"
                parts.append(
                    f"<span style='color: #38BDF8; font-weight: 600;'>{flag}</span>"
                    f"<span style='color: #64748B;'>=</span>"
                    f"<span style='color: {val_color}; font-weight: 500;'>{val}</span>"
                )
            else:
                parts.append(f"<span style='color: #38BDF8; font-weight: 600;'>{arg}</span>")
        else:
            parts.append(f"<span style='color: #F8FAFC;'>{arg}</span>")

    return " ".join(parts)


class GoalCard(QAbstractButton):
    """Large selectable goal card with gradient glow and micro-interactions."""

    doubleClicked = Signal()

    def __init__(self, icon: str, title: str, desc: str, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumHeight(114)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(3)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        self._icon = QLabel(icon)
        self._icon.setStyleSheet("font-size: 26px; background: transparent;")
        top_row.addWidget(self._icon)
        top_row.addStretch()

        self._badge = QLabel("✓ ACTIVO")
        self._badge.setStyleSheet(
            f"background: rgba(6, 182, 212, 0.16); border: 1px solid {C['cyan']}; "
            f"color: {C['cyan_bright']}; font-size: 10px; font-weight: 700; "
            f"border-radius: 999px; padding: 2px 8px;"
        )
        self._badge.hide()
        top_row.addWidget(self._badge)
        lay.addLayout(top_row)

        self._title = QLabel(title)
        self._title.setStyleSheet("font-size: 15px; font-weight: 700; background: transparent;")
        self._desc = QLabel(desc)
        self._desc.setWordWrap(True)
        self._desc.setStyleSheet(f"font-size: 12px; color: {C['text2']}; background: transparent; line-height: 1.3;")

        for w in (self._title, self._desc, self._badge):
            w.setAttribute(Qt.WA_TransparentForMouseEvents)

        lay.addWidget(self._title)
        lay.addWidget(self._desc)

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(0)
        self._shadow.setOffset(0, 2)
        self._shadow.setColor(QColor(C["cyan"]))
        self.setGraphicsEffect(self._shadow)
        self.toggled.connect(self._on_toggled)
        self.setAccessibleName(title)

    def mouseDoubleClickEvent(self, e):
        super().mouseDoubleClickEvent(e)
        self.doubleClicked.emit()

    def _on_toggled(self, on: bool):
        self._shadow.setBlurRadius(24 if on else 0)
        self._badge.setVisible(on)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        hovered = self.underMouse()

        if self.isChecked():
            # Glowing active card gradient
            grad = QLinearGradient(r.topLeft(), r.bottomRight())
            grad.setColorAt(0.0, QColor("#101C38"))
            grad.setColorAt(0.5, QColor("#142142"))
            grad.setColorAt(1.0, QColor("#1C1E4E"))
            p.setBrush(grad)
            p.setPen(QPen(QBrush(_gradient(r)), 2))
        else:
            bg = QColor(C["hover"] if hovered else C["surface"])
            p.setBrush(bg)
            border_c = QColor(C["cyan"] if hovered else C["border"])
            p.setPen(QPen(border_c, 1.5 if hovered else 1))

        p.drawRoundedRect(r, 14, 14)
        if self.hasFocus():
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(C["cyan_bright"]), 1, Qt.DashLine))
            p.drawRoundedRect(r.adjusted(4, 4, -4, -4), 10, 10)

    def enterEvent(self, e):
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.update()
        super().leaveEvent(e)



class Toast(QFrame):
    """Transient bottom-right notification."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("toast")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        self._lbl = QLabel("")
        self._lbl.setWordWrap(True)
        self._lbl.setMaximumWidth(420)
        lay.addWidget(self._lbl)
        self.hide()
        self._timer = QTimer(self, singleShot=True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text: str, kind: str = "info", ms: int = 4200):
        color = {"info": C["cyan"], "ok": C["success"], "warn": C["warning"],
                 "error": C["danger"]}.get(kind, C["cyan"])
        self.setStyleSheet(f"QFrame#toast {{ border: 1px solid {color}; }}")
        self._lbl.setText(text)
        self.adjustSize()
        self.reposition()
        self.show()
        self.raise_()
        self._timer.start(ms)

    def reposition(self):
        p = self.parentWidget()
        if p:
            self.move(p.width() - self.width() - 24, p.height() - self.height() - 80)


# ── Schema-driven setting rows ──────────────────────────────────────
class SettingRow(QWidget):
    """Two-way bound control for one ``Spec`` with guardian feedback."""

    def __init__(self, state: AppState, spec: Spec, parent=None):
        super().__init__(parent)
        self.state, self.spec = state, spec
        self._busy = False
        self.setProperty("specKey", spec.key)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 4, 0, 4)
        root.setSpacing(4)

        head = QHBoxLayout()
        head.setSpacing(10)
        self.lbl = QLabel(spec.label)
        self.lbl.setWordWrap(True)
        head.addWidget(self.lbl, 1)
        self.value_lbl = QLabel("")
        self.value_lbl.setObjectName("muted")
        self.control = self._make_control()
        head.addWidget(self.control, 0, Qt.AlignRight)
        if spec.kind == "app":
            self.btn_refresh_apps = QPushButton("🔄")
            self.btn_refresh_apps.setObjectName("ghost")
            self.btn_refresh_apps.setToolTip("Actualizar lista de apps del móvil")
            self.btn_refresh_apps.setFixedSize(30, 30)
            self.btn_refresh_apps.setCursor(Qt.PointingHandCursor)
            self.btn_refresh_apps.clicked.connect(self._trigger_app_scan)
            head.addWidget(self.btn_refresh_apps, 0, Qt.AlignRight)
        root.addLayout(head)
        self.reason = QLabel("")
        self.reason.setObjectName("warn")
        self.reason.setWordWrap(True)
        self.reason.hide()
        root.addWidget(self.reason)
        if spec.tip:
            self.setToolTip(spec.tip)
        self.control.setAccessibleName(spec.label)
        state.subscribe(self._on_state)
        self.destroyed.connect(lambda *_: state.unsubscribe(self._on_state))
        self.refresh()

    # control factories
    def _make_control(self) -> QWidget:
        s, st = self.spec, self.state
        if s.kind == "switch":
            w = Toggle()
            w.toggled.connect(lambda on: self._push(on))
            return w
        if s.kind == "app":
            w = QComboBox()
            w.setMinimumWidth(190)
            self._populate_app_combo(w)
            w.currentIndexChanged.connect(self._on_app_combo_changed)
            return w
        if s.kind in ("choice", "map", "slider"):
            w = QComboBox()
            w.setMinimumWidth(190)
            if s.kind == "map":
                for text, val in s.opts.items():
                    w.addItem(text, val)
            elif s.kind == "slider":
                options = STD_NUM_MAPS.get(s.key)
                if not options:
                    lo, hi = s.rng
                    step = max(1, (hi - lo) // 5)
                    options = {f"{v} {s.unit}".strip(): v for v in range(lo, hi + 1, step)}
                for text, val in options.items():
                    w.addItem(text, val)
            else:
                for val in s.opts:
                    w.addItem(VALUE_LABELS.get(val, val), val)
            w.currentIndexChanged.connect(lambda _i: self._push(w.currentData()))
            return w
        w = QLineEdit()
        w.setMinimumWidth(190)
        w.setPlaceholderText(s.placeholder)
        w.textEdited.connect(lambda t: self._push(t))
        return w

    def _populate_app_combo(self, w: QComboBox):
        w.blockSignals(True)
        w.clear()
        w.addItem("🖥️ Ninguna (Pantalla libre)", "")
        apps = getattr(self.state, "available_apps", [])
        if apps:
            for name, pkg in apps:
                w.addItem(f"📱 {name}", pkg)
                w.setItemData(w.count() - 1, f"{name}\n({pkg})", Qt.ToolTipRole)
        else:
            w.addItem("📱 Conecta el móvil para listar apps...", "__hint__")
        w.addItem("✏️ Escribir paquete manual...", "__custom__")
        w.blockSignals(False)

    def _on_app_combo_changed(self, _i: int):
        if self._busy:
            return
        data = self.control.currentData()
        if data == "__custom__":
            curr = str(self.state.get(self.spec.key) or "").strip()
            pkg, ok = QInputDialog.getText(
                self,
                "App Personalizada",
                "Introduce el nombre del paquete Android (ej: com.whatsapp):",
                QLineEdit.Normal,
                curr,
            )
            if ok and pkg.strip():
                self._push(pkg.strip())
            else:
                self.refresh()
            return
        if data == "__hint__":
            self.refresh()
            return
        self._push(data or "")

    def _trigger_app_scan(self):
        from .services import run_async
        import scrcpy_manager as mgr
        dev = getattr(self.state, "device", "")
        if not dev:
            devs = mgr.list_devices()
            if devs:
                dev = devs[0][0]
        if not dev:
            return
        if hasattr(self, "btn_refresh_apps"):
            self.btn_refresh_apps.setEnabled(False)
            self.btn_refresh_apps.setText("⌛")
        def _done(apps):
            if hasattr(self, "btn_refresh_apps"):
                self.btn_refresh_apps.setEnabled(True)
                self.btn_refresh_apps.setText("🔄")
            if isinstance(apps, list) and apps:
                self.state.set_available_apps(apps)
        run_async(lambda: mgr.get_installed_apps(dev), _done)

    def _push(self, value):
        if self._busy or value is None or value in ("__custom__", "__hint__"):
            return
        self._busy = True
        try:
            self.state.set(self.spec.key, value)
        finally:
            self._busy = False
        self._update_value_label()

    def _on_state(self, key: str):
        if key in ("*", self.spec.key) or key in self._deps():
            try:
                self.refresh()
            except RuntimeError:  # widget already deleted
                self.state.unsubscribe(self._on_state)

    @staticmethod
    def _deps() -> tuple:
        return ("no_control", "video_source", "audio", "virtual_display", "record", "available_apps")

    def refresh(self):
        s, st = self.spec, self.state
        val = st.get(s.key)
        self._busy = True
        try:
            c = self.control
            if s.kind == "switch":
                c.setChecked(bool(val))
            elif s.kind == "app":
                curr_val = str(val or "").strip()
                self._populate_app_combo(c)
                idx = c.findData(curr_val)
                if idx >= 0:
                    c.setCurrentIndex(idx)
                elif curr_val:
                    insert_idx = max(1, c.count() - 1)
                    c.insertItem(insert_idx, f"📦 {curr_val}", curr_val)
                    c.setCurrentIndex(insert_idx)
                else:
                    c.setCurrentIndex(0)
            elif s.kind in ("choice", "map", "slider"):
                idx = c.findData(val)
                if idx < 0:
                    try:
                        idx = c.findData(int(val))
                    except (ValueError, TypeError):
                        pass
                if idx < 0:
                    idx = c.findData(str(val))
                if idx < 0 and s.kind == "choice":
                    c.addItem(VALUE_LABELS.get(str(val), str(val)), val)
                    idx = c.findData(val)
                elif idx < 0:
                    c.addItem(f"{val} {s.unit}".strip() + " (Personalizado)", val)
                    idx = c.findData(val)
                c.setCurrentIndex(max(idx, 0))
            else:
                if c.text() != str(val):
                    c.setText(str(val))
        finally:
            self._busy = False
        self._update_value_label()
        why = st.disabled_reason(s.key)
        self.control.setEnabled(not why)
        self.lbl.setEnabled(not why)
        self.reason.setText(f"🛡️ {why}" if why else "")
        self.reason.setVisible(bool(why))

    def _update_value_label(self):
        pass
