"""Presets, constants, and theme configuration for ScrcpyGUI.

This module centralises all static data used by the application:
- **PRESETS**: Predefined configuration profiles optimised for specific use
  cases (cinema, gaming, desktop/dex, wireless, streaming, vp9, etc.).
- **Dropdown value lists**: ``VIDEO_CODECS``, ``VIRTUAL_RES_PRESETS``, ``AUDIO_SOURCES``, etc.
- **COLORS / MODE_COLORS**: The colour palette for the dark theme.
"""

# ── Presets ──
PRESETS = {
    "desktop": {
        "label": "🖥️ Modo Escritorio (DeX)",
        "desc": "Pantalla virtual 1080p independiente, DPI tablet y control UHID nativo.",
        "badge": "Workstation",
        "codec": "h264", "max_size": 1920, "fps": 60, "bitrate": 16,
        "audio": True, "audio_buffer": 30, "video_buffer": 0,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "uhid", "mouse": "uhid", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "audio_codec": "aac", "audio_bitrate": 128,
        "virtual_display": True,
        "virtual_display_res": "1920x1080",
        "virtual_dpi": "220",
    },
    "virtual_app": {
        "label": "🚀 App en Pantalla Virtual",
        "desc": "Abre una app específica de tu móvil en una ventana secundaria aislada y redimensionable.",
        "badge": "App Monitor",
        "codec": "h264", "max_size": 1920, "fps": 60, "bitrate": 16,
        "audio": True, "audio_buffer": 30, "video_buffer": 0,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "uhid", "mouse": "uhid", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "audio_codec": "aac", "audio_bitrate": 128,
        "virtual_display": True,
        "virtual_display_res": "1920x1080",
        "virtual_dpi": "220",
        "flex_display": True,
        "prompt_app": True,
    },
    "gaming": {
        "label": "🎮 Gaming Pro (120fps/HID)",
        "desc": "Latencia cero. Optimizado para eSports a 120 Hz.",
        "badge": "eSports Ready",
        "codec": "h264", "max_size": 1920, "fps": 120, "bitrate": 16,
        "audio": True, "audio_buffer": 20, "video_buffer": 0,
        "fullscreen": True, "stay_awake": True, "screen_off": True,
        "keyboard": "uhid", "mouse": "uhid", "gamepad": True,
        "record": False, "record_file": "", "print_fps": True,
        "show_touches": False, "crop": "",
        "audio_codec": "opus", "audio_bitrate": 128,
    },
    "video": {
        "label": "💎 Cine 2K (H.265 Pro)",
        "desc": "Máxima fidelidad sin lag. Ideal para ver contenido.",
        "badge": "High Quality",
        "codec": "h265", "max_size": 2560, "fps": 60, "bitrate": 24,
        "audio": True, "audio_buffer": 80, "video_buffer": 50,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "audio_codec": "opus", "audio_bitrate": 256,
    },
    "balanced": {
        "label": "⚖️ Inalámbrico (Wi-Fi 6/7)",
        "desc": "Estable y fluido para uso diario y redes locales.",
        "badge": "Balanced",
        "codec": "h265", "max_size": 1920, "fps": 60, "bitrate": 10,
        "audio": True, "audio_buffer": 80, "video_buffer": 20,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "audio_codec": "opus", "audio_bitrate": 96,
    },
    "streamer": {
        "label": "🎙️ Stream / OBS Pro",
        "desc": "Captura limpia sin retorno de audio local para OBS o streaming.",
        "badge": "Broadcast",
        "codec": "h264", "max_size": 1920, "fps": 60, "bitrate": 20,
        "audio": True, "audio_buffer": 30, "video_buffer": 0,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "audio_codec": "opus", "audio_bitrate": 256,
        "no_audio_playback": True,
    },
    "vp9": {
        "label": "⚡ Ultra VP9 (v4.1)",
        "desc": "Máxima eficiencia y bajo consumo usando códec VP9.",
        "badge": "VP9 Modern",
        "codec": "vp9", "max_size": 1600, "fps": 60, "bitrate": 8,
        "audio": True, "audio_buffer": 50, "video_buffer": 20,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "audio_codec": "opus", "audio_bitrate": 96,
    },
    "vp8": {
        "label": "⚡ Ultra VP8 (v4.1)",
        "desc": "Streaming ultraligero y de baja carga de CPU usando el códec libre VP8.",
        "badge": "VP8 Fast",
        "codec": "vp8", "max_size": 1600, "fps": 60, "bitrate": 8,
        "audio": True, "audio_buffer": 50, "video_buffer": 20,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "audio_codec": "opus", "audio_bitrate": 96,
    },
    "compatible": {
        "label": "🔋 Modo Compatible",
        "desc": "Funciona en cualquier dispositivo (Legacy/Batería baja).",
        "badge": "Max Compatibility",
        "codec": "h264", "max_size": 1280, "fps": 30, "bitrate": 4,
        "audio": True, "audio_buffer": 100, "video_buffer": 30,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "sdk", "mouse": "sdk", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "audio_codec": "opus", "audio_bitrate": 64,
    },
    "present": {
        "label": "👔 Presentación / Demo",
        "desc": "Muestra tus toques en pantalla. Ideal para tutoriales.",
        "badge": "Work",
        "codec": "h264", "max_size": 1920, "fps": 30, "bitrate": 8,
        "audio": True, "audio_buffer": 50, "video_buffer": 0,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": True, "crop": "",
        "keep_active": True,
    },
    "otg": {
        "label": "🔌 Modo OTG Puro",
        "desc": "Sin video/audio. Solo control de hardware por USB (teclado/ratón).",
        "badge": "Hardware",
        "codec": "h264", "max_size": 1280, "fps": 30, "bitrate": 4,
        "audio": False, "audio_buffer": 50, "video_buffer": 0,
        "fullscreen": False, "stay_awake": False, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "otg_mode": True,
    },
    "otg_audio": {
        "label": "🎵 OTG + Audio (UHID)",
        "desc": "Control nativo por hardware (teclado/ratón) con streaming de audio a PC y sin video.",
        "badge": "Audio + HID",
        "codec": "h264", "max_size": 1280, "fps": 30, "bitrate": 4,
        "audio": True, "audio_buffer": 40, "video_buffer": 0,
        "audio_codec": "opus", "audio_bitrate": 128,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "uhid", "mouse": "uhid", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "otg_mode": True,
    },
}

