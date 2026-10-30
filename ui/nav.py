"""Navigation-level widgets: left rail button and elided label."""
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QFontMetrics
from PySide6.QtWidgets import QAbstractButton, QLabel, QSizePolicy

from .theme import C
from .widgets import _gradient


class RailButton(QAbstractButton):
    """Left navigation rail item: emoji icon + small caption."""

    def __init__(self, icon: str, caption: str, parent=None):
        super().__init__(parent)
        self._icon, self._caption = icon, caption
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(76, 64)
        self.setToolTip(caption)
        self.setAccessibleName(caption)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(4, 2, -4, -2)
        if self.isChecked():
            p.setBrush(QColor(C["elevated"]))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(r, 12, 12)
            ind = QRectF(0, 16, 3, 32)
            p.setBrush(QBrush(_gradient(ind)))
            p.drawRoundedRect(ind, 1.5, 1.5)
        elif self.underMouse():
            p.setBrush(QColor(C["hover"]))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(r, 12, 12)
        if self.hasFocus():
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(C["cyan"]), 1))
            p.drawRoundedRect(r, 12, 12)
        p.setFont(QFont("Segoe UI Emoji", 15))
        p.setPen(QColor(C["text"] if self.isChecked() else C["text2"]))
        p.drawText(QRectF(0, 6, self.width(), 28), Qt.AlignHCenter | Qt.AlignVCenter, self._icon)
        f2 = QFont("Segoe UI", 8)
        f2.setBold(self.isChecked())
        p.setFont(f2)
        p.setPen(QColor(C["cyan"] if self.isChecked() else C["text2"]))
        p.drawText(QRectF(0, 36, self.width(), 20), Qt.AlignHCenter | Qt.AlignVCenter, self._caption)

    def enterEvent(self, e):
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.update()
        super().leaveEvent(e)


class ElidedLabel(QLabel):
    """Single-line label that truncates with an ellipsis and keeps a tooltip."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._full = ""
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setText(text)

    def setText(self, text: str):
        self._full = text
        self.setToolTip(text)
        self._elide()

    def full_text(self) -> str:
        return self._full

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._elide()

    def _elide(self):
        fm = QFontMetrics(self.font())
        QLabel.setText(self, fm.elidedText(self._full, Qt.ElideRight, max(self.width() - 4, 40)))
