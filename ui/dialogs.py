"""Modals and dialogs for Scrcpy Studio (Advanced settings search, profiles, Wi-Fi)."""
from __future__ import annotations

from typing import Optional
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QWidget, QFrame, QSizePolicy
)

from .schema import MAIN_SECTIONS, ADV_SECTIONS, Spec
from .state import AppState, DEFAULTS
from .widgets import SettingRow, card, hline
from .theme import C


class AdvancedDialog(QDialog):
    """Full-power settings modal with instant live-search filtering and category chips."""

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self.setWindowTitle("Configuración Avanzada — Scrcpy Studio")
        self.resize(800, 720)
        self.setMinimumSize(640, 520)
        self.setObjectName("root")
        self._active_category: Optional[str] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        # Header
        head = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_h1 = QLabel("Opciones y Parámetros Avanzados")
        lbl_h1.setObjectName("h2")
        lbl_sub = QLabel("Busca y ajusta cualquiera de las opciones nativas de scrcpy con guardián activo.")
        lbl_sub.setObjectName("sub")
        title_box.addWidget(lbl_h1)
        title_box.addWidget(lbl_sub)
        head.addLayout(title_box, 1)

        btn_close = QPushButton("Cerrar")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        head.addWidget(btn_close)
        root.addLayout(head)

        # Search Bar
        search_frame = card("card")
        search_lay = QHBoxLayout(search_frame)
        search_lay.setContentsMargins(12, 6, 12, 6)
        search_lay.setSpacing(8)

        lbl_icon = QLabel("🔍")
        lbl_icon.setStyleSheet("font-size: 16px; background: transparent;")
        search_lay.addWidget(lbl_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filtrar por nombre, bandera scrcpy o palabra clave (ej. fps, rotación, encoder, audio, otg...)")
        self.search_input.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        self.search_input.textChanged.connect(self._apply_filter)
        search_lay.addWidget(self.search_input, 1)

        btn_clear = QPushButton("✕")
        btn_clear.setObjectName("ghost")
        btn_clear.setFixedWidth(28)
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.clicked.connect(self.search_input.clear)
        search_lay.addWidget(btn_clear)
        root.addWidget(search_frame)

        # Category Filter Chips Row
        chips_frame = QWidget()
        chips_lay = QHBoxLayout(chips_frame)
        chips_lay.setContentsMargins(0, 0, 0, 0)
        chips_lay.setSpacing(6)

        categories_chips = [
            ("Todas", None),
            ("⚡ Vídeo", "vídeo"),
            ("🎵 Audio", "audio"),
            ("🎮 Entrada", "entrada"),
            ("📷 Cámara", "cámara"),
            ("🪟 Virtual", "virtual"),
            ("🖥️ Ventana", "ventana"),
            ("⏺️ Grabación", "grabación"),
            ("🔌 Conexión", "conexión"),
        ]

        self._chip_buttons: list[tuple[QPushButton, Optional[str]]] = []
        for label, cat_key in categories_chips:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            if cat_key is None:
                btn.setChecked(True)
                btn.setStyleSheet(f"border: 1px solid {C['cyan']}; background: {C['cardHover']}; color: {C['cyan']}; font-weight: bold; padding: 4px 10px; border-radius: 6px;")
            else:
                btn.setStyleSheet(f"border: 1px solid {C['border']}; background: {C['card']}; color: {C['textMuted']}; padding: 4px 10px; border-radius: 6px;")
            btn.clicked.connect(lambda _, k=cat_key, b=btn: self._on_chip_selected(k, b))
            chips_lay.addWidget(btn)
            self._chip_buttons.append((btn, cat_key))

        chips_lay.addStretch()

        # Result count badge
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(f"font-size: 12px; color: {C['textMuted']}; font-weight: 500;")
        chips_lay.addWidget(self.lbl_count)
        root.addWidget(chips_frame)

        # Scroll Area for categories and SettingRows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("root")

        container = QWidget()
        self.container_layout = QVBoxLayout(container)
        self.container_layout.setContentsMargins(4, 8, 8, 8)
        self.container_layout.setSpacing(16)

        self._row_items: list[tuple[QWidget, SettingRow, str, str]] = []  # (category_widget, row, searchable_text, section_title)
        self._categories: list[tuple[QWidget, list[SettingRow], str]] = []

        all_sections = MAIN_SECTIONS + ADV_SECTIONS
        for section_title, specs in all_sections:
            cat_card = card("cardElevated")
            cat_lay = QVBoxLayout(cat_card)
            cat_lay.setContentsMargins(16, 14, 16, 14)
            cat_lay.setSpacing(10)

            # Category Header with Reset Button
            cat_head_lay = QHBoxLayout()
            cat_header = QLabel(f"{section_title.upper()} ({len(specs)})")
            cat_header.setObjectName("eyebrow")
            cat_head_lay.addWidget(cat_header)
            cat_head_lay.addStretch()

            btn_reset_cat = QPushButton("↺ Restaurar sección")
            btn_reset_cat.setObjectName("ghost")
            btn_reset_cat.setCursor(Qt.PointingHandCursor)
            btn_reset_cat.setStyleSheet("font-size: 11px; padding: 2px 8px;")
            btn_reset_cat.setToolTip(f"Restaurar las {len(specs)} opciones de {section_title} a sus valores originales recomendados.")
            btn_reset_cat.clicked.connect(lambda _, sps=specs: self._reset_section(sps))
            cat_head_lay.addWidget(btn_reset_cat)
            cat_lay.addLayout(cat_head_lay)

            cat_rows: list[SettingRow] = []
            for spec in specs:
                row = SettingRow(self.state, spec, cat_card)
                cat_lay.addWidget(row)
                searchable = f"{spec.label} {spec.key} {spec.tip} {spec.keywords} {section_title}".lower()
                self._row_items.append((cat_card, row, searchable, section_title.lower()))
                cat_rows.append(row)

            self.container_layout.addWidget(cat_card)
            self._categories.append((cat_card, cat_rows, section_title.lower()))

        self.container_layout.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll, 1)

        self._apply_filter()

    def _reset_section(self, specs_to_reset: list[Spec]):
        """Reset only the given specs in this category to default values."""
        for spec in specs_to_reset:
            if spec.key in DEFAULTS:
                self.state.set(spec.key, DEFAULTS[spec.key])

    def _on_chip_selected(self, cat_key: Optional[str], active_btn: QPushButton):
        self._active_category = cat_key
        for btn, k in self._chip_buttons:
            is_active = (btn == active_btn)
            btn.setChecked(is_active)
            if is_active:
                btn.setStyleSheet(f"border: 1px solid {C['cyan']}; background: {C['cardHover']}; color: {C['cyan']}; font-weight: bold; padding: 4px 10px; border-radius: 6px;")
            else:
                btn.setStyleSheet(f"border: 1px solid {C['border']}; background: {C['card']}; color: {C['textMuted']}; padding: 4px 10px; border-radius: 6px;")
        self._apply_filter()

    def _apply_filter(self):
        query = self.search_input.text().strip().lower()
        active_cat = self._active_category

        total_rows = len(self._row_items)
        visible_rows = 0

        cat_has_visible: dict[QWidget, bool] = {cat: False for cat, _, _ in self._categories}

        for cat_widget, row, text, sec_title in self._row_items:
            # Check category filter
            cat_match = True
            if active_cat:
                cat_match = active_cat in sec_title

            # Check text query
            text_match = True
            if query:
                text_match = query in text

            match = cat_match and text_match
            row.setVisible(match)
            if match:
                cat_has_visible[cat_widget] = True
                visible_rows += 1

        for cat_widget, has_vis in cat_has_visible.items():
            cat_widget.setVisible(has_vis)

        if query or active_cat:
            self.lbl_count.setText(f"Mostrando {visible_rows} de {total_rows} opciones")
        else:
            self.lbl_count.setText(f"{total_rows} opciones disponibles")


