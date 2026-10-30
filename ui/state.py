"""Application state for Scrcpy Studio (framework-agnostic, unit-testable).

``AppState`` exposes one ``Var`` per scrcpy option as ``state.v_<key>`` so the
existing ``config_manager`` (save/load config & profiles) keeps working
unchanged: it only needs objects with ``get()`` / ``set()``.
"""
from __future__ import annotations

from typing import Any, Callable

import config_manager as cfg
from presets import PRESETS

BOOL_KEYS = {
    "audio", "fullscreen", "stay_awake", "screen_off", "record", "print_fps",
    "show_touches", "always_on_top", "borderless", "virtual_display", "no_video",
    "no_control", "audio_dup", "disable_screensaver", "no_vd_decorations",
    "no_vd_destroy", "no_clipboard_sync", "flex_display", "virtual_mouse",
    "camera_torch", "keep_active", "no_aspect_ratio_lock", "otg_mode",
    "ignore_encoder_constraints", "no_audio_playback", "no_playback",
    "legacy_paste", "force_adb_forward", "camera_high_speed", "kill_adb_on_close",
    "no_video_playback", "require_audio", "power_off_on_close", "no_power_on",
    "no_window", "no_cleanup", "no_downsize_on_error", "no_key_repeat",
    "prefer_text", "raw_key_events", "no_mouse_hover", "no_terminal_title",
    "start_app_force_stop", "no_mipmaps", "auto_wifi",
}
INT_DEFAULTS = {
    "fps": 60, "bitrate": 8, "audio_buf": 50, "audio_bitrate": 128,
    "time_limit": 0, "video_buffer": 0, "camera_fps": 30, "audio_output_buf": 0,
    "screen_off_timeout": 0, "angle": 0,
}
STR_DEFAULTS = {
    "codec": "h264", "res_preset": "1080p", "max_size": "1920", "keyboard": "",
    "mouse": "", "gamepad": "", "record_file": "recording.mp4", "crop": "",
    "audio_source": "output", "audio_codec": "opus", "window_title": "Scrcpy Mirror",
    "virtual_display_res": "1920x1080", "virtual_res_preset": "1920x1080",
    "virtual_display_app": "", "video_source": "display", "camera_id": "0",
    "camera_facing": "", "v4l2_device": "", "display_id": "0", "orientation": "0",
    "virtual_dpi": "", "camera_zoom": "", "background_color": "", "render_fit": "",
    "video_encoder": "", "audio_encoder": "", "record_format": "",
    "capture_orientation": "0", "display_orientation": "0", "render_driver": "",
    "window_x": "", "window_y": "", "shortcut_mod": "", "push_target": "",
    "window_width": "", "window_height": "", "display_ime_policy": "",
    "verbosity": "", "pause_on_exit": "", "port": "", "tunnel_host": "",
    "tunnel_port": "", "camera_ar": "", "camera_size": "", "hwdec": "",
    "record_orientation": "", "min_size_alignment": "",
}
BOOL_DEFAULTS = {k: False for k in BOOL_KEYS}
BOOL_DEFAULTS["audio"] = True
BOOL_DEFAULTS["stay_awake"] = True

DEFAULTS: dict[str, Any] = {**STR_DEFAULTS, **INT_DEFAULTS, **BOOL_DEFAULTS}

# Options that scrcpy rejects when control is disabled (Read-only guardian).
NEEDS_CONTROL = ("stay_awake", "screen_off", "keep_active", "show_touches",
                 "power_off_on_close")


class Var:
    """Minimal observable variable with the tkinter ``get``/``set`` contract."""

    def __init__(self, state: "AppState", key: str, value: Any):
        self._state, self._key, self._value = state, key, value

    def get(self) -> Any:
        return self._value

    def set(self, value: Any) -> None:
        value = self._coerce(value)
        if value != self._value:
            self._value = value
            self._state._notify(self._key)

    def _coerce(self, value: Any) -> Any:
        key = self._key
        try:
            if key in BOOL_KEYS:
                return bool(value)
            if key in INT_DEFAULTS:
                return int(float(value))
        except (TypeError, ValueError):
            return self._value
        return "" if value is None else str(value)


