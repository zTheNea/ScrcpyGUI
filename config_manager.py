"""Configuration persistence and profile management for ScrcpyGUI."""
from __future__ import annotations

import json
import logging
import os
import platform
import shutil
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # avoid circular import at runtime
    from scrcpy_gui import ScrcpyGUI

logger = logging.getLogger(__name__)

# ── Data directory (shared with scrcpy_manager.py) ──
if platform.system() == "Windows":
    _APP_DIR = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
        "ScrcpyGUI",
    )
else:
    _APP_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "ScrcpyGUI")

CONFIG_FILE = os.path.join(_APP_DIR, "config.json")
PROFILES_FILE = os.path.join(_APP_DIR, "profiles.json")

# ── Legacy path (next to the script) for automatic migration ──
_LEGACY_DIR = os.path.dirname(os.path.abspath(__file__))
_LEGACY_CONFIG = os.path.join(_LEGACY_DIR, "config.json")
_LEGACY_PROFILES = os.path.join(_LEGACY_DIR, "profiles.json")


def _ensure_app_dir() -> None:
    """Create the data directory if it doesn't exist."""
    os.makedirs(_APP_DIR, exist_ok=True)


def _migrate_legacy_files() -> None:
    """One-time migration: copy config/profiles from the old location."""
    _ensure_app_dir()
    for src, dst in [(_LEGACY_CONFIG, CONFIG_FILE), (_LEGACY_PROFILES, PROFILES_FILE)]:
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
    "flex_display", "camera_torch", "camera_zoom", "keep_active",
    "background_color", "no_aspect_ratio_lock", "otg_mode",
    "ignore_encoder_constraints", "no_audio_playback", "no_playback",
    "audio_output_buf", "legacy_paste", "force_adb_forward",
    "camera_high_speed", "kill_adb_on_close",
]


def save_config(gui: ScrcpyGUI) -> None:
    """Save all config variables from the GUI to config.json."""
    data: dict[str, Any] = {}
    data["_active_mode"] = gui.active_mode.get()
    for key in CONFIG_KEYS:
        var = getattr(gui, f"v_{key}", None)
        if var is not None:
            data[key] = var.get()
    try:
        _ensure_app_dir()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Error saving config: %s", e)


def load_config(gui: ScrcpyGUI) -> tuple[bool, str]:
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
    """Read profiles.json, return dict."""
    if not os.path.isfile(PROFILES_FILE):
        return {}
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_profiles(profiles: dict[str, dict[str, Any]]) -> None:
    """Write profiles dict to profiles.json."""
    try:
        _ensure_app_dir()
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Error saving profiles: %s", e)


def list_profiles() -> list[str]:
    """Return list of profile names."""
    return list(_read_profiles().keys())


def save_profile(gui: ScrcpyGUI, name: str) -> None:
    """Save current GUI state as a named profile."""
    profiles = _read_profiles()
    data: dict[str, Any] = {}
    for key in CONFIG_KEYS:
        var = getattr(gui, f"v_{key}", None)
        if var is not None:
            data[key] = var.get()
    profiles[name] = data
    _write_profiles(profiles)


def load_profile(gui: ScrcpyGUI, name: str) -> bool:
    """Load a named profile into the GUI. Returns True on success."""
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
    return True


def delete_profile(name: str) -> bool:
    """Delete a named profile. Returns True on success."""
    profiles = _read_profiles()
    if name in profiles:
        del profiles[name]
        _write_profiles(profiles)
        return True
    return False
