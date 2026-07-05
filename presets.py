"""Presets, constants, and theme configuration for ScrcpyGUI."""

# ── Presets ──
PRESETS = {
    "video": {
        "label": "💎 Cine 2K (H.265 Pro)", "desc": "Máxima fidelidad sin lag. Ideal para ver contenido.",
        "badge": "High Quality",
        "codec": "h265", "max_size": 2560, "fps": 60, "bitrate": 24,
        "audio": True, "audio_buffer": 80, "video_buffer": 50,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "audio_codec": "opus", "audio_bitrate": 256,
    },
    "gaming": {
        "label": "🎮 Gaming Pro (120fps/HID)", "desc": "Latencia cero. Optimizado para eSports a 120 Hz.",
        "badge": "eSports Ready",
        "codec": "h264", "max_size": 1920, "fps": 120, "bitrate": 16,
        "audio": True, "audio_buffer": 20, "video_buffer": 0,
        "fullscreen": True, "stay_awake": True, "screen_off": True,
        "keyboard": "uhid", "mouse": "uhid", "gamepad": True,
        "record": False, "record_file": "", "print_fps": True,
        "show_touches": False, "crop": "",
        "audio_codec": "opus", "audio_bitrate": 128,
    },
    "balanced": {
        "label": "⚖️ Inalámbrico (Wi-Fi 6/7)", "desc": "Estable y fluido para uso diario y redes locales.",
        "badge": "Balanced",
        "codec": "h265", "max_size": 1920, "fps": 60, "bitrate": 10,
        "audio": True, "audio_buffer": 80, "video_buffer": 20,
        "fullscreen": False, "stay_awake": True, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "audio_codec": "opus", "audio_bitrate": 96,
    },
    "compatible": {
        "label": "🔋 Modo Compatible", "desc": "Funciona en cualquier dispositivo (Legacy/Batería baja).",
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
        "label": "👔 Presentación / Demo", "desc": "Muestra tus toques en pantalla. Ideal para tutoriales.",
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
        "label": "🔌 Modo OTG Puro", "desc": "Sin video/audio. Solo control de hardware por USB.",
        "badge": "Hardware",
        "codec": "h264", "max_size": 1280, "fps": 30, "bitrate": 4,
        "audio": False, "audio_buffer": 50, "video_buffer": 0,
        "fullscreen": False, "stay_awake": False, "screen_off": False,
        "keyboard": "", "mouse": "", "gamepad": False,
        "record": False, "record_file": "", "print_fps": False,
        "show_touches": False, "crop": "",
        "otg_mode": True,
    },
}

# ── Dropdown values ──
VIRTUAL_RES_PRESETS = ["1920x1080", "1280x720", "2560x1440", "3840x2160", "720x1280 (Portrait)", "1080x1920 (Portrait)", "Personalizada"]

AUDIO_SOURCES = ["output", "playback", "mic", "mic-unprocessed", "mic-camcorder",
                 "mic-voice-recognition", "mic-voice-communication",
                 "voice-call", "voice-call-uplink", "voice-call-downlink", "voice-performance"]
AUDIO_CODECS = ["opus", "aac", "flac", "raw"]
KEYBOARD_MODES = ["", "sdk", "uhid", "aoa", "disabled"]
MOUSE_MODES = ["", "sdk", "uhid", "aoa", "disabled"]
GAMEPAD_MODES = ["", "uhid", "aoa", "disabled"]
ORIENTATION_VALUES = ["0", "90", "180", "270", "flip0", "flip90", "flip180", "flip270"]
CAMERA_FACING = ["", "front", "back", "external"]

# ── Theme ──
COLORS = {
    "bg": "#0f1219", "card": "#1a1f2e", "card_hover": "#232a3d", "border": "#2a3146",
    "accent": "#22d3ee", "purple": "#a78bfa", "green": "#34d399", "orange": "#fb923c",
    "text": "#f1f5f9", "text2": "#94a3b8", "muted": "#64748b", "danger": "#ef4444",
}

MODE_COLORS = {
    "video": "#22d3ee", "gaming": "#a78bfa", "balanced": "#34d399", "compatible": "#f472b6",
    "present": "#fde047", "otg": "#f87171", "custom": "#fb923c",
}