# ── Dropdown values ──
VIDEO_CODECS = ["h264", "h265", "av1", "vp9", "vp8"]
"""Supported video codecs in scrcpy v4.1."""

VIRTUAL_RES_PRESETS = [
    "1920x1080", "1280x720", "2560x1440", "3840x2160",
    "720x1280 (Portrait)", "1080x1920 (Portrait)", "Personalizada",
]
"""Resolution presets for virtual display creation."""

AUDIO_SOURCES = [
    "output", "playback", "mic", "mic-unprocessed", "mic-camcorder",
    "mic-voice-recognition", "mic-voice-communication",
    "voice-call", "voice-call-uplink", "voice-call-downlink",
    "voice-performance",
]
"""Valid values for scrcpy ``--audio-source``."""

AUDIO_CODECS = ["opus", "aac", "flac", "raw"]
"""Valid values for scrcpy ``--audio-codec``."""

KEYBOARD_MODES = ["", "sdk", "uhid", "aoa", "disabled"]
"""Keyboard input modes. Empty string means scrcpy default."""

MOUSE_MODES = ["", "sdk", "uhid", "aoa", "disabled"]
"""Mouse input modes. Empty string means scrcpy default."""

GAMEPAD_MODES = ["", "uhid", "aoa", "disabled"]
"""Gamepad input modes. Empty string means no gamepad forwarding."""

ORIENTATION_VALUES = ["0", "90", "180", "270", "flip0", "flip90", "flip180", "flip270"]
"""Display orientation options (degrees or flipped variants)."""

CAMERA_FACING = ["", "front", "back", "external"]
"""Camera facing direction for ``--camera-facing``."""

# ── Theme ──
COLORS = {
    "bg": "#0f1219",           # Main background
    "card": "#1a1f2e",         # Card / panel background
    "card_hover": "#232a3d",   # Card hover state
    "border": "#2a3146",       # Borders and dividers
    "accent": "#22d3ee",       # Primary accent (cyan)
    "purple": "#a78bfa",       # Secondary accent (purple)
    "green": "#34d399",        # Success / positive states
    "orange": "#fb923c",       # Warning / brand highlight
    "text": "#f1f5f9",         # Primary text
    "text2": "#94a3b8",        # Secondary text
    "muted": "#64748b",        # Muted / disabled text
    "danger": "#ef4444",       # Error / destructive actions
}
"""Dark theme colour palette used across the entire UI."""

MODE_COLORS = {
    "desktop": "#06b6d4",
    "virtual_app": "#38bdf8",
    "gaming": "#a78bfa",
    "video": "#22d3ee",
    "balanced": "#34d399",
    "streamer": "#e879f9",
    "vp9": "#38bdf8",
    "vp8": "#2dd4bf",
    "compatible": "#f472b6",
    "present": "#fde047",
    "otg": "#f87171",
    "otg_audio": "#ec4899",
    "custom": "#fb923c",
}
"""Accent colour for each mode card's border highlight."""
