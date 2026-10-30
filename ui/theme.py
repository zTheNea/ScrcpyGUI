"""Design tokens + global stylesheet for Scrcpy Studio (UI/UX Pro Max)."""

C = {
    "bg": "#080B11",             # Deep abyss black
    "surface": "#0F1626",        # Slate dark surface
    "elevated": "#151F36",       # Card elevation & interactive surface
    "hover": "#1D2B4A",          # Hover state
    "border": "#1E2A42",         # Subtle clean border
    "border_strong": "#2D3E64",  # High contrast border
    "text": "#F8FAFC",           # Pure crisp white (> 16:1 contrast)
    "text2": "#94A3B8",          # Secondary text (> 7:1 WCAG AAA)
    "muted": "#64748B",          # Tertiary / hint text
    "cyan": "#06B6D4",           # Vibrant tech cyan
    "cyan_bright": "#22D3EE",
    "indigo": "#6366F1",         # Electric indigo
    "indigo_bright": "#818CF8",
    "success": "#10B981",        # Emerald green
    "warning": "#F59E0B",        # Amber gold
    "danger": "#F43F5E",         # Rose red
    "purple": "#A855F7",         # Purple accent
}
# Convenience semantic aliases
C["amber"] = C["warning"]
C["emerald"] = C["success"]
C["red"] = C["danger"]
C["card"] = C["surface"]
C["cardElevated"] = C["elevated"]
C["cardHover"] = C["hover"]
C["textMuted"] = C["muted"]

RADIUS_CARD = 14
RADIUS_CTRL = 10

FONT = "Segoe UI"