class PromptDialog(QDialog):
    """Clean single-input dialog with title and subtext."""

    def __init__(self, title: str, subtitle: str, placeholder: str = "", default_val: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(440, 200)
        self.setObjectName("root")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        lbl_t = QLabel(title)
        lbl_t.setObjectName("h2")
        lbl_s = QLabel(subtitle)
        lbl_s.setObjectName("sub")
        lbl_s.setWordWrap(True)
        lay.addWidget(lbl_t)
        lay.addWidget(lbl_s)

        self.inp = QLineEdit()
        self.inp.setPlaceholderText(placeholder)
        self.inp.setText(default_val)
        lay.addWidget(self.inp)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        self.btn_ok = QPushButton("Aceptar")
        self.btn_ok.setObjectName("primary")
        self.btn_ok.clicked.connect(self.accept)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(self.btn_ok)
        lay.addLayout(btn_box)

    def get_value(self) -> str:
        return self.inp.text().strip()


class PairDeviceDialog(QDialog):
    """Modal for pairing Android 11+ Wireless Debugging."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vincular Dispositivo por Wi-Fi — Scrcpy Studio")
        self.resize(460, 260)
        self.setObjectName("root")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        lbl_t = QLabel("Vincular con Código de Emparejamiento")
        lbl_t.setObjectName("h2")
        lbl_s = QLabel("En tu Android ve a Opciones de Desarrollador → Depuración inalámbrica → Vincular dispositivo con código de vinculación.")
        lbl_s.setObjectName("sub")
        lbl_s.setWordWrap(True)
        lay.addWidget(lbl_t)
        lay.addWidget(lbl_s)

        self.inp_host = QLineEdit()
        self.inp_host.setPlaceholderText("Dirección IP y Puerto (ej: 192.168.1.50:37123)")
        lay.addWidget(self.inp_host)

        self.inp_code = QLineEdit()
        self.inp_code.setPlaceholderText("Código de vinculación de 6 dígitos (ej: 481920)")
        lay.addWidget(self.inp_code)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        self.btn_pair = QPushButton("Vincular")
        self.btn_pair.setObjectName("primary")
        self.btn_pair.clicked.connect(self.accept)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(self.btn_pair)
        lay.addLayout(btn_box)

    def get_data(self) -> tuple[str, str]:
        return self.inp_host.text().strip(), self.inp_code.text().strip()
