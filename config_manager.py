"""Configuration persistence and profile management for ScrcpyGUI."""
import json
import os
import shutil

# Config file lives next to the executable / script
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(_BASE_DIR, "config.json")
PROFILES_FILE = os.path.join(_BASE_DIR, "profiles.json")

# Keys that map directly to tkinter variable names (v_<key>)
CONFIG_KEYS = [
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
    # scrcpy v4.0
    "flex_display", "camera_torch", "camera_zoom", "keep_active",
    "background_color", "no_aspect_ratio_lock", "otg_mode",
]


def save_config(gui):
    """Save all config variables from the GUI to config.json."""
    data = {}
    data["_active_mode"] = gui.active_mode.get()
    for key in CONFIG_KEYS:
        var = getattr(gui, f"v_{key}", None)
        if var is not None:
            data[key] = var.get()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")


def load_config(gui):
    """Load config from config.json and apply to GUI variables.
    Returns (success: bool, active_mode: str).
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
        print(f"Error loading config: {e}")
        return (False, "")


def _read_profiles():
    """Read profiles.json, return dict."""
    if not os.path.isfile(PROFILES_FILE):
        return {}
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_profiles(profiles):
    """Write profiles dict to profiles.json."""
    try:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving profiles: {e}")


def list_profiles():
    """Return list of profile names."""
    return list(_read_profiles().keys())


def save_profile(gui, name):
    """Save current GUI state as a named profile."""
    profiles = _read_profiles()
    data = {}
    for key in CONFIG_KEYS:
        var = getattr(gui, f"v_{key}", None)
        if var is not None:
            data[key] = var.get()
    profiles[name] = data
    _write_profiles(profiles)


def load_profile(gui, name):
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


def delete_profile(name):
    """Delete a named profile. Returns True on success."""
    profiles = _read_profiles()
    if name in profiles:
        del profiles[name]
        _write_profiles(profiles)
        return True
    return False
