"""Declarative catalogue of every scrcpy option exposed in the UI.

One schema drives the compact *Inspector* (``MAIN_SECTIONS``) and the
searchable *Advanced* dialog (``ADV_SECTIONS``). Nothing from the old GUI is
lost: each ``v_<key>`` exists in ``ui.state`` and ``config_manager``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from presets import (
    VIDEO_CODECS, AUDIO_SOURCES, AUDIO_CODECS, KEYBOARD_MODES, MOUSE_MODES,
    GAMEPAD_MODES, ORIENTATION_VALUES, CAMERA_FACING, RENDER_FIT_VALUES,
    RENDER_DRIVER_VALUES, RECORD_FORMATS, HWDEC_MODES, RECORD_ORIENTATION_VALUES,
    MIN_SIZE_ALIGNMENT_VALUES, CAPTURE_ORIENTATION_VALUES, DISPLAY_ORIENTATION_VALUES,
    IME_POLICY_VALUES, VERBOSITY_LEVELS, PAUSE_ON_EXIT_VALUES, CAMERA_AR_VALUES,
)

RES_MAP = {"Original": "0", "4K (3840)": "3840", "1440p (2560)": "2560",
           "1080p (1920)": "1920", "720p (1280)": "1280", "480p (854)": "854"}
VD_RES = ["1920x1080", "1280x720", "2560x1440", "3840x2160", "720x1280", "1080x1920"]

CAMERA_SIZE_MAP = {
    "1080p Full HD (1920x1080)": "1920x1080",
    "720p HD (1280x720)": "1280x720",
    "4K Ultra HD (3840x2160)": "3840x2160",
    "480p SD (640x480)": "640x480",
}

VIRTUAL_DPI_MAP = {
    "220 (Tablet estándar)": "220",
    "160 (Escritorio compacto / DeX)": "160",
    "280 (Intermedio)": "280",
    "320 (Teléfono grande)": "320",
    "420 (Alta densidad)": "420",
}

VALUE_LABELS = {
    "": "Automático", "uhid": "UHID (hardware nativo)", "sdk": "SDK (estándar)",
    "aoa": "AOA (USB)", "disabled": "Desactivado", "display": "Pantalla",
    "camera": "Cámara", "letterbox": "Letterbox", "stretched": "Estirado",
    "unscaled": "Sin escalar", "auto": "Auto", "d3d11va": "D3D11VA (GPU Windows)",
    "output": "Salida del sistema", "playback": "Reproducción", "mic": "Micrófono",
    "back": "Trasera principal", "front": "Delantera (selfie)",
    "1920x1080": "1080p Full HD (1920x1080)", "1280x720": "720p HD (1280x720)",
    "2560x1440": "1440p 2K (2560x1440)", "3840x2160": "4K Ultra HD (3840x2160)",
    "720x1280": "Vertical 720p (720x1280)", "1080x1920": "Vertical 1080p (1080x1920)",
}


FPS_MAP = {
    "60 FPS (Recomendado)": 60,
    "30 FPS (Ahorro/Estándar)": 30,
    "90 FPS": 90,
    "120 FPS (Gaming)": 120,
    "144 FPS (Ultra)": 144,
    "240 FPS (Extremo)": 240,
    "15 FPS": 15,
}

BITRATE_MAP = {
    "8 Mbps (Recomendado)": 8,
    "4 Mbps (Wi-Fi débil)": 4,
    "12 Mbps": 12,
    "16 Mbps (Alta calidad)": 16,
    "24 Mbps (Ultra HD)": 24,
    "32 Mbps": 32,
    "48 Mbps": 48,
    "64 Mbps (Máximo)": 64,
    "2 Mbps": 2,
    "1 Mbps": 1,
}

AUDIO_BUF_MAP = {
    "50 ms (Estándar USB)": 50,
    "80 ms (Recomendado Wi-Fi)": 80,
    "20 ms (Baja latencia)": 20,
    "10 ms (Cero retraso)": 10,
    "120 ms (Wi-Fi estable)": 120,
    "200 ms (Ultra estable)": 200,
    "0 ms (Mínimo)": 0,
}

VIDEO_BUF_MAP = {
    "0 ms (Tiempo real)": 0,
    "10 ms": 10,
    "20 ms (Bajo)": 20,
    "30 ms (Recomendado Wi-Fi)": 30,
    "50 ms (Estable)": 50,
    "100 ms (Buffer alto)": 100,
}

CAMERA_FPS_MAP = {
    "30 FPS (Estándar)": 30,
    "60 FPS (Fluido)": 60,
    "24 FPS (Cine)": 24,
    "15 FPS": 15,
}

AUDIO_BITRATE_MAP = {
    "128 Kbps (Estándar)": 128,
    "96 Kbps": 96,
    "64 Kbps (Bajo)": 64,
    "192 Kbps (Alta calidad)": 192,
    "256 Kbps": 256,
    "320 Kbps (Máximo)": 320,
}

TIME_LIMIT_MAP = {
    "Sin límite (0s)": 0,
    "30 segundos": 30,
    "1 minuto (60s)": 60,
    "3 minutos (180s)": 180,
    "5 minutos (300s)": 300,
    "10 minutos (600s)": 600,
}

ROTATION_MAP = {
    "0° (Normal)": 0,
    "90° (Derecha)": 90,
    "180° (Invertido)": 180,
    "270° (Izquierda)": 270,
}

SCREEN_OFF_TIMEOUT_MAP = {
    "0 s (Inmediato)": 0,
    "10 s": 10,
    "30 s": 30,
    "60 s (1 min)": 60,
    "300 s (5 min)": 300,
}

AUDIO_OUTPUT_BUF_MAP = {
    "0 ms (Automático)": 0,
    "20 ms": 20,
    "50 ms": 50,
    "100 ms": 100,
    "200 ms": 200,
}

STD_NUM_MAPS: dict[str, dict[str, int]] = {
    "fps": FPS_MAP,
    "bitrate": BITRATE_MAP,
    "audio_buf": AUDIO_BUF_MAP,
    "video_buffer": VIDEO_BUF_MAP,
    "camera_fps": CAMERA_FPS_MAP,
    "audio_bitrate": AUDIO_BITRATE_MAP,
    "time_limit": TIME_LIMIT_MAP,
    "angle": ROTATION_MAP,
    "screen_off_timeout": SCREEN_OFF_TIMEOUT_MAP,
    "audio_output_buf": AUDIO_OUTPUT_BUF_MAP,
}


@dataclass
class Spec:
    key: str
    label: str
    kind: str                 # switch | slider | choice | map | text
    tip: str = ""
    opts: Any = None          # choice list / map dict
    rng: tuple = (0, 100)     # slider range
    unit: str = ""
    placeholder: str = ""
    keywords: str = ""        # extra search terms
    windows_only: bool = False
    linux_only: bool = False


def sw(key, label, tip="", **kw):
    return Spec(key, label, "switch", tip, **kw)


def sl(key, label, lo=None, hi=None, unit="", tip="", opts=None, **kw):
    """Dropdown menu with standard most-used values (replacing slider bars)."""
    options = opts or STD_NUM_MAPS.get(key)
    if options:
        return Spec(key, label, "map", tip, opts=options, unit=unit, **kw)
    lo_val = lo if lo is not None else 0
    hi_val = hi if hi is not None else 100
    step = max(1, (hi_val - lo_val) // 5)
    fallback_opts = {f"{v} {unit}".strip(): v for v in range(lo_val, hi_val + 1, step)}
    return Spec(key, label, "map", tip, opts=fallback_opts, unit=unit, **kw)


def ch(key, label, opts, tip="", **kw):
    return Spec(key, label, "choice", tip, opts=list(opts), **kw)


def tx(key, label, placeholder="", tip="", **kw):
    return Spec(key, label, "text", tip, placeholder=placeholder, **kw)


# ── Inspector (always-visible essentials) ───────────────────────────
MAIN_SECTIONS: list[tuple[str, list[Spec]]] = [
    ("Calidad", [
        Spec("max_size", "Resolución", "map", "Resolución máxima de captura.", opts=RES_MAP),
        sl("fps", "Fotogramas por segundo", 15, 240, "FPS", "60 es fluido; 90-120 para juegos."),
        sl("bitrate", "Bitrate", 1, 64, "Mbps", "Más bitrate = más nitidez y más ancho de banda."),
        ch("codec", "Códec de vídeo", VIDEO_CODECS, "H.264 es el más compatible; H.265/AV1 comprimen mejor."),
    ]),
    ("Audio", [
        sw("audio", "Transmitir audio al PC", "Reenvía el audio del móvil a tus altavoces."),
        sl("audio_buf", "Búfer de audio", 0, 300, "ms", "Bajo = menos latencia; alto = más estable."),
        ch("audio_codec", "Códec de audio", AUDIO_CODECS),
    ]),
    ("Control", [
        sw("no_control", "Solo lectura (solo ver)", "Desactiva teclado, ratón y toques."),
        sw("virtual_mouse", "Ratón virtual (UHID)", "Ratón nativo sin capturar tu puntero."),
        ch("keyboard", "Teclado", KEYBOARD_MODES, "UHID escribe como un teclado USB real."),
        sw("stay_awake", "Mantener móvil despierto", "Evita que el móvil entre en reposo."),
        sw("screen_off", "Apagar pantalla del móvil", "Ahorra batería y calor mientras duplicas."),
        sw("show_touches", "Mostrar toques", "Dibuja un círculo donde tocas."),
    ]),
    ("Ventana", [
        sw("fullscreen", "Pantalla completa"),
        sw("always_on_top", "Siempre al frente"),
        sw("flex_display", "Pantalla flexible", "Cambia la resolución al redimensionar la ventana."),
        sw("virtual_display", "Pantalla virtual", "Crea un monitor secundario en Android."),
    ]),
]

# ── Goal-Specific Contextual Quick Settings ─────────────────────────
GOAL_SECTIONS: dict[str, list[tuple[str, list[Spec]]]] = {
    "camera": [
        ("Cámara Web", [
            ch("camera_facing", "Lente (Frontal/Trasera)", CAMERA_FACING, "Elige qué cámara usar."),
            Spec("camera_size", "Resolución de cámara", "map", "Resolución de streaming del sensor.", opts=CAMERA_SIZE_MAP),
            sl("camera_fps", "FPS de cámara", 15, 60, "FPS", "30 FPS estándar; 60 para máxima fluidez."),
            ch("camera_ar", "Relación de aspecto", CAMERA_AR_VALUES, "16:9 es ideal para videollamadas."),
            tx("camera_id", "ID de cámara", "0", "0 suele ser la trasera principal; 1 la delantera."),
            sw("camera_torch", "Linterna / Flash", "Enciende el flash trasero para iluminarte."),
            sw("camera_high_speed", "Alta velocidad (cámara lenta)"),
            tx("camera_zoom", "Zoom de cámara", "1.0"),
        ]),
        ("Audio de Cámara", [
            sw("audio", "Transmitir micrófono al PC", "Usa el micrófono del móvil como micro de PC."),
            ch("audio_codec", "Códec de audio", AUDIO_CODECS),
            sl("audio_buf", "Búfer de audio", 0, 300, "ms"),
        ]),
        ("Ventana de Cámara", [
            sw("always_on_top", "Siempre al frente", "Mantén la webcam visible sobre tus otras ventanas."),
            sw("fullscreen", "Pantalla completa"),
            sw("borderless", "Ventana sin bordes"),
        ]),
    ],
    "record": [
        ("Grabación de Pantalla", [
            tx("record_file", "Nombre o plantilla", "recording.mp4", "Nombre o ruta del archivo de video."),
            ch("record_format", "Formato de video", RECORD_FORMATS, "mp4 es universal; mkv resiste cortes súbitos."),
            sl("time_limit", "Límite de tiempo", 0, 600, "s", "0 para grabar indefinidamente hasta cerrar."),
            ch("record_orientation", "Orientación de grabación", RECORD_ORIENTATION_VALUES),
            sw("no_playback", "Grabar en segundo plano (sin ventana)", "Graba sin mostrar ventana para ahorrar CPU/GPU."),
        ]),
        ("Calidad de Video", [
            Spec("max_size", "Resolución", "map", "Resolución de captura.", opts=RES_MAP),
            sl("fps", "Fotogramas por segundo", 15, 120, "FPS"),
            sl("bitrate", "Bitrate de video", 4, 64, "Mbps", "Más bitrate = más nitidez."),
            ch("codec", "Códec de video", VIDEO_CODECS),
        ]),
        ("Audio de Grabación", [
            sw("audio", "Grabar audio interno"),
            sw("audio_dup", "Escuchar en PC mientras graba"),
            ch("audio_codec", "Códec de audio", AUDIO_CODECS),
            sl("audio_bitrate", "Bitrate de audio", 64, 320, "K"),
        ]),
    ],
    "virtual": [
        ("Pantalla Virtual", [
            Spec("virtual_display_app", "App a ejecutar", "app", "Selecciona una aplicación instalada en tu móvil para abrirla en su ventana virtual."),
            ch("virtual_display_res", "Resolución virtual", VD_RES, "Resolución de la ventana virtual."),
            Spec("virtual_dpi", "Densidad DPI", "map", "Escala de la interfaz en la ventana.", opts=VIRTUAL_DPI_MAP),
            sw("flex_display", "Pantalla flexible (redimensionable)", "Permite cambiar el tamaño de ventana libremente."),
            sw("start_app_force_stop", "Reinicio limpio (+force-stop)"),
            sw("no_vd_destroy", "Conservar apps al cerrar"),
        ]),
        ("Control y Ratón", [
            sw("virtual_mouse", "Ratón virtual (UHID)", "Ratón independiente sin capturar el puntero."),
            ch("keyboard", "Teclado", KEYBOARD_MODES),
            sw("stay_awake", "Mantener móvil despierto"),
        ]),
        ("Calidad y Ventana", [
            Spec("max_size", "Resolución máxima", "map", opts=RES_MAP),
            sl("fps", "Fotogramas por segundo", 15, 120, "FPS"),
            sl("bitrate", "Bitrate", 1, 32, "Mbps"),
            sw("always_on_top", "Siempre al frente"),
        ]),
    ],
    "desktop": [
        ("Escritorio Virtual", [
            ch("virtual_display_res", "Resolución de escritorio", VD_RES, "Resolución del monitor virtual."),
            Spec("virtual_dpi", "Densidad DPI", "map", "Tamaño de fuentes e iconos.", opts=VIRTUAL_DPI_MAP),
            sw("flex_display", "Pantalla flexible", "Ajusta la resolución al cambiar el tamaño de ventana."),
        ]),
        ("Control de PC", [
            sw("virtual_mouse", "Ratón virtual (UHID)", "Ratón nativo sin capturar tu puntero."),
            ch("keyboard", "Teclado físico", KEYBOARD_MODES, "UHID permite atajos reales como Ctrl+C, Ctrl+V."),
            sw("stay_awake", "Mantener móvil despierto"),
        ]),
        ("Calidad y Ventana", [
            Spec("max_size", "Resolución de pantalla", "map", opts=RES_MAP),
            sl("fps", "Fotogramas por segundo", 30, 120, "FPS"),
            sl("bitrate", "Bitrate", 8, 40, "Mbps"),
            sw("fullscreen", "Pantalla completa"),
            sw("always_on_top", "Siempre al frente"),
        ]),
        ("Audio", [
            sw("audio", "Transmitir audio al PC"),
            sl("audio_buf", "Búfer de audio", 0, 300, "ms"),
        ]),
    ],
    "gaming": [
        ("Rendimiento Gaming", [
            sl("fps", "FPS objetivo", 60, 240, "FPS", "60, 90, 120 o 144 FPS para juegos."),
            sl("bitrate", "Bitrate de video", 8, 64, "Mbps", "16 Mbps o más para cero pixelado."),
            ch("codec", "Códec de video", VIDEO_CODECS, "H.265 ofrece menor latencia y compresión."),
            ch("hwdec", "Aceleración por GPU", [""] + HWDEC_MODES, "Decodificación directa en tu tarjeta gráfica."),
            sl("video_buffer", "Búfer de video", 0, 100, "ms", "0 ms para latencia ultra baja."),
        ]),
        ("Controles de Juego", [
            ch("gamepad", "Mando / Gamepad", GAMEPAD_MODES, "Reenvía mandos USB/Bluetooth al juego."),
            ch("keyboard", "Teclado", KEYBOARD_MODES),
            ch("mouse", "Modo de ratón", MOUSE_MODES),
            sw("stay_awake", "Mantener despierto"),
            sw("screen_off", "Apagar pantalla del móvil", "Ahorra batería mientras juegas en PC."),
        ]),
        ("Audio de Juego", [
            sw("audio", "Transmitir audio del juego"),
            sl("audio_buf", "Búfer de audio", 0, 120, "ms", "Bajo para escuchar pasos y disparos al instante."),
        ]),
        ("Pantalla y Consola", [
            sw("fullscreen", "Pantalla completa"),
            sw("print_fps", "Mostrar FPS en tiempo real en consola"),
        ]),
    ],
    "balanced": MAIN_SECTIONS,
}


def get_goal_sections(goal_id: str) -> list[tuple[str, list[Spec]]]:
    return GOAL_SECTIONS.get(goal_id, MAIN_SECTIONS)

# ── Advanced (searchable) ───────────────────────────────────────────
ADV_SECTIONS: list[tuple[str, list[Spec]]] = [
    ("Vídeo", [
        ch("video_source", "Fuente de vídeo", ["display", "camera"]),
        tx("video_encoder", "Encoder específico", "ej. c2.qti.avc.encoder"),
        ch("render_fit", "Ajuste en ventana", RENDER_FIT_VALUES),
        ch("render_driver", "Driver de render", RENDER_DRIVER_VALUES),
        ch("hwdec", "Decodificación por GPU", [""] + HWDEC_MODES, "Usa tu tarjeta gráfica para decodificar.", keywords="hwdec gpu"),
        sw("ignore_encoder_constraints", "Ignorar límites del encoder"),
        sw("no_video_playback", "Sin reproducción de vídeo local"),
        sw("no_video", "Sin vídeo (solo audio/control)"),
        sl("video_buffer", "Búfer de vídeo", 0, 500, "ms"),
        ch("orientation", "Orientación", ORIENTATION_VALUES),
        ch("capture_orientation", "Orientación de captura", CAPTURE_ORIENTATION_VALUES),
        ch("display_orientation", "Orientación de pantalla", DISPLAY_ORIENTATION_VALUES),
        sl("angle", "Rotación personalizada", 0, 359, "°"),
        tx("crop", "Recorte", "ancho:alto:x:y"),
        tx("display_id", "ID de pantalla", "0 = principal"),
    ]),
    ("Cámara", [
        tx("camera_id", "ID de cámara", "0"),
        ch("camera_facing", "Cámara frontal/trasera", CAMERA_FACING),
        ch("camera_ar", "Relación de aspecto", CAMERA_AR_VALUES),
        tx("camera_size", "Resolución de cámara", "1920x1080"),
        sl("camera_fps", "FPS de cámara", 15, 240, "FPS"),
        sw("camera_torch", "Linterna"),
        sw("camera_high_speed", "Alta velocidad (120fps+)"),
        tx("camera_zoom", "Zoom", "1.0"),
    ]),
    ("Audio avanzado", [
        ch("audio_source", "Fuente de audio", AUDIO_SOURCES),
        sl("audio_bitrate", "Bitrate de audio", 32, 320, "K"),
        tx("audio_encoder", "Encoder de audio"),
        sw("audio_dup", "Duplicar audio (PC + móvil)"),
        sw("no_audio_playback", "Capturar sin reproducir en PC"),
        sw("require_audio", "Exigir audio (fallar si no hay)"),
        sl("audio_output_buf", "Búfer de salida en PC", 0, 500, "ms"),
    ]),
    ("Pantalla virtual", [
        ch("virtual_display_res", "Resolución virtual", VD_RES),
        tx("virtual_dpi", "DPI", "220"),
        Spec("virtual_display_app", "App de inicio", "app", "Selecciona una aplicación instalada en tu móvil para iniciarla automáticamente."),
        sw("start_app_force_stop", "Reinicio limpio de la app (+force-stop)"),
        sw("no_vd_decorations", "Sin decoraciones del sistema"),
        sw("no_vd_destroy", "Conservar apps al cerrar"),
    ]),
    ("Ventana avanzada", [
        tx("window_title", "Título de ventana"),
        tx("window_x", "Posición X"), tx("window_y", "Posición Y"),
        tx("window_width", "Ancho"), tx("window_height", "Alto"),
        sw("borderless", "Sin bordes"),
        sw("no_window", "Sin ventana (headless)"),
        sw("no_playback", "Sin ventana de vídeo"),
        tx("background_color", "Color de fondo", "#000000"),
        sw("no_aspect_ratio_lock", "Sin bloqueo de relación de aspecto"),
        ch("min_size_alignment", "Alineación mínima de tamaño", MIN_SIZE_ALIGNMENT_VALUES),
        sw("no_mipmaps", "Sin mipmaps"),
        sw("disable_screensaver", "Desactivar salvapantallas del PC"),
        sw("print_fps", "Mostrar FPS en consola"),
    ]),
    ("Entrada", [
        ch("mouse", "Modo de ratón", MOUSE_MODES),
        ch("gamepad", "Mando", GAMEPAD_MODES),
        sw("otg_mode", "Modo OTG (periférico USB)", "Usa tu PC como teclado/ratón físico del móvil."),
        sw("keep_active", "Mantener activo"),
        tx("shortcut_mod", "Modificador de atajos", "lalt,lsuper"),
        sw("no_key_repeat", "Sin repetición de tecla"),
        sw("prefer_text", "Inyectar como texto"),
        sw("raw_key_events", "Eventos de tecla crudos"),
        sw("no_mouse_hover", "Sin hover del ratón"),
        sw("legacy_paste", "Pegado legacy"),
        sw("no_clipboard_sync", "No sincronizar portapapeles"),
        ch("display_ime_policy", "Política de teclado en pantalla", IME_POLICY_VALUES),
        tx("push_target", "Carpeta destino al arrastrar archivos", "/sdcard/Download"),
    ]),
    ("Energía", [
        sw("power_off_on_close", "Apagar pantalla al cerrar"),
        sw("no_power_on", "No encender al iniciar"),
        sl("screen_off_timeout", "Tiempo de pantalla apagada", 0, 300, "s"),
    ]),
    ("Grabación", [
        sw("record", "Grabar sesión"),
        tx("record_file", "Plantilla de archivo", "{device}_{date}_{time}.mp4",
           "Variables: {device}, {preset}, {date}, {time}"),
        ch("record_format", "Formato", RECORD_FORMATS),
        ch("record_orientation", "Orientación de grabación", RECORD_ORIENTATION_VALUES),
        sl("time_limit", "Límite de tiempo (0 = sin límite)", 0, 600, "s"),
    ]),
    ("Conexión y proceso", [
        sw("force_adb_forward", "Forzar ADB forward"),
        sw("kill_adb_on_close", "Detener ADB al salir"),
        tx("port", "Puerto local", "27183:27199"),
        tx("tunnel_host", "Tunnel host"), tx("tunnel_port", "Tunnel port"),
        ch("verbosity", "Nivel de log", VERBOSITY_LEVELS),
        ch("pause_on_exit", "Pausar al salir", PAUSE_ON_EXIT_VALUES),
        sw("no_cleanup", "No limpiar servidor al salir"),
        sw("no_downsize_on_error", "No reducir resolución al fallar"),
        sw("no_terminal_title", "No cambiar título de terminal"),
        tx("v4l2_device", "V4L2 sink (Linux)", "/dev/video2", linux_only=True),
    ]),
]

ALL_SPECS: dict[str, Spec] = {
    s.key: s for _, specs in (MAIN_SECTIONS + ADV_SECTIONS) for s in specs
}

# ── Goals (replace the 17 old profiles) ─────────────────────────────
GOALS = [
    {"id": "mirror", "icon": "📱", "title": "Espejo rápido",
     "desc": "Ver y controlar tu móvil con el mejor equilibrio.",
     "preset": "balanced", "over": {}},
    {"id": "gaming", "icon": "🎮", "title": "Gaming 120 FPS",
     "desc": "Latencia mínima, mando y ratón nativos.",
     "preset": "gaming", "over": {}},
    {"id": "desktop", "icon": "🖥️", "title": "Escritorio / DeX",
     "desc": "Un monitor virtual tipo PC en tu móvil.",
     "preset": "desktop", "over": {}},
    {"id": "app", "icon": "🪟", "title": "App en ventana aparte",
     "desc": "Abre una app en su propia ventana.",
     "preset": "virtual_app", "over": {}},
    {"id": "record", "icon": "⏺️", "title": "Grabar pantalla",
     "desc": "Graba en alta calidad mientras duplicas.",
     "preset": "video", "over": {"record": True, "record_file": "{device}_{date}_{time}.mp4"}},
    {"id": "camera", "icon": "📷", "title": "Cámara del móvil",
     "desc": "Usa la cámara del móvil como webcam.",
     "preset": "camera_doc", "over": {}},
]
# Variants shown inside the Goals page (old presets, nothing is lost).
EXTRA_PRESETS = ["gaming_competitive", "streamer", "vp9", "vp8", "compatible",
                 "present", "multimonitor", "mirror_readonly", "headless_record",
                 "otg", "otg_audio"]
