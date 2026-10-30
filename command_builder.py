"""Pure function to build scrcpy command-line arguments from a config dict.

This module is independent of the GUI framework so it can be unit-tested
without importing customtkinter.
"""
from __future__ import annotations

from datetime import datetime
import os
import re
from typing import Any


def _safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int, returning *default* on failure.

    Handles float-strings like ``"12.34"`` by truncating to ``12``.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default


def format_record_filename(template: str, cfg: dict[str, Any], dt: datetime | None = None) -> str:
    """Format a recording filename template with variables and strftime tokens.

    Supported variables: ``{device}``, ``{preset}``, ``{date}``, ``{time}``.
    Also supports standard datetime strftime directives like ``%Y``, ``%m``, ``%d``, ``%H``, ``%M``, ``%S``.
    """
    rf = str(template).strip() or "recording.mp4"
    now = dt or datetime.now()
    dev_raw = str(cfg.get("device", "device")).split(" (")[0].strip() or "device"
    dev_clean = re.sub(r'[\/:*?"<>|]', '_', dev_raw)
    preset_name = str(cfg.get("active_mode", cfg.get("preset", "custom"))) or "session"

    rf = rf.replace("{device}", dev_clean)
    rf = rf.replace("{preset}", preset_name)
    rf = rf.replace("{date}", now.strftime("%Y%m%d"))
    rf = rf.replace("{time}", now.strftime("%H%M%S"))
    try:
        rf = now.strftime(rf)
    except Exception:
        pass
    return rf


def parse_version(ver: tuple[int, ...] | str | None) -> tuple[int, int]:
    """Parse version into a (major, minor) integer tuple.

    Defaults to (99, 99) (unconstrained modern target) when unspecified or empty.
    """
    if not ver:
        return (99, 99)
    if isinstance(ver, tuple):
        if len(ver) >= 2:
            return (int(ver[0]), int(ver[1]))
        if len(ver) == 1:
            return (int(ver[0]), 0)
        return (99, 99)
    m = re.search(r"(\d+)(?:\.(\d+))?", str(ver))
    if m:
        major = int(m.group(1))
        minor = int(m.group(2)) if m.group(2) else 0
        return (major, minor)
    return (99, 99)


