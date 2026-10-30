"""Centralised application paths and platform detection for ScrcpyGUI.

Every module that needs to know *where* data lives should import from here
instead of computing paths independently.  This avoids duplicated logic
between ``scrcpy_manager`` and ``config_manager``.
"""
from __future__ import annotations

import os
import platform

IS_WINDOWS: bool = platform.system() == "Windows"
"""``True`` when running on Microsoft Windows."""

# ── Application data directory ──────────────────────────────────────
if IS_WINDOWS:
    APP_DIR: str = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
        "ScrcpyGUI",
    )
else:
    APP_DIR: str = os.path.join(
        os.path.expanduser("~"), ".local", "share", "ScrcpyGUI",
    )

SCRCPY_DIR: str = os.path.join(APP_DIR, "scrcpy")
"""Directory where the scrcpy binary and its assets are stored."""

VERSION_FILE: str = os.path.join(APP_DIR, "version.json")
"""JSON file that records the currently installed scrcpy version."""

CONFIG_FILE: str = os.path.join(APP_DIR, "config.json")
"""JSON file that persists the user's last GUI configuration."""

PROFILES_FILE: str = os.path.join(APP_DIR, "profiles.json")
"""JSON file that stores named user profiles."""

# ── Legacy paths (next to the script) for one-time migration ────────
LEGACY_DIR: str = os.path.dirname(os.path.abspath(__file__))
LEGACY_CONFIG: str = os.path.join(LEGACY_DIR, "config.json")
LEGACY_PROFILES: str = os.path.join(LEGACY_DIR, "profiles.json")


def ensure_app_dir() -> None:
    """Create the application data directory if it does not already exist."""
    os.makedirs(APP_DIR, exist_ok=True)


RECORDINGS_DIR: str = os.path.join(
    os.path.expanduser("~"),
    "Videos",
    "ScrcpyRecordings",
)
"""Default directory where screen recordings are saved."""


def ensure_recordings_dir() -> str:
    """Create and return the recordings directory."""
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    return RECORDINGS_DIR


def atomic_write_json(filepath: str, data: Any, backup: bool = False, indent: int = 2) -> None:
    """Safely write data to a JSON file using an atomic replace strategy.

    1. Writes data to a temporary file in the same directory.
    2. Flushes and syncs to disk.
    3. Replaces target file atomically via `os.replace`.
    """
    import json
    import shutil
    import tempfile

    dir_name = os.path.dirname(filepath) or "."
    os.makedirs(dir_name, exist_ok=True)

    if backup and os.path.isfile(filepath) and os.path.getsize(filepath) > 0:
        try:
            shutil.copy2(filepath, filepath + ".bak")
        except Exception:
            pass

    tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, filepath)
    except Exception:
        if os.path.isfile(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise


def safe_read_json(filepath: str, default: Any = None) -> Any:
    """Read a JSON file safely, returning default on failure or falling back to .bak."""
    import json

    if not os.path.isfile(filepath):
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        bak = filepath + ".bak"
        if os.path.isfile(bak):
            try:
                with open(bak, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return default


