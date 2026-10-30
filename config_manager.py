"""Configuration persistence and profile management for ScrcpyGUI."""
from __future__ import annotations

import json
import logging
import os
import shutil
from typing import TYPE_CHECKING, Any

from paths import (
    APP_DIR, CONFIG_FILE, PROFILES_FILE,
    LEGACY_CONFIG, LEGACY_PROFILES, ensure_app_dir,
    atomic_write_json, safe_read_json,
)

if TYPE_CHECKING:  # avoid circular import at runtime
    from scrcpy_gui import ScrcpyGUI

logger = logging.getLogger(__name__)


def _migrate_legacy_files() -> None:
    """One-time migration: copy config/profiles from the old location."""
    ensure_app_dir()
    for src, dst in [(LEGACY_CONFIG, CONFIG_FILE), (LEGACY_PROFILES, PROFILES_FILE)]:
        if os.path.isfile(src) and not os.path.isfile(dst):
            try:
                shutil.copy2(src, dst)
            except Exception:
                pass


# Run migration on import
_migrate_legacy_files()

# Keys that map directly to tkinter variable names (v_<key>)
CONFIG_KEYS: list[str] = [
    "codec", "res_preset", "max_size", "fps", "bitrate",
    "audio", "audio_buf", "fullscreen", "stay_awake", "screen_off",
    "keyboard", "mouse", "gamepad", "record", "record_file",
    "print_fps", "show_touches", "crop", "audio_source", "audio_codec",
    "always_on_top", "borderless", "window_title",
    "virtual_display", "virtual_display_res", "virtual_res_preset",
    "virtual_display_app", "video_source", "camera_id", "camera_facing",
    "camera_fps", "v4l2_device", "display_id", "orientation",
    "no_video", "no_control", "audio_dup", "audio_bitrate",
    "disable_screensaver", "time_limit", "no_vd_decorations",
    "no_vd_destroy", "virtual_dpi", "no_clipboard_sync", "video_buffer",
    # scrcpy v4.0 / v4.1
    "flex_display", "virtual_mouse", "camera_torch", "camera_zoom", "keep_active",
    "background_color", "no_aspect_ratio_lock", "otg_mode",
    "ignore_encoder_constraints", "no_audio_playback", "no_playback",
    "audio_output_buf", "legacy_paste", "force_adb_forward",
    "camera_high_speed", "kill_adb_on_close",
    # Phase 1 — high-value missing options
    "render_fit", "no_video_playback", "video_encoder", "audio_encoder",
    "record_format", "require_audio",
    "capture_orientation", "display_orientation",
    "render_driver", "window_x", "window_y",
    "power_off_on_close", "no_power_on", "shortcut_mod", "push_target",
    # Phase 2 — Advanced tab
    "window_width", "window_height", "no_window",
    "display_ime_policy", "verbosity", "pause_on_exit",
    "no_cleanup", "no_downsize_on_error", "screen_off_timeout",
    "no_key_repeat", "prefer_text", "raw_key_events", "no_mouse_hover",
    "port", "tunnel_host", "tunnel_port", "no_terminal_title", "angle",
    # Phase 2 — Camera extras
    "camera_ar", "camera_size",
    # scrcpy 5.0 / 5.0.1
    "hwdec", "start_app_force_stop", "record_orientation",
    "min_size_alignment", "no_mipmaps",
    # Wi-Fi Auto
    "auto_wifi",
]


def save_config(gui: Any) -> None:
    """Save all config variables from the GUI to config.json atomically."""
    data: dict[str, Any] = {}
    if hasattr(gui, "active_mode") and hasattr(gui.active_mode, "get"):
        data["_active_mode"] = gui.active_mode.get()
    elif hasattr(gui, "goal"):
        data["_active_mode"] = getattr(gui, "goal")

    for key in CONFIG_KEYS:
        var = getattr(gui, f"v_{key}", None)
        if var is not None:
            data[key] = var.get()
    try:
        ensure_app_dir()
        atomic_write_json(CONFIG_FILE, data, backup=True)
    except Exception as e:
        logger.error("Error saving config: %s", e)


def load_config(gui: Any) -> tuple[bool, str]:
    """Load config from config.json and apply to GUI variables.

    Returns
    -------
    tuple[bool, str]
        ``(success, active_mode)``
    """
    if not os.path.isfile(CONFIG_FILE):
        return (False, "")
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        saved_mode = data.pop("_active_mode", "")
        for key, value in data.items():
            var = getattr(gui, f"v_{key}", None)
            if var is not None:
                try:
                    var.set(value)
                except Exception:
                    pass
        if hasattr(gui, "goal") and saved_mode:
            try:
                gui.goal = saved_mode
            except Exception:
                pass
        return (True, saved_mode)
    except Exception as e:
        # Backup the corrupt file for debugging
        try:
            shutil.copy2(CONFIG_FILE, CONFIG_FILE + ".bak")
        except Exception:
            pass
        logger.error("Error loading config: %s", e)
        return (False, "")


def _read_profiles() -> dict[str, dict[str, Any]]:
    """Read profiles.json safely."""
    res = safe_read_json(PROFILES_FILE, default={})
    return res if isinstance(res, dict) else {}


def _write_profiles(profiles: dict[str, dict[str, Any]]) -> None:
    """Write profiles dict to profiles.json atomically."""
    try:
        ensure_app_dir()
        atomic_write_json(PROFILES_FILE, profiles, backup=True)
    except Exception as e:
        logger.error("Error saving profiles: %s", e)



def list_profiles() -> list[str]:
    """Return list of profile names."""
    return list(_read_profiles().keys())


def get_profile_data(name: str) -> dict[str, Any]:
    """Return dictionary of a specific profile or empty dict if not found."""
    return _read_profiles().get(name, {})


def save_profile(gui: Any, name: str) -> None:
    """Save current GUI state as a named profile."""
    # Allow (gui, name) or (name, gui)
    if isinstance(gui, str) and not isinstance(name, str):
        gui, name = name, gui

    profiles = _read_profiles()
    data: dict[str, Any] = {}
    for key in CONFIG_KEYS:
        var = getattr(gui, f"v_{key}", None)
        if var is not None:
            data[key] = var.get()

    # Preserve goal/preset tag if available
    if hasattr(gui, "goal"):
        data["_goal"] = getattr(gui, "goal")
    elif hasattr(gui, "active_mode") and hasattr(gui.active_mode, "get"):
        data["_goal"] = gui.active_mode.get()

    profiles[name] = data
    _write_profiles(profiles)


def load_profile(gui: Any, name: str) -> bool:
    """Load a named profile into the GUI. Returns True on success."""
    # Allow (gui, name) or (name, gui)
    if isinstance(gui, str) and not isinstance(name, str):
        gui, name = name, gui

    profiles = _read_profiles()
    if name not in profiles:
        return False
    data = profiles[name]
    for key, value in data.items():
        var = getattr(gui, f"v_{key}", None)
        if var is not None:
            try:
                var.set(value)
            except Exception:
                pass

    if "_goal" in data and hasattr(gui, "goal"):
        try:
            gui.goal = data["_goal"]
        except Exception:
            pass

    return True


def delete_profile(name: str) -> bool:
    """Delete a named profile. Returns True on success."""
    profiles = _read_profiles()
    if name in profiles:
        del profiles[name]
        _write_profiles(profiles)
        return True
    return False