def build_scrcpy_args(
    cfg: dict[str, Any],
    is_windows: bool = True,
    scrcpy_version: tuple[int, ...] | str | None = None,
) -> list[str]:
    """Build a list of scrcpy CLI arguments from a flat config dictionary.

    Parameters
    ----------
    cfg : dict
        Flat key→value mapping. Expected keys mirror the configuration schema.
    is_windows : bool
        Whether the host OS is Windows (controls V4L2 visibility).
    scrcpy_version : tuple[int, ...] | str | None
        Target scrcpy version (e.g. 'v5.0' or (3, 0)). If omitted, targets
        the latest version without filtering.

    Returns
    -------
    list[str]
        The argument list (without the scrcpy executable itself).
    """
    ver = parse_version(scrcpy_version)
    args: list[str] = []

    # ── Device ──────────────────────────────────────
    dev = str(cfg.get("device", "")).split(" (")[0]
    if dev and "Buscando" not in dev and "Sin dispositivos" not in dev:
        args.extend(["-s", dev])

    # ── OTG mode ────────────────────────────────
    if cfg.get("otg_mode"):
        if cfg.get("audio", False):
            # OTG with Audio forwarding: headless video, audio streaming & native UHID controls
            args.append("--no-video")
        else:
            args.append("--otg")
            return args
    elif cfg.get("no_video"):
        args.append("--no-video")

    # ── Video Source ────────────────────────────────
    src = str(cfg.get("video_source", "display"))
    if src == "camera":
        args.append("--video-source=camera")
        if cfg.get("camera_torch") and ver >= (3, 0):
            args.append("--camera-torch")
        if cfg.get("camera_high_speed") and ver >= (3, 0):
            args.append("--camera-high-speed")
        zoom = str(cfg.get("camera_zoom", "")).strip()
        if zoom:
            args.append(f"--camera-zoom={zoom}")
        cid = str(cfg.get("camera_id", "0")).strip()
        if cid and cid != "0":
            args.append(f"--camera-id={cid}")
        else:
            facing = str(cfg.get("camera_facing", ""))
            if facing:
                args.append(f"--camera-facing={facing}")
        cam_fps = _safe_int(cfg.get("camera_fps", 30), 30)
        if cam_fps and cam_fps != 30:
            args.append(f"--camera-fps={cam_fps}")
    else:
        ms = str(cfg.get("max_size", "")).strip()
        if ms and ms != "0":
            args.append(f"--max-size={ms}")
        did = str(cfg.get("display_id", "0")).strip()
        if did and did != "0":
            args.append(f"--display-id={did}")

    codec = str(cfg.get("codec", "h264"))
    if codec and codec != "h264":
        args.append(f"--video-codec={codec}")
    fps = _safe_int(cfg.get("fps", 0))
    if fps:
        args.append(f"--max-fps={fps}")
    br = _safe_int(cfg.get("bitrate", 8), 8)
    if br and br != 8:
        args.append(f"--video-bit-rate={br}M")

    # scrcpy v4.1: ignore video encoder constraints
    if cfg.get("ignore_encoder_constraints") and ver >= (4, 1):
        args.append("--ignore-video-encoder-constraints")

    # ── Orientation ─────────────────────────────────
    # --capture-orientation and --display-orientation (scrcpy 4.0+, split from old --orientation)
    cap_orient = str(cfg.get("capture_orientation", "")).strip()
    disp_orient = str(cfg.get("display_orientation", "")).strip()
    if cap_orient and cap_orient != "0":
        args.append(f"--capture-orientation={cap_orient}")
    if disp_orient and disp_orient != "0":
        args.append(f"--display-orientation={disp_orient}")
    # Legacy --orientation (kept for backwards-compat presets that use it)
    if not cap_orient and not disp_orient:
        orient = str(cfg.get("orientation", "0"))
        if orient and orient != "0":
            args.append(f"--orientation={orient}")
    # Custom angle (degrees, independent of orientation)
    angle = _safe_int(cfg.get("angle", 0))
    if angle:
        args.append(f"--angle={angle}")

    # ── Audio ───────────────────────────────────────
    if not cfg.get("audio", True):
        args.append("--no-audio")
    else:
        audio_src = str(cfg.get("audio_source", "output"))
        if audio_src != "output":
            args.append(f"--audio-source={audio_src}")
        ac = str(cfg.get("audio_codec", "opus"))
        if ac != "opus":
            args.append(f"--audio-codec={ac}")
        ab = _safe_int(cfg.get("audio_buf") if "audio_buf" in cfg else cfg.get("audio_buffer", 0))
        if ab > 0:
            args.append(f"--audio-buffer={ab}")
        abr = _safe_int(cfg.get("audio_bitrate", 128), 128)
        if abr != 128:
            args.append(f"--audio-bit-rate={abr}K")
        if cfg.get("audio_dup"):
            args.append("--audio-dup")
        if cfg.get("no_audio_playback"):
            args.append("--no-audio-playback")
        aob = _safe_int(cfg.get("audio_output_buf", 0))
        if aob > 0:
            args.append(f"--audio-output-buffer={aob}")
        a_enc = str(cfg.get("audio_encoder", "")).strip()
        if a_enc:
            args.append(f"--audio-encoder={a_enc}")
        if cfg.get("require_audio"):
            args.append("--require-audio")
    # Recording format (force override of extension-based detection)
    rec_fmt = str(cfg.get("record_format", "")).strip()
    if rec_fmt:
        args.append(f"--record-format={rec_fmt}")
    rec_orient = str(cfg.get("record_orientation", "")).strip()
    if rec_orient:
        args.append(f"--record-orientation={rec_orient}")

    # ── Video buffer ────────────────────────────────
    vb = _safe_int(cfg.get("video_buffer", 0))
    if vb > 0:
        args.append(f"--video-buffer={vb}")

    # ── Window & Playback ───────────────────────────
    if cfg.get("fullscreen"):
        args.append("--fullscreen")
    if cfg.get("always_on_top"):
        args.append("--always-on-top")
    if cfg.get("borderless"):
        args.append("--window-borderless")
    if cfg.get("disable_screensaver"):
        args.append("--disable-screensaver")
    if cfg.get("no_playback"):
        args.append("--no-playback")
    if cfg.get("no_video_playback"):
        args.append("--no-video-playback")
    if cfg.get("no_window"):
        args.append("--no-window")
    # Render fit & driver
    rf = str(cfg.get("render_fit", "")).strip()
    if rf:
        args.append(f"--render-fit={rf}")
    rd = str(cfg.get("render_driver", "")).strip()
    if rd:
        args.append(f"--render-driver={rd}")
    # Hardware video decoding (scrcpy 5.0+)
    hwdec = str(cfg.get("hwdec", "")).strip().lower()
    if hwdec and ver >= (5, 0):
        args.append(f"--hwdec={hwdec}")
    # Video encoder
    v_enc = str(cfg.get("video_encoder", "")).strip()
    if v_enc:
        args.append(f"--video-encoder={v_enc}")
    # Window position and size
    wx = str(cfg.get("window_x", "")).strip()
    if wx:
        args.append(f"--window-x={wx}")
    wy = str(cfg.get("window_y", "")).strip()
    if wy:
        args.append(f"--window-y={wy}")
    ww = str(cfg.get("window_width", "")).strip()
    if ww and ww != "0":
        args.append(f"--window-width={ww}")
    wh = str(cfg.get("window_height", "")).strip()
    if wh and wh != "0":
        args.append(f"--window-height={wh}")
    has_no_control = bool(cfg.get("no_control") or src == "camera")
    if not (cfg.get("otg_mode") and not cfg.get("audio", False)):
        if cfg.get("stay_awake") and not has_no_control:
            args.append("--stay-awake")
        if cfg.get("screen_off") and not has_no_control:
            args.append("--turn-screen-off")
        if cfg.get("keep_active") and not has_no_control:
            args.append("--keep-active")
        if cfg.get("power_off_on_close") and not has_no_control:
            args.append("--power-off-on-close")
        if cfg.get("no_power_on"):
            args.append("--no-power-on")
        sot = _safe_int(cfg.get("screen_off_timeout", 0))
        if sot > 0 and not has_no_control:
            args.append(f"--screen-off-timeout={sot}")
    bg = str(cfg.get("background_color", "")).strip()
    if bg:
        args.append(f"--background-color={bg}")
    if cfg.get("no_aspect_ratio_lock"):
        args.append("--no-window-aspect-ratio-lock")
    wt = str(cfg.get("window_title", "")).strip()
    if wt:
        args.append(f"--window-title={wt}")
    # Display IME policy
    ime = str(cfg.get("display_ime_policy", "")).strip()
    if ime:
        args.append(f"--display-ime-policy={ime}")

    # ── Virtual Display ─────────────────────────────
    if cfg.get("virtual_display") and src != "camera" and ver >= (3, 0):
        res = str(cfg.get("virtual_display_res", "1280x720")).strip() or "1280x720"
        dpi = str(cfg.get("virtual_dpi", "")).strip()
        vd_val = f"{res}/{dpi}" if dpi else res
        args.append(f"--new-display={vd_val}")
        if cfg.get("flex_display"):
            args.append("--flex-display")
        v_app = str(cfg.get("virtual_display_app", "")).strip()
        if v_app and not has_no_control:
            if cfg.get("start_app_force_stop"):
                if ver >= (5, 0) and not v_app.startswith("+"):
                    v_app = f"+{v_app}"
                elif ver < (5, 0) and v_app.startswith("+"):
                    v_app = v_app[1:]
            args.append(f"--start-app={v_app}")
        if cfg.get("no_vd_decorations"):
            args.append("--no-vd-system-decorations")
        if cfg.get("no_vd_destroy"):
            args.append("--no-vd-destroy-content")

    if not is_windows:
        v4l2 = str(cfg.get("v4l2_device", "")).strip()
        if v4l2:
            args.append(f"--v4l2-sink={v4l2}")

    # ── Controls ────────────────────────────────────
    if cfg.get("no_control") or src == "camera":
        args.append("--no-control")
    else:
        kb = str(cfg.get("keyboard", ""))
        if not kb and cfg.get("otg_mode"):
            kb = "uhid"
        if kb and kb != "sdk":
            args.append(f"--keyboard={kb}")
        ms2 = str(cfg.get("mouse", ""))
        if cfg.get("virtual_mouse") is False and ms2 == "uhid":
            ms2 = ""
        elif cfg.get("virtual_mouse") is True and not ms2:
            ms2 = "uhid"
        if not ms2 and cfg.get("otg_mode"):
            ms2 = "uhid"
        if ms2 and ms2 != "sdk":
            args.append(f"--mouse={ms2}")
        gp = str(cfg.get("gamepad", ""))
        if gp:
            args.append(f"--gamepad={gp}")

    if cfg.get("no_clipboard_sync"):
        args.append("--no-clipboard-autosync")
    if cfg.get("legacy_paste"):
        args.append("--legacy-paste")
    # Shortcut modifier
    sm = str(cfg.get("shortcut_mod", "")).strip()
    if sm:
        args.append(f"--shortcut-mod={sm}")
    # Push target directory
    pt = str(cfg.get("push_target", "")).strip()
    if pt:
        args.append(f"--push-target={pt}")
    # Advanced input flags
    if cfg.get("no_key_repeat"):
        args.append("--no-key-repeat")
    if cfg.get("prefer_text"):
        args.append("--prefer-text")
    if cfg.get("raw_key_events"):
        args.append("--raw-key-events")
    if cfg.get("no_mouse_hover"):
        args.append("--no-mouse-hover")

    # ── Connection & Process ────────────────────────
    if cfg.get("force_adb_forward"):
        args.append("--force-adb-forward")
    if cfg.get("kill_adb_on_close"):
        args.append("--kill-adb-on-close")
    # Port range
    port = str(cfg.get("port", "")).strip()
    if port:
        args.append(f"--port={port}")
    # Tunnel
    th = str(cfg.get("tunnel_host", "")).strip()
    if th:
        args.append(f"--tunnel-host={th}")
    tp = str(cfg.get("tunnel_port", "")).strip()
    if tp:
        args.append(f"--tunnel-port={tp}")
    # Verbosity
    vrb = str(cfg.get("verbosity", "")).strip()
    if vrb:
        args.append(f"--verbosity={vrb}")
    # Pause on exit
    poe = str(cfg.get("pause_on_exit", "")).strip()
    if poe and poe != "false":
        args.append(f"--pause-on-exit={poe}")
    # Cleanup & downsize
    if cfg.get("no_cleanup"):
        args.append("--no-cleanup")
    if cfg.get("no_downsize_on_error"):
        args.append("--no-downsize-on-error")
    # Terminal title (4.1)
    if cfg.get("no_terminal_title") and ver >= (4, 1):
        args.append("--no-terminal-title")
    # scrcpy 5.0+: min-size-alignment & no-mipmaps
    if ver >= (5, 0):
        msa = _safe_int(cfg.get("min_size_alignment", 0))
        if msa > 0:
            args.append(f"--min-size-alignment={msa}")
        if cfg.get("no_mipmaps"):
            args.append("--no-mipmaps")

    # ── Recording ───────────────────────────────────
    if cfg.get("record"):
        rf = format_record_filename(cfg.get("record_file", "recording.mp4"), cfg)
        if not os.path.isabs(rf):
            try:
                from paths import RECORDINGS_DIR, ensure_recordings_dir
                ensure_recordings_dir()
                rf = os.path.join(RECORDINGS_DIR, rf)
            except Exception:
                pass
        else:
            try:
                os.makedirs(os.path.dirname(rf), exist_ok=True)
            except Exception:
                pass
        args.append(f"--record={rf}")
    tl = _safe_int(cfg.get("time_limit", 0))
    if tl > 0:
        args.append(f"--time-limit={tl}")

    if cfg.get("print_fps"):
        args.append("--print-fps")
    if cfg.get("show_touches") and not has_no_control:
        args.append("--show-touches")
    crop = str(cfg.get("crop", "")).strip()
    if crop and src != "camera":
        args.append(f"--crop={crop}")

    # Camera extras (Phase 2)
    if src == "camera":
        cam_ar = str(cfg.get("camera_ar", "")).strip()
        if cam_ar:
            args.append(f"--camera-ar={cam_ar}")
        cam_sz = str(cfg.get("camera_size", "")).strip()
        if cam_sz:
            args.append(f"--camera-size={cam_sz}")

    return args