def stylesheet() -> str:
    c = C
    return f"""
* {{ font-family: '{FONT}', 'Inter', system-ui, -apple-system, sans-serif; font-size: 13px; color: {c['text']}; }}
QMainWindow, QDialog, QWidget#root {{ background: {c['bg']}; }}
QWidget {{ background: transparent; }}
QToolTip {{ background: {c['elevated']}; color: {c['text']}; border: 1px solid {c['cyan']};
           padding: 6px 10px; border-radius: 8px; font-size: 12px; }}

/* Navigation Rail */
QFrame#rail {{ background: {c['surface']}; border-right: 1px solid {c['border']}; }}
QToolButton#railBtn {{ background: transparent; border: none; border-radius: 12px; color: {c['text2']};
    padding: 10px 4px; font-size: 11px; min-width: 64px; }}
QToolButton#railBtn:hover {{ background: {c['hover']}; color: {c['text']}; }}
QToolButton#railBtn:checked {{ background: {c['elevated']}; color: {c['cyan_bright']}; font-weight: 700; border-left: 3px solid {c['cyan']}; }}
QToolButton#railBtn:focus {{ border: 1px solid {c['cyan']}; }}

/* Cards & Bento Grid */
QFrame#card {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: {RADIUS_CARD}px; }}
QFrame#card:hover {{ border-color: {c['border_strong']}; }}
QFrame#cardElevated {{ background: {c['elevated']}; border: 1px solid {c['border']}; border-radius: {RADIUS_CARD}px; }}
QFrame#deviceCard {{ border: 1px solid {c['border_strong']}; border-radius: {RADIUS_CARD}px;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #111E36, stop:1 #171B38); }}
QFrame#actionBar {{ background: {c['surface']}; border: 1px solid {c['border_strong']}; border-radius: 16px; }}
QFrame#inspector {{ background: {c['surface']}; border-left: 1px solid {c['border']}; }}
QFrame#console {{ background: #06080E; border-top: 1px solid {c['border']}; }}

/* Typography */
QLabel#h1 {{ font-size: 24px; font-weight: 700; color: {c['text']}; letter-spacing: -0.3px; }}
QLabel#h2 {{ font-size: 15px; font-weight: 600; color: {c['text']}; }}
QLabel#eyebrow {{ font-size: 11px; font-weight: 700; color: {c['cyan_bright']}; letter-spacing: 1.2px; }}
QLabel#sub {{ color: {c['text2']}; font-size: 12px; }}
QLabel#muted {{ color: {c['muted']}; font-size: 12px; }}
QLabel#mono {{ font-family: Consolas, 'Cascadia Mono', 'Courier New', monospace; font-size: 12px; }}
QLabel#warn {{ color: {c['warning']}; font-size: 12px; }}
QLabel#sectionTitle {{ font-size: 11px; font-weight: 700; color: {c['text2']}; letter-spacing: 0.8px; }}

/* Buttons */
QPushButton {{ background: {c['elevated']}; border: 1px solid {c['border']}; border-radius: {RADIUS_CTRL}px;
    padding: 0 16px; min-height: 38px; color: {c['text']}; font-weight: 500; }}
QPushButton:hover {{ background: {c['hover']}; border-color: {c['border_strong']}; color: {c['text']}; }}
QPushButton:focus {{ border: 1px solid {c['cyan']}; }}
QPushButton:disabled {{ color: {c['muted']}; background: {c['surface']}; border-color: {c['border']}; }}

/* Primary CTA Button */
QPushButton#primary {{ border: none; font-weight: 700; font-size: 14px; color: #040812; min-height: 44px;
    border-radius: 12px; padding: 0 24px;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {c['cyan_bright']}, stop:1 {c['indigo_bright']}); }}
QPushButton#primary:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #67E8F9, stop:1 #A5B4FC); }}
QPushButton#primary:pressed {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {c['cyan']}, stop:1 {c['indigo']}); }}
QPushButton#primary:disabled {{ background: {c['elevated']}; color: {c['muted']}; border: 1px solid {c['border']}; }}

/* Danger Button */
QPushButton#danger {{ background: rgba(244,63,94,0.12); border: 1px solid {c['danger']}; color: {c['danger']}; font-weight: 600; }}
QPushButton#danger:hover {{ background: rgba(244,63,94,0.24); }}

/* Ghost Button */
QPushButton#ghost {{ background: transparent; border: none; color: {c['cyan_bright']}; padding: 0 10px; min-height: 32px; font-weight: 500; }}
QPushButton#ghost:hover {{ color: #A5F3FC; background: rgba(6,182,212,0.12); border-radius: 8px; }}

/* Status Chips */
QPushButton#chip {{ background: {c['elevated']}; border: 1px solid {c['border']}; border-radius: 999px;
    min-height: 28px; padding: 0 12px; font-size: 11px; font-weight: 600; color: {c['text2']}; }}
QPushButton#chip:hover {{ border-color: {c['cyan']}; color: {c['cyan_bright']}; background: {c['hover']}; }}

/* Form Controls & Inputs */
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {{ background: {c['elevated']}; border: 1px solid {c['border']};
    border-radius: {RADIUS_CTRL}px; padding: 0 12px; min-height: 36px; selection-background-color: {c['indigo']}; color: {c['text']}; }}
QPlainTextEdit {{ padding: 8px 12px; font-family: Consolas, monospace; font-size: 12px; color: {c['success']}; }}
QLineEdit:hover, QComboBox:hover {{ border-color: {c['border_strong']}; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border: 1px solid {c['cyan']}; }}
QLineEdit:disabled, QComboBox:disabled {{ color: {c['muted']}; background: {c['surface']}; }}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox QAbstractItemView {{ background: {c['surface']}; border: 1px solid {c['border_strong']};
    border-radius: 8px; selection-background-color: {c['hover']}; outline: none; padding: 4px; }}

/* Sliders */
QSlider::groove:horizontal {{ height: 6px; background: {c['border']}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {c['cyan']}, stop:1 {c['indigo']}); border-radius: 3px; }}
QSlider::handle:horizontal {{ width: 18px; height: 18px; margin: -6px 0; border-radius: 9px; background: {c['text']}; border: 2px solid {c['cyan']}; }}
QSlider::handle:horizontal:hover {{ background: {c['cyan_bright']}; }}
QSlider:disabled::sub-page:horizontal {{ background: {c['border_strong']}; }}

/* Scrollbars */
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {c['border_strong']}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {c['cyan']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar:horizontal {{ height: 0; }}

/* List Widget & Toasts */
QListWidget {{ background: transparent; border: none; outline: none; }}
QListWidget::item {{ background: {c['elevated']}; border: 1px solid {c['border']}; border-radius: 10px;
    padding: 10px 12px; margin: 3px 0; }}
QListWidget::item:hover {{ border-color: {c['cyan']}; background: {c['hover']}; }}
QListWidget::item:selected {{ border-color: {c['cyan']}; background: rgba(6,182,212,0.15); color: {c['text']}; }}
QFrame#sep {{ background: {c['border']}; max-height: 1px; min-height: 1px; }}
QFrame#toast {{ background: {c['elevated']}; border: 1px solid {c['border_strong']}; border-radius: 12px; }}
"""

