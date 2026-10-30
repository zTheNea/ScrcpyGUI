"""Session history persistence for ScrcpyGUI.

Keeps a rotating history (up to 50 entries) of executed sessions,
allowing users to review recent runs, re-launch them, or inspect generated commands.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime
from typing import Any

from paths import APP_DIR, ensure_app_dir, atomic_write_json, safe_read_json

logger = logging.getLogger(__name__)

HISTORY_FILE = os.path.join(APP_DIR, "history.json")
MAX_HISTORY_ENTRIES = 50
_lock = threading.Lock()


def _read_history_file() -> list[dict[str, Any]]:
    res = safe_read_json(HISTORY_FILE, default=[])
    return res if isinstance(res, list) else []


def _write_history_file(entries: list[dict[str, Any]]) -> None:
    try:
        ensure_app_dir()
        atomic_write_json(HISTORY_FILE, entries, backup=True)
    except Exception as e:
        logger.error("Error writing history file (%s): %s", HISTORY_FILE, e)



def record_session(
    device: str,
    preset: str,
    args: list[str],
    config: dict[str, Any] | None = None,
    command: str = "",
    success: bool = True,
) -> dict[str, Any]:
    """Append a session record to history, trimming to MAX_HISTORY_ENTRIES."""
    entry: dict[str, Any] = {
        "id": uuid.uuid4().hex[:12],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "device": device or "default",
        "preset": preset or "custom",
        "args": list(args),
        "command": command or " ".join(["scrcpy"] + list(args)),
        "config": dict(config) if config else {},
        "success": bool(success),
    }

    with _lock:
        history = _read_history_file()
        history.insert(0, entry)
        if len(history) > MAX_HISTORY_ENTRIES:
            history = history[:MAX_HISTORY_ENTRIES]
        _write_history_file(history)

    return entry


def get_history(limit: int = MAX_HISTORY_ENTRIES) -> list[dict[str, Any]]:
    """Return the most recent history records, up to `limit`."""
    with _lock:
        history = _read_history_file()
        return history[:limit]


def clear_history() -> None:
    """Clear all saved history records."""
    with _lock:
        _write_history_file([])


def delete_history_item(item_id: str) -> bool:
    """Delete a single history entry by its ID."""
    with _lock:
        history = _read_history_file()
        initial_len = len(history)
        history = [e for e in history if e.get("id") != item_id]
        if len(history) < initial_len:
            _write_history_file(history)
            return True
        return False
