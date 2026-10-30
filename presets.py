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
        "flex_display": True,
        "virtual_mouse": True,
        "video_source": "display", "no_control": False,
    },
    "virtual": {
        "label": "📱 App en Ventana (Virtual)",
        "desc": "Abre una pantalla virtual secundaria aislada y redimensionable.",
        "badge": "Virtual Window",
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
        "virtual_mouse": True,
        "start_app_force_stop": True,
        "video_source": "display", "no_control": False,
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
        "virtual_mouse": True,
        "start_app_force_stop": True,
        "video_source": "display", "no_control": False,
    },
    "gaming": {
        "label": "🎮 Gaming Pro (120fps/HID)",
        "desc": "Latencia cero. Optimizado para eSports a 120 Hz.",
        "badge": "eSports Ready",
        "codec": "h264", "max_size": 1920, "fps": 120, "bitrate": 16,
        "audio": True, "audio_buffer": 20, "video_buffer": 0,
        "fullscreen": True, "stay_awake": True, "screen_off": False,
        "keyboard": "uhid", "mouse": "uhid", "gamepad": True,
        "record": False, "record_file": "", "print_fps": True,
        "show_touches": False, "crop": "",
        "audio_codec": "opus", "audio_bitrate": 128,
        "hwdec": "auto",
        "video_source": "display", "virtual_display": False, "no_control": False,
    },
    "record": {
        "label": "🔴 Grabar Pantalla",
        "desc": "Captura directa a video MP4 Full HD a 60 FPS con audio de alta fidelidad.",
        "badge": "HD Recording",
        "codec": "h264", "max_size": 1920, "fps": 60, "bitrate": 16,
        "audio": True, "audio_buffer": 50, "video_buffer": 0,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "sdk", "mouse": "sdk", "gamepad": False,
        "record": True, "record_file": "captura_%Y%m%d_%H%M%S.mp4", "record_format": "mp4",
        "print_fps": False, "show_touches": False, "crop": "",
        "audio_codec": "aac", "audio_bitrate": 128,
        "no_video_playback": False, "no_audio_playback": False,
        "time_limit": 0,
        "video_source": "display", "virtual_display": False, "no_control": False,
    },
    "camera": {
        "label": "📷 Cámara Web Pro",
        "desc": "Transmite la cámara del móvil a tu PC en Full HD como cámara web.",
        "badge": "Webcam Pro",
        "video_source": "camera",
        "camera_facing": "back",
        "camera_size": "1920x1080",
        "camera_fps": 30,
        "codec": "h264", "max_size": 0, "fps": 30, "bitrate": 16,
        "audio": False, "audio_buffer": 0, "video_buffer": 0,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "no_control": True,
        "hwdec": "auto",
        "virtual_display": False,
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
        "hwdec": "auto",
        "video_source": "display", "virtual_display": False,
    },
    "balanced": {
        "label": "🚀 Espejo Rápido",
        "desc": "Estable y fluido para uso diario, control táctil y redes locales.",
        "badge": "Balanced",
        "codec": "h264", "max_size": 1920, "fps": 60, "bitrate": 12,
        "audio": True, "audio_buffer": 50, "video_buffer": 0,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "sdk", "mouse": "sdk", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "audio_codec": "opus", "audio_bitrate": 96,
        "video_source": "display", "virtual_display": False, "no_control": False,
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
    # ─── Phase 3 Presets (v1.4.0) ───────────────────────────────────────────────
    "headless_record": {
        "label": "🎥 Grabación Headless",
        "desc": "Graba el móvil sin ventana en PC. Ideal para capturas automáticas desatendidas.",
        "badge": "Stealth Capture",
        "codec": "h264", "max_size": 1920, "fps": 60, "bitrate": 16,
        "audio": True, "audio_buffer": 50, "video_buffer": 0,
        "fullscreen": False, "stay_awake": True, "screen_off": True,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": True, "record_file": "captura_%Y%m%d_%H%M%S.mp4", "print_fps": False,
        "show_touches": False, "crop": "",
        "audio_codec": "opus", "audio_bitrate": 128,
        "no_video_playback": True,
        "no_audio_playback": True,
        "require_audio": False,
    },
    "camera_doc": {
        "label": "📷 Cámara Documento",
        "desc": "Escáner en vivo con cámara trasera. Sin audio, sin control, sin escalar.",
        "badge": "Scanner",
        "codec": "h264", "max_size": 0, "fps": 30, "bitrate": 12,
        "audio": False, "audio_buffer": 50, "video_buffer": 0,
        "fullscreen": False, "stay_awake": False, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "video_source": "camera",
        "camera_facing": "back",
        "no_control": True,
        "render_fit": "unscaled",
    },
    "multimonitor": {
        "label": "🖥️ Multi-Monitor",
        "desc": "Coloca scrcpy en el segundo monitor (posición X=1920, Y=0) en pantalla completa.",
        "badge": "Dual Screen",
        "codec": "h264", "max_size": 1920, "fps": 60, "bitrate": 12,
        "audio": True, "audio_buffer": 50, "video_buffer": 0,
        "fullscreen": True, "stay_awake": True, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "window_x": "1920",
        "window_y": "0",
    },
    "gaming_competitive": {
        "label": "🕹️ Competitivo (sin shortcuts)",
        "desc": "Gaming sin interferencia de atajos. MOD cambiado a RCtrl para no conflictar.",
        "badge": "No Interference",
        "codec": "h264", "max_size": 1920, "fps": 120, "bitrate": 16,
        "audio": True, "audio_buffer": 20, "video_buffer": 0,
        "fullscreen": True, "stay_awake": True, "screen_off": True,
        "keyboard": "uhid", "mouse": "uhid", "gamepad": True,
        "record": False, "record_file": "", "print_fps": True,
        "show_touches": False, "crop": "",
        "audio_codec": "opus", "audio_bitrate": 128,
        "shortcut_mod": "rctrl",
        "no_key_repeat": False,
    },
    "mirror_readonly": {
        "label": "👁️ Mirror Solo Lectura",
        "desc": "Espejado sin control. Ideal para presentaciones, soporte remoto o tutoriales.",
        "badge": "Viewer",
        "codec": "h264", "max_size": 1920, "fps": 30, "bitrate": 8,
        "audio": True, "audio_buffer": 80, "video_buffer": 20,
        "fullscreen": False, "stay_awake": False, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "no_control": True,
        "render_fit": "letterbox",
        "keep_active": False,
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

# ── New in v1.4.0 (Phase 1 + Phase 2) ──
RENDER_FIT_VALUES = ["", "letterbox", "stretched", "unscaled"]
"""Values for ``--render-fit``. Empty string means scrcpy default (letterbox)."""

RENDER_DRIVER_VALUES = ["", "direct3d", "opengl", "opengles2", "opengles", "metal", "software"]
"""Values for ``--render-driver``."""

RECORD_FORMATS = ["", "mp4", "mkv", "m4a", "mka", "opus", "aac", "flac", "wav"]
"""Values for ``--record-format``."""

# ── New in v1.5.0 (scrcpy 5.0 / 5.0.1) ──
HWDEC_MODES = ["auto", "d3d11va", "disabled", "vaapi", "videotoolbox"]
"""Hardware decoding modes for ``--hwdec`` (scrcpy 5.0+)."""

RECORD_ORIENTATION_VALUES = ["", "0", "90", "180", "270"]
"""Values for ``--record-orientation`` (scrcpy 5.0+)."""

MIN_SIZE_ALIGNMENT_VALUES = ["", "2", "4", "8", "16", "32"]
"""Values for ``--min-size-alignment`` (scrcpy 5.0+)."""

CAPTURE_ORIENTATION_VALUES = ["0", "90", "180", "270", "flip0", "flip90", "flip180", "flip270", "@", "@90", "@180", "@270"]
"""Values for ``--capture-orientation`` (scrcpy 4.0+)."""

DISPLAY_ORIENTATION_VALUES = ["0", "90", "180", "270", "flip0", "flip90", "flip180", "flip270"]
"""Values for ``--display-orientation``."""

IME_POLICY_VALUES = ["", "local", "fallback", "hide"]
"""Values for ``--display-ime-policy``."""

VERBOSITY_LEVELS = ["", "verbose", "debug", "info", "warn", "error"]
"""Values for ``--verbosity``."""

PAUSE_ON_EXIT_VALUES = ["", "false", "true", "if-error"]
"""Values for ``--pause-on-exit``."""

CAMERA_AR_VALUES = ["", "sensor", "4:3", "16:9", "1:1", "3:2", "21:9"]
"""Common aspect ratio values for ``--camera-ar``."""

# ── Theme ──
COLORS = {
    "bg": "#0b0e14",           # Main background (rich deep slate)
    "card": "#151923",         # Card / panel background (elevation 1)
    "card_hover": "#1e2433",   # Card hover state (elevation 2)
    "border": "#232a3b",       # Borders and dividers (subtle, clean)
    "accent": "#38bdf8",       # Primary accent (sky blue, high contrast)
    "accent_hover": "#0ea5e9", # Primary accent hover
    "purple": "#a78bfa",       # Secondary accent (purple)
    "green": "#34d399",        # Success / positive states
    "orange": "#fb923c",       # Warning / brand highlight
    "text": "#f8fafc",         # Primary text (high contrast AAA)
    "text2": "#cbd5e1",        # Secondary text (WCAG AA compliant 5.8:1)
    "muted": "#94a3b8",        # Muted / metadata text (legible 4.5:1)
    "danger": "#f43f5e",       # Modern coral red
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
    # Phase 3 presets
    "headless_record": "#f43f5e",
    "camera_doc": "#84cc16",
    "multimonitor": "#0ea5e9",
    "gaming_competitive": "#c084fc",
    "mirror_readonly": "#94a3b8",
    "virtual": "#a855f7",
    "record": "#ef4444",
    "camera": "#06b6d4",
    "custom": "#fb923c",
}
"""Accent colour for each mode card's border highlight."""

PRESET_CATEGORIES = {
    "popular": {
        "title": "⚡ POPULARES & ESENCIALES",
        "keys": ["desktop", "virtual", "virtual_app", "gaming", "video", "balanced"],
    },
    "gaming": {
        "title": "🎮 GAMING & ESPORTS",
        "keys": ["gaming_competitive", "streamer", "vp9"],
    },
    "special": {
        "title": "📱 CAPTURA & ESPECIALES",
        "keys": ["record", "camera", "headless_record", "camera_doc", "multimonitor", "mirror_readonly", "compatible", "present", "vp8"],
    },
    "hardware": {
        "title": "🔌 HARDWARE & OTG",
        "keys": ["otg", "otg_audio"],
    },
}
"""Categories for organizing the sidebar presets gracefully."""