class AppState:
    """Holds every scrcpy option plus session-level state."""

    def __init__(self) -> None:
        self._listeners: list[Callable[[str], None]] = [self._link]
        self._muted = 0
        self._pending: set[str] = set()
        self.device: str = ""
        self.active_mode = Var(self, "_active_mode", "balanced")  # config_manager hook
        self.available_apps: list[tuple[str, str]] = []
        for key, default in DEFAULTS.items():
            setattr(self, f"v_{key}", Var(self, key, default))

    def set_available_apps(self, apps: list[tuple[str, str]]) -> None:
        self.available_apps = list(apps)
        self._notify("available_apps")

    def _link(self, key: str) -> None:
        """Keep dependent options consistent (runs before UI listeners)."""
        if key == "virtual_mouse":
            if self.get("virtual_mouse"):
                self.set("mouse", "uhid")
            elif self.get("mouse") == "uhid":
                self.set("mouse", "")
        elif key == "mouse":
            self.set("virtual_mouse", self.get("mouse") == "uhid")
        elif key == "max_size":
            self.sync_res_label()

    def unsubscribe(self, fn: Callable[[str], None]) -> None:
        if fn in self._listeners:
            self._listeners.remove(fn)

    # ── observers ────────────────────────────────────────────────
    def subscribe(self, fn: Callable[[str], None]) -> None:
        self._listeners.append(fn)

    def _notify(self, key: str) -> None:
        if self._muted:
            self._pending.add(key)
            return
        for fn in list(self._listeners):
            fn(key)

    def batch(self) -> "_Batch":
        """Context manager: coalesce many ``set`` calls into one ``*`` event."""
        return _Batch(self)

    # ── access ───────────────────────────────────────────────────
    def var(self, key: str) -> Var:
        return getattr(self, f"v_{key}")

    def get(self, key: str) -> Any:
        return self.var(key).get()

    def set(self, key: str, value: Any) -> None:
        self.var(key).set(value)

    def to_config(self) -> dict[str, Any]:
        """Flat dict consumed by ``command_builder.build_scrcpy_args``."""
        data = {"device": self.device, "active_mode": self.active_mode.get()}
        for key in cfg.CONFIG_KEYS:
            var = getattr(self, f"v_{key}", None)
            if var is not None:
                data[key] = var.get()
        return data

    # ── presets ──────────────────────────────────────────────────
    def reset(self) -> None:
        with self.batch():
            for key, default in DEFAULTS.items():
                self.set(key, default)

    def apply_preset(self, key: str, overrides: dict[str, Any] | None = None) -> None:
        """Reset to defaults and apply a preset (+ optional overrides)."""
        aliases = {
            "virtual": "virtual_app",
            "virtual_app": "virtual",
            "record": "recording",
            "recording": "record",
            "camera": "camera_doc",
            "camera_doc": "camera",
        }
        preset = dict(PRESETS.get(key, {}))
        if not preset and key in aliases:
            preset = dict(PRESETS.get(aliases[key], {}))
        preset.update(overrides or {})
        with self.batch():
            self.reset()
            self.active_mode.set(key)
            for name, val in preset.items():
                if name in ("label", "desc", "badge", "prompt_app"):
                    continue
                if name == "audio_buffer":
                    name = "audio_buf"
                elif name == "gamepad":
                    val = "uhid" if val is True else ("" if val is False else val)
                elif name == "max_size":
                    val = str(val)
                if hasattr(self, f"v_{name}"):
                    self.set(name, val)
            self.sync_virtual_mouse("virtual_mouse" in preset)
            self.sync_res_label()
            if ":" in self.device:
                # Safe Wi-Fi parameters: keep screen on to avoid antenna sleep, buffer jitter, and sdk input
                if self.get("screen_off"):
                    self.set("screen_off", False)
                if self.get("audio_buf") < 60:
                    self.set("audio_buf", 60)
                if self.get("video_buffer") < 20:
                    self.set("video_buffer", 20)
                if self.get("keyboard") == "uhid":
                    self.set("keyboard", "sdk")
                if self.get("mouse") == "uhid":
                    self.set("mouse", "sdk")
                    self.set("virtual_mouse", False)

    def sync_virtual_mouse(self, explicit: bool = False) -> None:
        """Reconcile ``virtual_mouse`` and ``mouse`` after a bulk update."""
        if explicit:
            if self.get("virtual_mouse"):
                self.set("mouse", "uhid")
            elif self.get("mouse") == "uhid":
                self.set("mouse", "")
        else:
            self.set("virtual_mouse", self.get("mouse") == "uhid")

    RES_LABELS = {"0": "Original", "3840": "4K", "2560": "1440p",
                  "1920": "1080p", "1280": "720p", "854": "480p"}

    def sync_res_label(self) -> None:
        self.set("res_preset", self.RES_LABELS.get(self.get("max_size"), "Personalizada"))

    # ── guardian ─────────────────────────────────────────────────
    def disabled_reason(self, key: str) -> str:
        """Return a human reason if *key* cannot be used right now ('' = ok)."""
        cam = self.get("video_source") == "camera"
        if key in NEEDS_CONTROL and (self.get("no_control") or cam):
            return "No disponible en modo Solo lectura / Cámara (scrcpy lo rechaza)."
        if key in ("keyboard", "mouse", "gamepad") and (self.get("no_control") or cam):
            return "El control está desactivado (Solo lectura / Cámara)."
        if key in ("audio_buf", "audio_codec", "audio_bitrate", "audio_source",
                   "audio_dup", "audio_encoder") and not self.get("audio"):
            return "Activa el audio para ajustar esta opción."
        if key in ("max_size", "crop", "display_id") and cam:
            return "No aplica al usar la cámara como fuente."
        if key in ("virtual_display_res", "virtual_dpi", "flex_display",
                   "virtual_display_app", "start_app_force_stop",
                   "no_vd_decorations", "no_vd_destroy") and not self.get("virtual_display"):
            return "Requiere una pantalla virtual (modo Escritorio o App en ventana)."
        if key in ("record_file", "record_format", "record_orientation") and not self.get("record"):
            return "Activa la grabación para ajustar esta opción."
        return ""


class _Batch:
    def __init__(self, state: AppState):
        self.state = state

    def __enter__(self):
        self.state._muted += 1
        return self.state

    def __exit__(self, *exc):
        st = self.state
        st._muted -= 1
        if st._muted == 0 and st._pending:
            st._pending.clear()
            for fn in list(st._listeners):
                fn("*")
        return False
